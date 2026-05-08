import ollama
import json
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

ip_location = "Hsinchu, Taiwan"

USER_PERMANENT_MEMORY = {
    "name": "Nguyen Mai Nhat Anh (Jay)",
    "occupation": "Computer Science Student at NYCU",
    "user_location_right_now": ip_location,
    "habitual_preferences": {
        "preferred_flight_time": "night",
        "meal_type": "vegetarian",
        "loyalty_program": "EVA Air"
    }
}

def get_calendar_data():
    try:
        # Giả sử API này trả về lịch bận của Nhật Anh
        response = requests.get("http://localhost:8005/get-calendar", timeout=5)
        return response.json()
    except:
        return {"calendar_events": []}

def agent_with_memory(user_speech_input):
    calendar_json = get_calendar_data()
    
    system_instruction = f"""
    You are a Personalized Travel Assistant. 
    Language for 'ai_message': Always use the same language as the User.
    
    USER PERMANENT MEMORY: {json.dumps(USER_PERMANENT_MEMORY, ensure_ascii=False)}

    STRICT RULES FOR DATA:
    1. 'time_travel': This is the specific date or time range the user wants to travel. 
       - If the user DOES NOT provide a specific date/month/time, it is NULL.
       - Do NOT use memory for 'time_travel' if not explicitly saved there.
       - If NULL, you MUST add "time_travel" to the 'missing_fields' array.
    2. 'occupation': Choose one from [children, student, adult, elderly, disabilities]. 
       - Use Memory if missing.
    3. 'from' & 'nearby_airports_from': 
       - Use current user location from Memory unless the user says "I am currently in [Other City]".
       - Identify the nearest international Airport Code (IATA).
    4. 'ai_message': 
       - If 'missing_fields' is not empty, ask the user politely for that specific info.
       - If everything is ready, just say "success".

    OUTPUT STRUCTURE (JSON ONLY):
    {{
      "status": "ready" or "need_more_info",
      "data": {{
        "occupation": "student",
        "from": "...",
        "nearby_airports_from": "...",
        "to": "...",
        "nearby_airports_to": "...",
        "busy_slots": [],
        "time_travel": null,
        "preferences": {{
          "flight_time": "...",
          "meal": "..."
        }}
      }},
      "missing_fields": [],
      "ai_message": "..."
    }}
    """

    user_payload = f"Calendar JSON: {json.dumps(calendar_json)}\nCurrent User Input: {user_speech_input}"

    response = ollama.chat(model='gemma4', messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': user_payload}
    ])

    return response['message']['content']

if __name__ == "__main__":
    print("--- SkyNode Agent 1 is thinking with memory (UTF-8 Ready) ---")
    
    user_talk = "I want to book a flight to Vietnam" 
    
    raw_ai_output = agent_with_memory(user_talk)
    
    try:
        start_idx = raw_ai_output.find('{')
        end_idx = raw_ai_output.rfind('}') + 1
        clean_json = json.loads(raw_ai_output[start_idx:end_idx])
        
        # if not clean_json['data'].get('time_travel') and 'time_travel' not in clean_json['missing_fields']:
        #      clean_json['status'] = "need_more_info"
        #      clean_json['missing_fields'].append("time_travel")
        #      clean_json['ai_message'] = "Bạn dự định khi nào sẽ khởi hành để mình kiểm tra lịch trống nhé?"

        with open('transfer_to_agent_2.json', 'w', encoding='utf-8') as f:
            json.dump(clean_json, f, indent=4, ensure_ascii=False)
            
        print("✅ SUCCESS: Package saved for Agent 2.")
        print(json.dumps(clean_json, indent=4, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Raw AI Output:", raw_ai_output)
