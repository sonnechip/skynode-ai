# File: flight_core.py
import os
import json
from openai import OpenAI
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# =========================================
# CẤU HÌNH KẾT NỐI VLLM (Thay cho Ollama)
# =========================================
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
from core.ai_provider import get_ai_config

def _get_client():
    config = get_ai_config()
    if config:
        return config["client"], config["model"]
    return None, None

_client, MODEL_NAME = _get_client()
client = _client  # 可能是 None，但不會在 import 時 crash

# =========================================
# KNOWLEDGE BASE - Dữ liệu sân bay
# =========================================
AIRPORT_CODES = {
    "hanoi": "HAN", "ha noi": "HAN", "hn": "HAN", "han": "HAN",
    "ho chi minh": "SGN", "saigon": "SGN", "sgn": "SGN", "hcm": "SGN",
    "da nang": "DAD", "danang": "DAD", "dad": "DAD",
    "phu quoc": "PQC", "pqc": "PQC", "nha trang": "CXR", "cxr": "CXR",
    "hai phong": "HPH", "hph": "HPH", "bangkok": "BKK", "bkk": "BKK",
    "singapore": "SIN", "sin": "SIN", "tokyo": "NRT", "nrt": "NRT",
    "osaka": "KIX", "kix": "KIX", "seoul": "ICN", "incheon": "ICN",
    "icn": "ICN", "taipei": "TPE", "taiwan": "TPE", "tpe": "TPE",
    "hong kong": "HKG", "hkg": "HKG", "london": "LHR", "lhr": "LHR",
    "paris": "CDG", "cdg": "CDG", "new york": "JFK", "jfk": "JFK",
    "los angeles": "LAX", "lax": "LAX", "chicago": "ORD", "ord": "ORD"
}

AIRLINE_NAMES = {
    "VN": "Vietnam Airlines", "VJ": "VietJet Air", "QH": "Bamboo Airways",
    "CX": "Cathay Pacific", "SQ": "Singapore Airlines", "TG": "Thai Airways",
    "KE": "Korean Air", "JL": "Japan Airlines", "NH": "ANA", "EK": "Emirates",
    "QR": "Qatar Airways", "BA": "British Airways", "AF": "Air France",
}

# =========================================
# HELPER FUNCTIONS
# =========================================
def get_airport_code(text: str) -> str:
    if not text: return ""
    text_lower = text.lower().strip()
    if text_lower in AIRPORT_CODES: return AIRPORT_CODES[text_lower]
    if len(text) == 3 and text.isupper(): return text
    for key, code in AIRPORT_CODES.items():
        if text_lower in key or key in text_lower: return code
    return text.upper()[:3]

def get_airline_name(code: str) -> str:
    return AIRLINE_NAMES.get(code.upper(), code)

def format_duration(minutes) -> str:
    if not minutes: return "?"
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m:02d}m"

def format_price(price) -> str:
    if not price: return "Contact for price"
    if isinstance(price, (int, float)): return f"${price:,.0f}"
    return f"${price}"

# =========================================
# API & AI TOOLS
# =========================================
def search_flights_api(origin: str, destination: str, date: str, return_date: str = None, adults: int = 1, api_key: str = None) -> dict:
    final_key = api_key if api_key else SERPAPI_KEY
    if not final_key:
        return {"success": False, "message": "Missing API Key. Please provide one in the .env file.", "flights": []}

    try:
        params = {
            "engine": "google_flights", "departure_id": origin, "arrival_id": destination,
            "outbound_date": date, "adults": adults, "travel_class": 1,
            "currency": "USD", "hl": "en", "api_key": final_key,
        }
        if return_date and return_date != "ONE_WAY":
            params["return_date"] = return_date
            params["type"] = "1"
        else:
            params["type"] = "2"

        results = GoogleSearch(params).get_dict()
        if "error" in results: return {"success": False, "message": results["error"], "flights": []}

        all_flights = results.get("best_flights", []) + results.get("other_flights", [])
        if not all_flights: return {"success": False, "message": "No flights found.", "flights": []}

        flights = []
        for offer in all_flights[:6]:
            segments = offer.get("flights", [])
            if not segments: continue
            first_seg, last_seg = segments[0], segments[-1]
            airline_code = first_seg.get("airline", "?")

            flights.append({
                "airline": get_airline_name(airline_code),
                "flight_number": first_seg.get("flight_number", "?"),
                "departure_time": first_seg.get("departure_airport", {}).get("time", "?"),
                "departure_airport": first_seg.get("departure_airport", {}).get("id", origin),
                "arrival_time": last_seg.get("arrival_airport", {}).get("time", "?"),
                "arrival_airport": last_seg.get("arrival_airport", {}).get("id", destination),
                "duration": offer.get("total_duration", 0),
                "stops": len(segments) - 1,
                "price": offer.get("price", 0),
                "travel_class": first_seg.get("travel_class", "Economy"),
                "is_best": offer in results.get("best_flights", []),
            })
        return {"success": True, "flights": flights}
    except Exception as e:
        return {"success": False, "message": str(e), "flights": []}

def extract_intent(user_message: str) -> dict:
    if client is None:
        return {"action": "general_question"}
    """
    Đã sửa prompt: Ép AI trả về null nếu thiếu thông tin, tuyệt đối không dùng placeholder.
    """
    prompt = f"""You are a flight search assistant. Extract information from the message. 
CRITICAL: If a piece of information is MISSING in the user's message, you MUST return null for that field. 
DO NOT use placeholders like "city", "IATA", "unknown", or "somewhere".

Return ONLY valid JSON exactly matching this structure:
{{
  "origin": "City name or Airport code or null",
  "destination": "City name or Airport code or null",
  "date": "YYYY-MM-DD or null",
  "return_date": "YYYY-MM-DD or 'ONE_WAY' or null",
  "adults": 1,
  "action": "search_flight"
}}

User Message: "{user_message}"
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        
        # Nếu LLM parse thành công, trả về Dict
        if start != -1 and end != -1:
            parsed_data = json.loads(content[start:end])
            
            # Quét dọn các giá trị "null" dạng chuỗi thành None thực sự
            for k, v in parsed_data.items():
                if isinstance(v, str) and v.lower() in ["null", "none", "city", "iata", "unknown"]:
                    parsed_data[k] = None
                    
            return parsed_data
            
        return {"action": "general_question"}
    except Exception as e:
        print(f"Parse Error: {e}")
        return {"action": "general_question"}

# =========================================
# MAIN AGENT ORCHESTRATOR
# =========================================
def process_user_request(user_input: str, api_key: str, chat_history: list) -> dict:
    info = extract_intent(user_input)

    if info.get("action") == "search_flight":
        origin, dest, date = info.get("origin"), info.get("destination"), info.get("date")
        if not origin or not dest or not date:
            return {"type": "error", "content": "⚠️ Please provide origin, destination, and date."}

        origin_code, dest_code = get_airport_code(origin), get_airport_code(dest)
        result = search_flights_api(origin_code, dest_code, date, info.get("return_date"), info.get("adults", 1), api_key)

        if result["success"] and result["flights"]:
            min_p = format_price(min([f["price"] for f in result["flights"]]))
            return {
                "type": "flights", "origin": origin_code, "destination": dest_code,
                "content": f"✅ Found {len(result['flights'])} flights. From {min_p}.",
                "data": result["flights"]
            }
        return {"type": "error", "content": f"😔 No flights found. {result.get('message', '')}"}
    
    # Chat thông thường
    if client is None:
        return {"type": "error", "content": "AI service is not available."}
    try:
        history = [{"role": m["role"], "content": m.get("content", "")} for m in chat_history if m.get("content")]
        messages = [{"role": "system", "content": "Flight assistant. Respond in user language."}] + history + [{"role": "user", "content": user_input}]
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        return {"type": "chat", "content": response.choices[0].message.content}
    except Exception as e:
        return {"type": "error", "content": f"vLLM Error: {str(e)}"}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("✈️ Terminal Flight Agent (vLLM + Qwen2.5 + SerpApi)")
    print("Hệ thống đã sẵn sàng. Gõ 'exit' để thoát.")
    print("="*60)

    chat_history = []
    
    while True:
        user_input = input("\n🧑 Bạn: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 Cảm ơn bạn đã sử dụng dịch vụ. Hẹn gặp lại!")
            break
        if not user_input.strip(): continue
            
        print("🤖 Agent đang phân tích và tìm kiếm chuyến bay...")
        response = process_user_request(user_input, api_key=None, chat_history=chat_history)
        
        print("\n" + "—"*50)
        if response["type"] == "flights":
            print(f"🛫 CHUYẾN BAY TỪ {response['origin']} ĐI {response['destination']}")
            print(response["content"] + "\n")
            for f in response["data"]:
                best_mark = "⭐ (BEST)" if f.get("is_best") else ""
                print(f"  • {f['airline']} {f.get('flight_number', '')} {best_mark}")
                print(f"    🕒 {f.get('departure_time', '?')} ({f['departure_airport']}) ➡️ {f.get('arrival_time', '?')} ({f['arrival_airport']})")
                print(f"    ⏱️ Thời gian: {format_duration(f.get('duration', 0))} | Điểm dừng: {f.get('stops', 0)}")
                print(f"    💵 Giá: {format_price(f.get('price', 0))}/người | Hạng: {f.get('travel_class', 'Economy')}")
                print("    - - - - - - - - - - - - - - - -")
        elif response["type"] == "error":
            print(f"❌ {response['content']}")
        else:
            print(f"🤖 AI: {response['content']}")
        print("—"*50)
        
        chat_history.append({"role": "user", "content": user_input})
        if response["type"] in ["chat", "error"]:
            chat_history.append({"role": "assistant", "content": response["content"]})