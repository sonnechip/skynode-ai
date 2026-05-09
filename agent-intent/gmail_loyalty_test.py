import json

AIRLINES = ["EVA Air", "STARLUX", "AirAsia"]

def analyze_emails(mock_emails):
    travel_history = []
    airline_count = {}

    # 1. Detect airlines in emails
    for email in mock_emails:
        detected_airline = None

        for airline in AIRLINES:
            if airline.lower() in email.lower():
                detected_airline = airline
                break

        if detected_airline:
            airline_count[detected_airline] = (
                airline_count.get(detected_airline, 0) + 1
            )

            travel_history.append({
                "airline": detected_airline,
                "email_snippet": email
            })

    # 2. Find most frequent airline
    preferred_airline = (
        max(airline_count, key=airline_count.get)
        if airline_count else None
    )

    # 3. Final structured output
    return {
        "preferred_airline": preferred_airline,
        "estimated_loyalty": airline_count,
        "travel_history": travel_history
    }


# ---------------------------
# TEST (optional but useful)
# ---------------------------
if __name__ == "__main__":

    mock_emails = [
        "Your EVA Air flight from Taipei to Tokyo is confirmed.",
        "STARLUX booking confirmation to Singapore.",
        "AirAsia online check-in reminder.",
        "EVA Air mileage reward update."
    ]

    result = analyze_emails(mock_emails)

    print(json.dumps(result, indent=4))


def email_loyalty_tool():
    """Simple wrapper used by the agent to return analyzed mock email loyalty data.
    Kept lightweight so it can be imported without side-effects.
    """
    mock_emails = [
        "Your EVA Air flight from Taipei to Tokyo is confirmed.",
        "STARLUX booking confirmation to Singapore.",
        "AirAsia online check-in reminder.",
        "EVA Air mileage reward update."
    ]

    return analyze_emails(mock_emails)

def email_loyalty_tool():
    mock_emails = [
        "Your EVA Air flight from Taipei to Tokyo is confirmed.",
        "STARLUX booking confirmation to Singapore.",
        "AirAsia online check-in reminder.",
        "EVA Air mileage reward update."
    ]

    return analyze_emails(mock_emails)