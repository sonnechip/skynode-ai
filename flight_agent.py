import os
import json
import ollama
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()
# Đây là key hệ thống, bạn sẽ cấu hình trong Secrets của Streamlit Cloud
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# =========================================
# IATA AIRPORT CODES – English Focused
# =========================================

AIRPORT_CODES = {
    # Vietnam
    "hanoi": "HAN", "ha noi": "HAN", "hn": "HAN", "han": "HAN",
    "ho chi minh": "SGN", "saigon": "SGN", "sgn": "SGN", "hcm": "SGN",
    "da nang": "DAD", "danang": "DAD", "dad": "DAD",
    "phu quoc": "PQC", "pqc": "PQC",
    "nha trang": "CXR", "cxr": "CXR",
    "hai phong": "HPH", "hph": "HPH",
    
    # Asia & Global
    "bangkok": "BKK", "bkk": "BKK",
    "singapore": "SIN", "sin": "SIN",
    "tokyo": "NRT", "nrt": "NRT",
    "osaka": "KIX", "kix": "KIX",
    "seoul": "ICN", "incheon": "ICN", "icn": "ICN",
    "taipei": "TPE", "taiwan": "TPE", "tpe": "TPE",
    "hong kong": "HKG", "hkg": "HKG",
    "london": "LHR", "lhr": "LHR",
    "paris": "CDG", "cdg": "CDG",
    "new york": "JFK", "jfk": "JFK",
    "los angeles": "LAX", "lax": "LAX",
}

AIRLINE_NAMES = {
    "VN": "Vietnam Airlines", "VJ": "VietJet Air", "QH": "Bamboo Airways",
    "CX": "Cathay Pacific", "SQ": "Singapore Airlines", "TG": "Thai Airways",
    "KE": "Korean Air", "JL": "Japan Airlines", "NH": "ANA", "EK": "Emirates",
    "QR": "Qatar Airways", "BA": "British Airways", "AF": "Air France",
}

def get_airport_code(text: str) -> str:
    text_lower = text.lower().strip()
    if text_lower in AIRPORT_CODES:
        return AIRPORT_CODES[text_lower]
    if len(text) == 3 and text.isupper():
        return text
    for key, code in AIRPORT_CODES.items():
        if text_lower in key or key in text_lower:
            return code
    return text.upper()[:3]

def get_airline_name(code: str) -> str:
    return AIRLINE_NAMES.get(code.upper(), code)

# =========================================
# SERPAPI – CẬP NHẬT ĐỂ NHẬN API KEY TỪ UI
# =========================================

def search_flights(origin: str, destination: str, date: str,
                   return_date: str = None, adults: int = 1,
                   travel_class: int = 1, api_key: str = None) -> dict:
    """
    api_key: Nếu người dùng nhập ở Sidebar, giá trị này sẽ được ưu tiên.
    """
    try:
        # Cơ chế ưu tiên: Key từ giao diện > Key từ hệ thống (.env/Secrets)
        final_key = api_key if api_key else SERPAPI_KEY
        
        if not final_key:
            return {
                "success": False, 
                "message": "Missing API Key. Please provide one in the sidebar.", 
                "flights": []
            }

        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": date,
            "adults": adults,
            "travel_class": travel_class,
            "currency": "USD",
            "hl": "en",
            "api_key": final_key, # Sử dụng key đã xác định
        }
        
        if return_date:
            params["return_date"] = return_date
            params["type"] = "1"
        else:
            params["type"] = "2"

        search = GoogleSearch(params)
        results = search.get_dict()

        # Kiểm tra lỗi từ phía SerpApi (ví dụ: Invalid Key)
        if "error" in results:
            return {"success": False, "message": results["error"], "flights": []}

        best = results.get("best_flights", [])
        other = results.get("other_flights", [])
        all_flights = best + other

        if not all_flights:
            return {"success": False, "message": "No flights found for these criteria.", "flights": []}

        flights = []
        for offer in all_flights[:6]:
            segments = offer.get("flights", [])
            if not segments: continue

            first_seg = segments[0]
            last_seg = segments[-1]
            airline_code = first_seg.get("airline", "?")

            flights.append({
                "airline": get_airline_name(airline_code),
                "airline_code": airline_code,
                "flight_number": first_seg.get("flight_number", "?"),
                "departure_time": first_seg.get("departure_airport", {}).get("time", "?"),
                "departure_airport": first_seg.get("departure_airport", {}).get("id", origin),
                "arrival_time": last_seg.get("arrival_airport", {}).get("time", "?"),
                "arrival_airport": last_seg.get("arrival_airport", {}).get("id", destination),
                "duration": offer.get("total_duration", 0),
                "stops": len(segments) - 1,
                "price": offer.get("price", 0),
                "travel_class": first_seg.get("travel_class", "Economy"),
                "is_best": offer in best,
            })

        return {"success": True, "flights": flights, "count": len(flights)}

    except Exception as e:
        return {"success": False, "message": str(e), "flights": []}

# =========================================
# AI & FORMATTING (Giữ nguyên)
# =========================================

def extract_flight_info(user_message: str) -> dict:
    prompt = f"""You are a flight search assistant. Extract information from the message.
Return ONLY valid JSON:
{{
    "origin": "city/IATA",
    "destination": "city/IATA",
    "date": "YYYY-MM-DD or null",
    "return_date": "YYYY-MM-DD or null",
    "adults": 1,
    "travel_class": "economy/business/first",
    "action": "search_flight or general_question",
    "language": "en"
}}
Message: "{user_message}"
"""
    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )
        content = response["message"]["content"].strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except:
        return {"action": "general_question", "language": "en"}

def format_duration(minutes) -> str:
    if not minutes: return "?"
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m:02d}m"

def format_price(price) -> str:
    if not price:
        return "Contact for price"
    if isinstance(price, (int, float)):
        return f"${price:,.0f}"
    return f"${price}"

def run_flight_skill(user_query: str, api_key_from_ui: str = None):
    """
    Đây là hàm thực thi chính của 'Skill' đọc lịch trình bay.
    Nó kết hợp AI để hiểu câu hỏi và API để lấy dữ liệu.
    """
    extracted = extract_flight_info(user_query)
    
    if extracted.get("action") == "general_question":
        return "Where would you like to fly to, and on what date?"

    origin_code = get_airport_code(extracted.get("origin", "HAN"))
    dest_code = get_airport_code(extracted.get("destination", "SGN"))
    flight_date = extracted.get("date")

    if not flight_date:
        return "Please provide your travel date"

    search_results = search_flights(
        origin=origin_code,
        destination=dest_code,
        date=flight_date,
        api_key=api_key_from_ui
    )

    if not search_results["success"]:
        # Chuyển thông báo lỗi sang tiếng Anh
        error_msg = search_results.get('message', 'No schedules found.')
        return f"Error: {error_msg}"

    flights = search_results["flights"]
    # Tiêu đề chuyên nghiệp
    response = f"✈️ **Flight schedule from {origin_code} to {dest_code} on {flight_date}:**\n\n"
    
    for f in flights:
        response += (
            f"- **{f['airline']}** ({f['flight_number']})\n"
            f"  🕒 {f['departure_time']} ➔ {f['arrival_time']} "
            f"({format_duration(f['duration'])})\n"
            f"  💰 Price from: {format_price(f['price'])}\n"
            f"  --- \n"
        )
    return response
