# pipeline.py
import json
from agents.intent_agent import agent_with_memory
from agents.flight_agent import FlightSearchAgent
from agents.miles_agent import MilesArchitectAgent
from agents.concierge_agent import ConciergeAgent

def run_full_pipeline(user_input: str, user_profile: dict) -> dict:
    """
    Complete 4-stage Agent pipeline
    Returns a result dict for frontend display
    """
    # --- Stage 1: Intent Agent ---
    raw = agent_with_memory(user_input)
    try:
        start = raw.find('{')
        intent = json.loads(raw[start:raw.rfind('}')+1])
    except:
        return {"error": "Unable to parse user intent, please try again."}

    if intent.get("status") == "need_more_info":
        return {
            "stage": "need_more_info",
            "message": intent.get("ai_message", "Please provide more information.")
        }

    data = intent.get("data", {})
    origin = data.get("nearby_airports_from", "TPE")
    destination = data.get("nearby_airports_to", "") or data.get("to", "")
    date = data.get("time_travel", "")

    if not destination or not date:
        return {"stage": "need_more_info", "message": intent.get("ai_message")}

    # --- Stage 2: Flight Search Agent ---
    flight_agent = FlightSearchAgent()
    query = f"Flights from {origin} to {destination} on {date}"
    flight_result = flight_agent.search(query)

    if not flight_result.success:
        return {"error": f"No flights found: {flight_result.error_message}"}

    # --- Stage 3: Miles Architect Agent ---
    miles_agent = MilesArchitectAgent()
    miles_result = miles_agent.analyze_flights(
        flights=flight_result.to_miles_agent_input(),
        user_card=user_profile.get("card", ""),
        current_miles=user_profile.get("current_miles", 0),
        current_miles_airline=user_profile.get("ff_airline", "")
    )

    # --- Stage 4: Concierge Agent ---
    concierge = ConciergeAgent()
    final = concierge.synthesize(flight_result, miles_result, user_profile)

    return {
        "stage": "complete",
        "flights": [f.to_dict() for f in flight_result.flights],
        "miles_analysis": miles_result.to_dict(),
        "recommendation": {
            "headline": final.headline,
            "why": final.why_this_flight,
            "card_tip": final.credit_card_tip,
            "upgrade_tip": final.upgrade_tip,
            "full_report": final.full_report
        }
    }