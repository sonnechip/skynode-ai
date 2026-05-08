import ollama
import json
import requests
from datetime import datetime

# 1. Fetch real-time calendar data from your local API
def get_calendar_data():
    try:
        response = requests.get("http://localhost:8005/get-calendar")
        return response.json()
    except Exception as e:
        return {"error": f"Connection failed: {e}"}

# 2. Agent 1 logic to summarize user context and calendar
def agent_understand_user(user_input):
    raw_calendar = get_calendar_data()
    
    # System Prompt optimized for English output and timestamp analysis
    system_instruction = """
    You are Agent 1 (User Context Manager) for SkyNode AI.
    Your mission:
    1. Parse 'calendar_events' to find specific BUSY time slots (start and end timestamps).
    2. Identify FREE travel windows based on those busy slots.
    3. Extract user preferences (Occupation, Flight Time, Meals).
    4. Current Reference Date: 2026-05-08.
    
    STRICT RULES:
    - Language: ENGLISH.
    - Format: PURE JSON ONLY.
    - Do not assume "all day" if hours are provided.
    
    JSON STRUCTURE:
    {
      "occupation": "string",
      "busy_slots": [{"event": "name", "start": "YYYY-MM-DD HH:MM", "end": "YYYY-MM-DD HH:MM"}],
      "free_travel_windows": [{"from": "YYYY-MM-DD HH:MM", "to": "YYYY-MM-DD HH:MM"}],
      "preferences": {
        "preferred_flight_time": "morning/night",
        "meal_type": "string"
      },
      "summary": "English summary for Agent 2"
    }
    """

    user_payload = f"""
    Calendar Data: {json.dumps(raw_calendar)}
    User Request: "{user_input}"
    """

    # Call Gemma via Ollama
    response = ollama.chat(model='gemma4', messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': user_payload}
    ])

    return response['message']['content']

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Test case for the Hackathon
    raw_user_speech = "I am a student at NYCU. I want to fly home tomorrow. I prefer night flights and need vegetarian meals."
    
    print("--- SkyNode Agent 1 is analyzing schedule... ---")
    raw_ai_output = agent_understand_user(raw_user_speech)
    
    try:
        # Extract JSON from potential AI chatter
        start_idx = raw_ai_output.find('{')
        end_idx = raw_ai_output.rfind('}') + 1
        clean_json = json.loads(raw_ai_output[start_idx:end_idx])
        
        # Save for Agent 2 (Hai)
        with open('transfer_to_agent_2.json', 'w', encoding='utf-8') as f:
            json.dump(clean_json, f, indent=4, ensure_ascii=False)
            
        print("✅ SUCCESS: Data packaged for Agent 2 in 'transfer_to_agent_2.json'")
        print(json.dumps(clean_json, indent=4))
        
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        print("Raw AI Output:", raw_ai_output)