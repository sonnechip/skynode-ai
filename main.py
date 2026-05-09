"""
main.py - SkyNode AI (Smart Memory Version)
"""

import os
from dotenv import load_dotenv

load_dotenv()

from flight_agent import FlightSearchAgent
from miles_agent import MilesArchitectAgent
from concierge_agent import ConciergeAgent

# ============================================================
# TERMINAL COLORS
# ============================================================
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    DIM    = "\033[2m"
    LINE   = "─" * 60

def ok(text):    print(f"{C.GREEN}✅ {text}{C.RESET}")
def warn(text):  print(f"{C.YELLOW}⚠️  {text}{C.RESET}")
def err(text):   print(f"{C.RED}❌ {text}{C.RESET}")
def step(n, text): print(f"\n{C.CYAN}[Step {n}/3] {text}{C.RESET}")

# ============================================================
# POPULAR DESTINATIONS + CLARIFICATION HELPERS
# ============================================================
POPULAR_CITIES = {
    "1": ("New York", "JFK"), "2": ("Los Angeles", "LAX"),
    "3": ("San Francisco", "SFO"), "4": ("Chicago", "ORD"),
    "5": ("Seattle", "SEA"), "6": ("Tokyo", "NRT"),
    "7": ("Osaka", "KIX"), "8": ("Seoul", "ICN"),
    "9": ("Singapore", "SIN"), "10": ("Bangkok", "BKK"),
    "11": ("Hong Kong", "HKG"), "12": ("Taipei", "TPE"),
    "13": ("London", "LHR"), "14": ("Paris", "CDG"),
    "15": ("Amsterdam", "AMS"), "16": ("Hanoi", "HAN"),
    "17": ("Ho Chi Minh", "SGN"), "18": ("Da Nang", "DAD"),
}

VAGUE_REGIONS = {
    "usa", "america", "us", "united states", "mỹ",
    "europe", "eu", "châu âu",
    "asia", "southeast asia", "sea", "châu á", "đông nam á",
    "france", "pháp", "vietnam", "việt nam", "vn", 
    "japan", "nhật bản", "nhật", "korea", "hàn quốc", "hàn",
    "china", "trung quốc", "thailand", "thái lan", "thái",
    "uk", "united kingdom", "anh", "germany", "đức", "italy", "ý",
    "australia", "úc", "canada", "taiwan", "đài loan",
    "singapore", "malaysia", "indonesia"
}

def _is_vague(text: str) -> bool:
    if not text: return False
    return text.lower().strip() in VAGUE_REGIONS

def _ask_clarify_location(vague_loc: str, loc_type: str) -> str:
    loc = vague_loc.lower().strip()

    if loc in ("usa", "us", "america", "united states", "mỹ"):
        subset = {k: v for k, v in POPULAR_CITIES.items() if int(k) <= 5}
        label = "🇺🇸 USA"
    elif loc in ("europe", "eu", "châu âu", "france", "pháp", "uk", "anh", "germany", "đức"):
        subset = {k: v for k, v in POPULAR_CITIES.items() if 13 <= int(k) <= 15}
        label = "🇪🇺 Europe"
    elif loc in ("vietnam", "việt nam", "vn"):
        subset = {k: v for k, v in POPULAR_CITIES.items() if 16 <= int(k) <= 18}
        label = "🇻🇳 Vietnam"
    elif loc in ("asia", "châu á", "japan", "nhật bản", "korea", "hàn quốc", "china", "taiwan"):
        subset = {k: v for k, v in POPULAR_CITIES.items() if 6 <= int(k) <= 12}
        label = "🌏 Asia"
    else:
        subset = POPULAR_CITIES
        label = "All destinations"

    print(f"\n{C.YELLOW}⚠️ '{vague_loc}' là một quốc gia/khu vực. Hệ thống cần tên thành phố hoặc mã sân bay cho {loc_type}.{C.RESET}")
    print(f"{C.CYAN}Bạn muốn chọn thành phố nào? ({label}){C.RESET}\n")
    for k, (city, code) in subset.items():
        print(f"  {k:>2}. {city:15s}  ({code})")
    
    while True:
        choice = input(f"\n{C.YELLOW}{loc_type} của bạn: {C.RESET}").strip()
        if not choice: continue
        if choice in subset:
            city, code = subset[choice]
            ok(f"{loc_type} đã được thiết lập → {city} ({code})")
            return city
        ok(f"{loc_type} đã được thiết lập → {choice}")
        return choice

def _ask_clarify_missing(intent: dict) -> dict:
    updated = dict(intent)

    orig = updated.get("origin", "")
    if not orig:
        print(f"\n{C.YELLOW}⚠️ Bạn muốn bay TỪ đâu?{C.RESET}")
        orig = input(f"{C.YELLOW}Điểm đi (vd: Hanoi, SGN): {C.RESET}").strip()
    if _is_vague(orig):
        orig = _ask_clarify_location(orig, "ĐIỂM ĐI")
    updated["origin"] = orig

    dest = updated.get("destination", "")
    if not dest:
        print(f"\n{C.YELLOW}⚠️ Bạn muốn bay ĐẾN đâu?{C.RESET}")
        dest = input(f"{C.YELLOW}Điểm đến: {C.RESET}").strip()
    if _is_vague(dest):
        dest = _ask_clarify_location(dest, "ĐIỂM ĐẾN")
    updated["destination"] = dest

    if not updated.get("date"):
        print(f"\n{C.YELLOW}⚠️ Bạn muốn đi vào ngày nào?{C.RESET}")
        updated["date"] = input(f"{C.YELLOW}Ngày đi (YYYY-MM-DD): {C.RESET}").strip()

    if not updated.get("return_date") or updated.get("return_date") == "":
        print(f"\n{C.YELLOW}⚠️ Đây là chuyến bay một chiều hay khứ hồi?{C.RESET}")
        is_round = input(f"{C.YELLOW}Nhập 'y' nếu là khứ hồi (nhấn Enter nếu 1 chiều): {C.RESET}").strip().lower()
        if is_round in ['y', 'yes', 'có', 'co']:
            updated["return_date"] = input(f"{C.YELLOW}Ngày về (YYYY-MM-DD): {C.RESET}").strip()
        else:
            updated["return_date"] = "ONE_WAY"

    return updated

# ============================================================
# SMART MEMORY LOGIC
# ============================================================
def update_memory(current_memory: dict, new_intent: dict) -> dict:
    updated = current_memory.copy()
    GARBAGE = ["city", "somewhere", "unknown", "none", "null", "airport", "location"]

    for key in ["origin", "destination", "date", "return_date"]:
        new_val = new_intent.get(key)
        if new_val:
            val_str = str(new_val).strip().lower()
            if val_str not in GARBAGE and val_str != "":
                if key == "return_date" and val_str in ["one way", "1 chiều", "no"]:
                    updated[key] = "ONE_WAY"
                else:
                    updated[key] = new_val
    return updated

# ============================================================
# PIPELINE
# ============================================================
class SkyNodePipeline:
    def __init__(self, serpapi_key: str = None):
        self.flight_agent = FlightSearchAgent(serpapi_key=serpapi_key)
        self.miles_agent = MilesArchitectAgent()
        self.concierge = ConciergeAgent()

    def run(self, query: str, profile: dict):
        step(1, "Searching flights...")
        flight_result = self.flight_agent.search(query)
        if not flight_result.success:
            err(f"Lỗi: {flight_result.error_message}")
            return

        ok(f"Tìm thấy {len(flight_result.flights)} chuyến bay.")

        step(2, f"Analyzing miles for '{profile['card']}'...")
        miles_result = self.miles_agent.analyze_flights(
            flights=flight_result.to_miles_agent_input(),
            user_card=profile["card"],
            current_miles=profile["current_miles"],
            current_miles_airline=profile["ff_airline"]
        )

        step(3, "Writing recommendation...")
        final = self.concierge.synthesize(flight_result, miles_result, profile)
        
        print(f"\n{C.BOLD}{C.GREEN}{'═'*60}{C.RESET}")
        print(f"🏆 {final.headline}")
        print(f"{C.GREEN}{'═'*60}{C.RESET}")
        print(f"{C.BOLD}Tại sao chọn:{C.RESET} {final.why_this_flight}")
        print(f"{C.BOLD}Mẹo dùng thẻ:{C.RESET} {final.credit_card_tip}")
        print(f"\n{C.DIM}{final.full_report}{C.RESET}\n")

# ============================================================
# TERMINAL RUNNER
# ============================================================
def run_terminal():
    pipeline = SkyNodePipeline(serpapi_key=os.getenv("SERPAPI_KEY"))
    
    # Bạn có thể điều chỉnh profile mặc định ở đây
    profile = {"card": "Vietnam Airlines BIDV Visa", "current_miles": 50000, "ff_airline": "Vietnam Airlines"}
    
    session_memory = {"origin": "", "destination": "", "date": "", "return_date": ""}

    print(f"\n{C.BOLD}{C.BLUE}SkyNode AI - Trình điều phối bay thông minh (Có trí nhớ){C.RESET}")
    print(f"{C.DIM}Gõ 'reset' để xóa nhớ, 'exit' để thoát.{C.RESET}\n")

    from flight_core import extract_intent

    while True:
        try:
            user_input = input(f"{C.BOLD}{C.BLUE}Bạn: {C.RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.DIM}Goodbye! ✈️{C.RESET}")
            break

        if not user_input: continue
        if user_input.lower() in ["exit", "quit"]: break
        if user_input.lower() == "reset":
            session_memory = {"origin": "", "destination": "", "date": "", "return_date": ""}
            ok("Đã xóa trí nhớ. Bạn có thể bắt đầu tìm chuyến mới!"); continue

        # 1. Bóc tách ý định (NLP)
        new_intent = extract_intent(user_input)

        # 2. Cập nhật trí nhớ (Chỉ đè cái mới, giữ cái cũ)
        session_memory = update_memory(session_memory, new_intent)

        # 3. Kiểm tra thiếu thông tin (Sẽ gọi thẳng hàm _ask_clarify_missing đã định nghĩa ở trên)
        session_memory = _ask_clarify_missing(session_memory)

        # 4. Build Query từ trí nhớ hoàn chỉnh
        orig = session_memory['origin'].split('/')[0].strip()
        dest = session_memory['destination'].split('/')[0].strip()
        
        query = f"Flights from {orig} to {dest} on {session_memory['date']}"
        if session_memory['return_date'] and session_memory['return_date'] != "ONE_WAY":
            query += f" round-trip returning {session_memory['return_date']}"

        # 5. Hiển thị trạng thái AI đang nhớ
        print(f"\n{C.DIM}→ AI đang nhớ: {orig} ✈ {dest} | Đi: {session_memory['date']} | Về: {session_memory['return_date']}{C.RESET}")

        # 6. Chạy Pipeline
        pipeline.run(query, profile)

if __name__ == "__main__":
    run_terminal()