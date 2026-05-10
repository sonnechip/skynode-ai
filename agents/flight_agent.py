"""
flight_agent.py
────────────────────────────────────────────────────────────
Flight Search Agent — SkyNode AI Backend
Wraps flight_core.py search logic into a clean Agent class.
Outputs structured FlightSearchResult that MilesAgent can consume.
"""

import os
import json
from dataclasses import dataclass, asdict, field
from openai import OpenAI
from core.ai_provider import get_ai_config

# Import existing flight core (your team's code — untouched)
from core.flight_core import (
    search_flights_api,
    extract_intent,
    get_airport_code,
    format_duration,
    format_price,
    AIRPORT_CODES,
    AIRLINE_NAMES,
)

# ============================================================
# OUTPUT SCHEMA  (MilesAgent reads this)
# ============================================================

@dataclass
class FlightRecord:
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price_usd: float
    fare_class: str          # "Economy" / "Business" / "First"
    duration_minutes: int
    stops: int
    is_best: bool = False
    route: str = ""          # auto-filled: "HAN-NRT"

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class FlightSearchResult:
    success: bool
    origin: str
    destination: str
    date: str
    flights: list[FlightRecord] = field(default_factory=list)
    error_message: str = ""
    agent_name: str = "FlightSearchAgent"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["flights"] = [asdict(f) for f in self.flights]
        return d

    def to_miles_agent_input(self) -> list[dict]:
        """
        Convert to the format MilesArchitectAgent.analyze() expects:
        [{"airline": str, "price_usd": float, "fare_class": str, "route": str}, ...]
        """
        return [
            {
                "airline": f.airline,
                "price_usd": f.price_usd,
                "fare_class": f.fare_class,
                "route": f.route or f"{f.origin}-{f.destination}",
            }
            for f in self.flights
        ]


# ============================================================
# FLIGHT SEARCH AGENT CLASS
# ============================================================

class FlightSearchAgent:
    """
    Wraps flight_core.py into a callable Agent.

    Usage:
        agent = FlightSearchAgent(serpapi_key="sk-...")
        result = agent.search("Find flights from Hanoi to Tokyo on 2026-06-01")
        # or structured:
        result = agent.search_structured("HAN", "NRT", "2026-06-01")
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

    def search(self, user_message: str) -> FlightSearchResult:
        """
        Natural language entry: parse intent then search.
        """
        info = extract_intent(user_message)

        if info.get("action") != "search_flight":
            return FlightSearchResult(
                success=False,
                origin="", destination="", date="",
                error_message="Could not extract flight intent from message.",
            )

        origin_raw = info.get("origin", "")
        dest_raw   = info.get("destination", "")
        date       = info.get("date", "")

        if not origin_raw or not dest_raw or not date:
            return FlightSearchResult(
                success=False,
                origin=origin_raw, destination=dest_raw, date=date,
                error_message="Missing origin, destination, or date.",
            )

        origin_code = get_airport_code(origin_raw)
        dest_code   = get_airport_code(dest_raw)
        return self._do_search(origin_code, dest_code, date,
                               info.get("return_date"), info.get("adults", 1))

    def search_structured(
        self,
        origin: str,
        destination: str,
        date: str,
        return_date: str = None,
        adults: int = 1,
    ) -> FlightSearchResult:
        """
        Structured entry: pass IATA codes directly.
        """
        return self._do_search(
            get_airport_code(origin),
            get_airport_code(destination),
            date, return_date, adults,
        )

    # ── Internal ───────────────────────────────────────────

    def _do_search(
        self,
        origin: str,
        destination: str,
        date: str,
        return_date: str = None,
        adults: int = 1,
    ) -> FlightSearchResult:
        raw = search_flights_api(
            origin, destination, date, return_date, adults,
            api_key=self.serpapi_key,
        )

        if not raw.get("success") or not raw.get("flights"):
            return FlightSearchResult(
                success=False,
                origin=origin, destination=destination, date=date,
                error_message=raw.get("message", "No flights found."),
            )

        records = []
        for f in raw["flights"]:
            price = float(f.get("price", 0))
            records.append(FlightRecord(
                airline=f.get("airline", "Unknown"),
                flight_number=f.get("flight_number", ""),
                origin=f.get("departure_airport", origin),
                destination=f.get("arrival_airport", destination),
                departure_time=f.get("departure_time", ""),
                arrival_time=f.get("arrival_time", ""),
                price_usd=price,
                fare_class=f.get("travel_class", "Economy"),
                duration_minutes=int(f.get("duration", 0) or 0),
                stops=int(f.get("stops", 0) or 0),
                is_best=bool(f.get("is_best", False)),
                route=f"{origin}-{destination}",
            ))

        return FlightSearchResult(
            success=True,
            origin=origin, destination=destination, date=date,
            flights=records,
        )