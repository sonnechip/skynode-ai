"""
miles_agent.py
────────────────────────────────────────────────────────────
Miles Architect Agent — SkyNode AI Backend
Wraps miles_core.py into a clean Agent class.
Accepts FlightSearchResult from FlightSearchAgent, outputs MilesAnalysisResult.
"""

import os
import json
from dataclasses import dataclass, asdict, field
from typing import Optional
from openai import OpenAI
from core.ai_provider import get_ai_config

# Import existing miles core (your code — untouched)
from core.miles_core import (
    compare_flights_for_miles,
    get_upgrade_path,
    check_airline_alliance,
    calculate_miles_earned,
    calculate_credit_card_bonus,
    CREDIT_CARD_DB,
)

# ============================================================
# OUTPUT SCHEMA  (Concierge + frontend reads this)
# ============================================================

@dataclass
class RankedFlight:
    airline: str
    alliance: str
    price_usd: float
    fare_class: str
    route: str
    earned_miles: int
    card_bonus_points: int
    total_rewards_value_usd: float
    effective_cost: float
    recommendation_badge: str    # "BEST MILES" | "BEST VALUE" | "STANDARD"

@dataclass
class MilesAnalysisResult:
    ranked_flights: list[RankedFlight]
    best_flight: Optional[RankedFlight]
    recommendation_summary: str      # 1 sentence — Concierge reads this
    full_analysis_markdown: str      # Full markdown table — terminal / frontend
    upgrade_info: Optional[dict]
    card_strategy: Optional[dict]
    agent_name: str = "MilesArchitectAgent"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ranked_flights"] = [asdict(f) for f in self.ranked_flights]
        if self.best_flight:
            d["best_flight"] = asdict(self.best_flight)
        return d

    def to_concierge_context(self) -> str:
        """Short text for ConciergeAgent to embed in its prompt."""
        if not self.best_flight:
            return self.recommendation_summary
        f = self.best_flight
        return (
            f"[MilesArchitectAgent] Best option: {f.airline} ({f.alliance}) "
            f"${f.price_usd:.0f} {f.fare_class}-class. "
            f"Earns {f.earned_miles} miles + {f.card_bonus_points} card pts. "
            f"Effective cost: ${f.effective_cost:.2f}. "
            f"Badge: {f.recommendation_badge}. "
            f"Summary: {self.recommendation_summary}"
        )


# ============================================================
# LLM TOOL DEFINITIONS
# ============================================================

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "compare_flights",
            "description": "Rank a list of flights by miles/rewards ROI for a given credit card.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flights_json": {
                        "type": "string",
                        "description": "JSON string of flight list: [{airline, price_usd, fare_class, route}]"
                    },
                    "user_card": {"type": "string"}
                },
                "required": ["flights_json", "user_card"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upgrade_path",
            "description": "Calculate how many miles needed to upgrade to Business class.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_miles": {"type": "integer"},
                    "airline": {"type": "string"},
                },
                "required": ["current_miles", "airline"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_alliance",
            "description": "Lookup which alliance an airline belongs to.",
            "parameters": {
                "type": "object",
                "properties": {"airline_name": {"type": "string"}},
                "required": ["airline_name"],
            },
        },
    },
]

def _run_tool(name: str, args: dict) -> str:
    try:
        if name == "compare_flights":
            flights = json.loads(args["flights_json"])
            result = compare_flights_for_miles(flights, args["user_card"])
            return json.dumps(result, ensure_ascii=False, indent=2)
        if name == "get_upgrade_path":
            result = get_upgrade_path(int(args["current_miles"]), args["airline"])
            return json.dumps(result, ensure_ascii=False)
        if name == "check_alliance":
            result = check_airline_alliance(args["airline_name"])
            return json.dumps(result, ensure_ascii=False)
        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


_SYSTEM_PROMPT = """You are MilesArchitectAgent — a specialist in airline miles and credit card rewards optimization.

TOOLS: Always call tools for calculations. Never guess numbers.

OUTPUT FORMAT — you MUST follow this exactly:
RECOMMENDATION_SUMMARY: <one sentence with the best flight choice and why>
FULL_ANALYSIS:
<markdown table comparing all flights: Airline | Price | Alliance | Miles Earned | Card Points | Rewards Value | Effective Cost | Badge>
<brief paragraph explaining the winner>
<if upgrade_info provided: add "Upgrade Path" section>
"""


# ============================================================
# MILES ARCHITECT AGENT CLASS
# ============================================================

class MilesArchitectAgent:
    """
    Analyzes a list of flights and picks the best one based on miles/rewards ROI.

    Usage:
        from miles_agent import MilesArchitectAgent

        agent = MilesArchitectAgent()

        # From FlightSearchAgent output:
        result = agent.analyze_flights(
            flights=flight_result.to_miles_agent_input(),
            user_card="Chase Sapphire Reserve",
            current_miles=18000,
            current_miles_airline="Vietnam Airlines",
        )
        print(result.full_analysis_markdown)
        print(result.to_concierge_context())   # pass to ConciergeAgent
    """

    def __init__(self, serpapi_key: str = None):
        config = get_ai_config()
        if config:
            self.client = config["client"]
            self.model_name = config["model"]
        else:
            self.client = None 
            
        self.serpapi_key = serpapi_key or os.environ.get("SERPAPI_KEY", "")

    # ── Public API ─────────────────────────────────────────

    def analyze_flights(
        self,
        flights: list[dict],
        user_card: str,
        current_miles: int = None,
        current_miles_airline: str = None,
    ) -> MilesAnalysisResult:
        """
        Main entry point.
        flights: [{"airline": str, "price_usd": float, "fare_class": str, "route": str}]
        """
        # Step 1: Python math first (no LLM) — accurate rankings
        ranked_raw = compare_flights_for_miles(flights, user_card).get("ranked_flights", [])

        # Assign badges
        for i, r in enumerate(ranked_raw):
            if i == 0:
                r["recommendation_badge"] = "BEST MILES"
            elif ranked_raw and r["effective_cost"] == min(x["effective_cost"] for x in ranked_raw):
                r["recommendation_badge"] = "BEST VALUE"
            else:
                r["recommendation_badge"] = "STANDARD"

        # Step 2: Upgrade path (pure Python)
        upgrade_info = None
        if current_miles is not None and current_miles_airline:
            upgrade_info = get_upgrade_path(current_miles, current_miles_airline)

        # Step 3: Card strategy
        card_strategy = None
        if flights and user_card:
            card_strategy = calculate_credit_card_bonus(
                flights[0]["price_usd"], user_card, flights[0]["airline"]
            )

        # Step 4: LLM writes the narrative
        narrative = self._llm_narrate(ranked_raw, user_card, upgrade_info)

        return self._build_result(narrative, ranked_raw, upgrade_info, card_strategy)

    def quick_rank(self, flights: list[dict], user_card: str) -> list[dict]:
        """No LLM — instant ranked list. Use when you just need the order fast."""
        return compare_flights_for_miles(flights, user_card).get("ranked_flights", [])

    def check_upgrade(self, current_miles: int, airline: str) -> dict:
        """No LLM — instant upgrade status."""
        return get_upgrade_path(current_miles, airline)

    # ── Internal ───────────────────────────────────────────

    def _llm_narrate(self, ranked: list, user_card: str, upgrade_info: dict) -> str:
        flights_json = json.dumps(ranked, ensure_ascii=False, indent=2)
        upgrade_text = json.dumps(upgrade_info) if upgrade_info else "Not provided"

        user_msg = (
            f"Flights ranked by Python tools (user card: {user_card}):\n{flights_json}\n\n"
            f"Upgrade info: {upgrade_text}\n\n"
            "Now write the RECOMMENDATION_SUMMARY and FULL_ANALYSIS."
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

        for _ in range(5):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=_TOOLS,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=2000,
                )
            except Exception:
                try:
                    resp = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.2,
                        max_tokens=2000,
                    )
                except Exception as e:
                    return f"RECOMMENDATION_SUMMARY: LLM error: {e}\nFULL_ANALYSIS: N/A"

            choice = resp.choices[0]
            if choice.finish_reason == "stop" or not choice.message.tool_calls:
                return choice.message.content or ""

            messages.append({
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [tc.model_dump() for tc in choice.message.tool_calls],
            })
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": _run_tool(tc.function.name, args),
                })

        return "RECOMMENDATION_SUMMARY: Max iterations reached.\nFULL_ANALYSIS: N/A"

    def _build_result(
        self,
        narrative: str,
        ranked_raw: list,
        upgrade_info: dict,
        card_strategy: dict,
    ) -> MilesAnalysisResult:
        summary = ""
        full_md = narrative
        if "RECOMMENDATION_SUMMARY:" in narrative:
            after = narrative.split("RECOMMENDATION_SUMMARY:", 1)[1].strip()
            lines = after.split("\n")
            summary = lines[0].strip()
            rest = "\n".join(lines[1:]).strip()
            full_md = rest.split("FULL_ANALYSIS:", 1)[1].strip() if "FULL_ANALYSIS:" in rest else rest
        else:
            summary = narrative[:150].split("\n")[0]

        ranked_objs = []
        for r in ranked_raw:
            flight_data = r.get("flight", r)
            ranked_objs.append(RankedFlight(
                airline=r.get("airline") or flight_data.get("airline", "Unknown"),
                alliance=r.get("alliance", "Unknown"),
                price_usd=float(r.get("price_usd") or flight_data.get("price_usd", 0)),
                fare_class=r.get("fare_class") or flight_data.get("fare_class", "Economy"),
                route=r.get("route") or flight_data.get("route", ""),
                earned_miles=r.get("earned_miles", 0),
                card_bonus_points=r.get("card_bonus_points", 0),
                total_rewards_value_usd=r.get("total_rewards_value_usd", 0.0),
                effective_cost=r.get("effective_cost", 0.0),
                recommendation_badge=r.get("recommendation_badge", "STANDARD"),
            ))

        return MilesAnalysisResult(
            ranked_flights=ranked_objs,
            best_flight=ranked_objs[0] if ranked_objs else None,
            recommendation_summary=summary,
            full_analysis_markdown=full_md,
            upgrade_info=upgrade_info,
            card_strategy=card_strategy,
        )