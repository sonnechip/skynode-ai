# Tệp: miles_core.py

# ============================================================
# KNOWLEDGE BASE - Miles/Flight data
# ============================================================
AIRLINE_ALLIANCE_DB = {
    "Vietnam Airlines": "SkyTeam", "VN": "SkyTeam",
    "Air France": "SkyTeam", "KLM": "SkyTeam", "Delta": "SkyTeam",
    "Korean Air": "SkyTeam", "China Southern": "SkyTeam",
    "Singapore Airlines": "Star Alliance", "SQ": "Star Alliance",
    "Thai Airways": "Star Alliance", "United": "Star Alliance",
    "Lufthansa": "Star Alliance", "ANA": "Star Alliance",
    "EVA Air": "Star Alliance", "Asiana": "Star Alliance",
    "Qatar Airways": "Oneworld", "Cathay Pacific": "Oneworld",
    "British Airways": "Oneworld", "Japan Airlines": "Oneworld",
    "Malaysia Airlines": "Oneworld", "American Airlines": "Oneworld",
    "Bamboo Airways": "Independent", "VietJet": "Independent",
}

FARE_CLASS_MULTIPLIER = {
    "Y": 1.0, "B": 1.0, "M": 0.75, "H": 0.75, "Q": 0.5,
    "V": 0.5, "W": 0.5, "L": 0.25, "K": 0.25, "U": 0.0,
    "Economy": 0.5, "Business": 1.5, "First": 2.0,
    "Premium Economy": 1.0,
}

CREDIT_CARD_DB = {
    "Chase Sapphire Reserve": {
        "Star Alliance": 3.0, "SkyTeam": 3.0, "Oneworld": 3.0,
        "Independent": 1.0, "transfer_partners": ["United MileagePlus", "Singapore KrisFlyer"]
    },
    "Chase Sapphire Preferred": {
        "Star Alliance": 2.0, "SkyTeam": 2.0, "Oneworld": 2.0,
        "Independent": 1.0, "transfer_partners": ["United MileagePlus", "Singapore KrisFlyer"]
    },
    "Amex Platinum": {
        "Star Alliance": 5.0, "SkyTeam": 5.0, "Oneworld": 5.0,
        "Independent": 1.0, "transfer_partners": ["Singapore KrisFlyer", "ANA Mileage Club", "Air France/KLM Flying Blue"]
    },
    "Vietnam Airlines BIDV Visa": {
        "SkyTeam": 3.0, "Star Alliance": 1.5, "Oneworld": 1.5,
        "Independent": 1.0, "transfer_partners": ["Vietnam Airlines Lotusmiles"]
    },
    "Techcombank Visa Infinite": {
        "SkyTeam": 2.5, "Star Alliance": 2.0, "Oneworld": 2.0,
        "Independent": 1.5, "transfer_partners": ["Vietnam Airlines Lotusmiles"]
    },
}

UPGRADE_THRESHOLDS = {
    "Vietnam Airlines": {"Silver→Gold": 25000, "Economy→Business": 30000, "description": "Lotusmiles program"},
    "Singapore Airlines": {"Silver→Gold": 50000, "Economy→Business": 35000, "description": "KrisFlyer program"},
}

# ============================================================
# CORE FUNCTIONS - Pure Python, No AI
# ============================================================
def check_airline_alliance(airline_name: str) -> dict:
    for key, alliance in AIRLINE_ALLIANCE_DB.items():
        if key.lower() in airline_name.lower() or airline_name.lower() in key.lower():
            return {"airline": airline_name, "alliance": alliance, "found": True}
    return {"airline": airline_name, "alliance": "Unknown", "found": False}

def calculate_miles_earned(price_usd: float, fare_class: str, airline: str) -> dict:
    alliance_info = check_airline_alliance(airline)
    base_miles = price_usd * 5
    multiplier = FARE_CLASS_MULTIPLIER.get(fare_class, 0.5)
    earned_miles = base_miles * multiplier
    return {
        "airline": airline, "alliance": alliance_info["alliance"],
        "earned_miles": round(earned_miles), "multiplier": multiplier
    }

def calculate_credit_card_bonus(price_usd: float, card_name: str, airline: str) -> dict:
    alliance_info = check_airline_alliance(airline)
    alliance = alliance_info["alliance"]
    card_info = None
    for key, info in CREDIT_CARD_DB.items():
        if key.lower() in card_name.lower() or card_name.lower() in key.lower():
            card_info = info
            card_name = key
            break
    if not card_info:
        return {"error": f"Credit card information not found: {card_name}"}
    multiplier = card_info.get(alliance, card_info.get("Independent", 1.0))
    return {
        "card": card_name, "airline": airline,
        "bonus_points": round(price_usd * multiplier), "multiplier": multiplier
    }

def compare_flights_for_miles(flights: list, user_card: str) -> dict:
    results = []
    for flight in flights:
        airline = flight.get("airline", "Unknown")
        price = float(flight.get("price_usd", 0))
        fare_class = flight.get("fare_class", "Economy")
        
        miles_info = calculate_miles_earned(price, fare_class, airline)
        card_info = calculate_credit_card_bonus(price, user_card, airline)
        
        # 1 mile ≈ $0.015 | 1 point ≈ $0.01
        card_bonus = card_info.get("bonus_points", 0)
        total_value_score = (miles_info["earned_miles"] * 0.015 + card_bonus * 0.01)
        
        results.append({
            "flight": flight, "alliance": miles_info["alliance"],
            "earned_miles": miles_info["earned_miles"],
            "card_bonus_points": card_bonus,
            "total_rewards_value_usd": round(total_value_score, 2),
            "effective_cost": round(price - total_value_score, 2)
        })
    results.sort(key=lambda x: x["total_rewards_value_usd"], reverse=True)
    return {"ranked_flights": results, "recommendation": results[0] if results else None}

def get_upgrade_path(current_miles: int, airline: str) -> dict:
    for key, info in UPGRADE_THRESHOLDS.items():
        if key.lower() in airline.lower():
            needed = info.get("Economy→Business", 30000)
            gap = max(0, needed - current_miles)
            return {
                "airline": key, "current_miles": current_miles, "needed_for_upgrade": needed,
                "miles_gap": gap, "can_upgrade_now": gap == 0
            }
    return {"error": f"No upgrade data found for {airline}"}