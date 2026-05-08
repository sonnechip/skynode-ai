import pandas as pd
import numpy as np

def get_user_profile():
    """
    Fetch user-specific preferences and sensitive data.
    In the final version, this will pull from the encrypted Local Vault.
    """
    return {
        "name": "Claire",
        "membership": ["Star Alliance (Gold)", "SkyTeam"],
        "cards": ["Amex Gold", "Chase Sapphire"],
        "budget": 2000
    }

def get_price_trend_data():
    """
    Retrieve historical and forecasted price data for visualization.
    """
    # Dummy data representing price fluctuations
    return pd.DataFrame(np.random.randn(20, 1), columns=['Price Trend'])

def get_recommended_flights(query=""):
    """
    Fetch flight results processed by the AI Agent.
    In the final version, this will call the Agent 2 computation engine.
    """
    return [
        {
            "id": "SQ879",
            "airline": "Singapore Airlines",
            "time": "10:00 - 14:00",
            "route": "TPE-SIN",
            "price": 450,
            "badge": "⭐ AI Choice",
            "class": "Business (Z)",
            "aircraft": "A350-900",
            "miles": "2,500 miles",
            "card_strategy": "Use Amex Platinum for 5x points!"
        },
        {
            "id": "BR225",
            "airline": "EVA Air",
            "time": "07:40 - 12:05",
            "route": "TPE-SIN",
            "price": 380,
            "badge": "💰 Best Value",
            "class": "Economy (V)",
            "aircraft": "B787-10",
            "miles": "850 miles",
            "card_strategy": "Use EVA Co-brand Card for 2x miles"
        }
    ]

def get_calendar_events():
    """
    Retrieve upcoming events from the synced local calendar.
    Used for the suggestion chips in the UI.
    """
    return [
        {"name": "SAFMC Competition", "date": "2024-05-10", "loc": "SG"},
        {"name": "Summer Holiday", "date": "2024-07-01", "loc": "JP"}
    ]