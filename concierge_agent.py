"""
concierge_agent.py
────────────────────────────────────────────────────────────
Travel Concierge Agent — SkyNode AI Backend
Receives outputs from FlightSearchAgent + MilesArchitectAgent,
synthesizes them into a final human-readable recommendation.
"""

import os
import json
from dataclasses import dataclass, asdict
from openai import OpenAI

# ============================================================
# OUTPUT SCHEMA
# ============================================================

@dataclass
class FinalRecommendation:
    headline: str             # "Book Singapore Airlines SQ637 — saves $47 in rewards"
    chosen_flight: dict       # The best FlightRecord dict
    miles_analysis: dict      # The best RankedFlight dict
    why_this_flight: str      # 2-3 sentence explanation
    credit_card_tip: str      # "Use Amex Platinum for 5x points on this purchase"
    upgrade_tip: str          # "You need 12,000 more miles for Business on VN"
    full_report: str          # Full markdown report for display
    agent_name: str = "ConciergeAgent"

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# CONCIERGE AGENT CLASS
# ============================================================

_SYSTEM_PROMPT = """You are ConciergeAgent — the final step in SkyNode AI's multi-agent pipeline.

You receive structured data from two specialist agents:
1. FlightSearchAgent — raw flight options with prices, times, stops
2. MilesArchitectAgent — miles/rewards analysis, effective costs, upgrade path

YOUR JOB: Synthesize everything into ONE clear, friendly final recommendation.

OUTPUT FORMAT (follow exactly):
HEADLINE: <one punchy sentence: best flight + key benefit>

WHY_THIS_FLIGHT:
<2-3 sentences: why this flight wins on the combination of price + rewards + convenience>

CREDIT_CARD_TIP:
<1 sentence: which card to use and why>

UPGRADE_TIP:
<1 sentence: upgrade progress / how many more miles needed>

FULL_REPORT:
<markdown table of all options>
<then the detailed recommendation with numbers>

Rules:
- Always show the effective cost (price minus rewards value)
- Tone: confident, helpful, like a knowledgeable travel advisor
- Keep it concise — no padding
"""


class ConciergeAgent:
    """
    Final synthesis agent. Combines flight data + miles analysis into a recommendation.

    Usage:
        from concierge_agent import ConciergeAgent

        agent = ConciergeAgent()
        result = agent.synthesize(
            flight_result=flight_result,       # FlightSearchResult
            miles_result=miles_result,         # MilesAnalysisResult
            user_context={"card": "...", "current_miles": 18000}
        )
        print(result.full_report)
    """

    def __init__(self):
        self.model_name = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
        self.client = OpenAI(
            base_url=os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1"),
            api_key="not-required",
        )

    def synthesize(
        self,
        flight_result,        # FlightSearchResult
        miles_result,         # MilesAnalysisResult
        user_context: dict,   # {"card": str, "current_miles": int, "ff_airline": str}
    ) -> FinalRecommendation:

        # Build context string for LLM
        context = self._build_context(flight_result, miles_result, user_context)
        raw = self._call_llm(context)
        return self._parse_output(raw, flight_result, miles_result)

    # ── Internal ───────────────────────────────────────────

    def _build_context(self, flight_result, miles_result, user_ctx: dict) -> str:
        # Flight data summary
        flights_text = ""
        for f in flight_result.flights[:6]:
            flights_text += (
                f"  • {f.airline} {f.flight_number} | "
                f"{f.departure_time}→{f.arrival_time} | "
                f"${f.price_usd:.0f} | {f.fare_class} | "
                f"{f.stops} stop(s) | {f.duration_minutes}min\n"
            )

        # Miles analysis summary
        miles_text = miles_result.to_concierge_context()

        # Upgrade info
        upgrade_text = ""
        if miles_result.upgrade_info and "miles_gap" in miles_result.upgrade_info:
            ui = miles_result.upgrade_info
            if ui["miles_gap"] == 0:
                upgrade_text = f"✅ {ui['airline']}: eligible for Business upgrade NOW!"
            else:
                upgrade_text = (
                    f"{ui['airline']}: {ui['current_miles']:,} miles, "
                    f"need {ui['needed_for_upgrade']:,}, gap = {ui['miles_gap']:,}"
                )

        return f"""
USER CONTEXT:
- Credit card: {user_ctx.get('card', 'Not specified')}
- Current miles: {user_ctx.get('current_miles', 'Not specified')}
- FF airline: {user_ctx.get('ff_airline', 'Not specified')}
- Route: {flight_result.origin} → {flight_result.destination} on {flight_result.date}

FLIGHT OPTIONS (from FlightSearchAgent):
{flights_text}

MILES ANALYSIS (from MilesArchitectAgent):
{miles_text}

RANKED FLIGHTS WITH REWARDS:
{json.dumps([r.__dict__ if hasattr(r,'__dict__') else r 
             for r in miles_result.ranked_flights[:4]], indent=2, ensure_ascii=False, default=str)}

UPGRADE STATUS:
{upgrade_text or 'Not calculated'}

Now write the final recommendation following the output format.
"""

    def _call_llm(self, context: str) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                temperature=0.4,
                max_tokens=1500,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"HEADLINE: LLM error\nFULL_REPORT: {e}"

    def _parse_output(self, raw: str, flight_result, miles_result) -> FinalRecommendation:
        def extract(tag: str) -> str:
            if f"{tag}:" not in raw:
                return ""
            after = raw.split(f"{tag}:", 1)[1]
            # Extract until next tag or end
            tags = ["HEADLINE", "WHY_THIS_FLIGHT", "CREDIT_CARD_TIP", "UPGRADE_TIP", "FULL_REPORT"]
            end = len(after)
            for t in tags:
                if t != tag and f"\n{t}:" in after:
                    idx = after.index(f"\n{t}:")
                    end = min(end, idx)
            return after[:end].strip()

        best_flight_dict = {}
        if flight_result.flights:
            best_flight_dict = flight_result.flights[0].to_dict() if hasattr(flight_result.flights[0], 'to_dict') else {}

        best_miles_dict = {}
        if miles_result.best_flight:
            best_miles_dict = asdict(miles_result.best_flight)

        return FinalRecommendation(
            headline=extract("HEADLINE"),
            chosen_flight=best_flight_dict,
            miles_analysis=best_miles_dict,
            why_this_flight=extract("WHY_THIS_FLIGHT"),
            credit_card_tip=extract("CREDIT_CARD_TIP"),
            upgrade_tip=extract("UPGRADE_TIP"),
            full_report=extract("FULL_REPORT") or raw,
        )