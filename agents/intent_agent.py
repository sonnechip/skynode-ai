import json
import requests
import sys
import os
from openai import OpenAI
from core.ai_provider import get_ai_config  # 1. 引入妳剛寫好的聰明工具

sys.stdout.reconfigure(encoding='utf-8')

# 2. 這裡原本是寫死的 client，現在改成自動偵測
config = get_ai_config()
if config:
    client = config["client"]
    AI_MODEL = config["model"]
else:
    # 萬一都沒偵測到，給一個保險的預設值防止程式直接死掉
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    AI_MODEL = "gemma4"

ip_location = "Taipei, Taiwan"

USER_PERMANENT_MEMORY = {
    "name": "Claire",
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

    # 3. 這裡的 model 參數，原本是抓環境變數或預設 gemma，現在統一改用我們偵測到的 AI_MODEL
    response = client.chat.completions.create(
        model=AI_MODEL, 
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': user_payload}
        ]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print("--- SkyNode Agent 1 is thinking with memory (UTF-8 Ready) ---")
    
    user_talk = "I want to book a flight to Vietnam" 
    
    raw_ai_output = agent_with_memory(user_talk)
    
    try:
        start_idx = raw_ai_output.find('{')
        end_idx = raw_ai_output.rfind('}') + 1
        clean_json = json.loads(raw_ai_output[start_idx:end_idx])
        
        # 檢查若沒有提供旅遊時間，則將狀態設為需要更多資訊，並要求使用者提供出發時間
        # if not clean_json['data'].get('time_travel') and 'time_travel' not in clean_json['missing_fields']:
        #      clean_json['status'] = "need_more_info"
        #      clean_json['missing_fields'].append("time_travel")
        #      clean_json['ai_message'] = "請問您預計什麼時候出發？這樣我才能幫您檢查空檔喔！"

        with open('transfer_to_agent_2.json', 'w', encoding='utf-8') as f:
            json.dump(clean_json, f, indent=4, ensure_ascii=False)
            
        print("✅ SUCCESS: Package saved for Agent 2.")
        print(json.dumps(clean_json, indent=4, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Raw AI Output:", raw_ai_output)