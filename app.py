import streamlit as st
import ollama
import os
from flight_agent import (
    extract_flight_info, search_flights,
    get_airport_code, format_duration, format_price
)

st.set_page_config(page_title="✈️ AI Flight Agent", page_icon="✈️", layout="wide", initial_sidebar_state="expanded")

# --- CSS (Giữ nguyên) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
* { font-family: 'Plus Jakarta Sans', sans-serif !important; }
.stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
.main-header { text-align:center; padding:1.5rem 0 1rem; }
.main-header h1 { font-size:2.8rem; font-weight:800; background:linear-gradient(135deg,#a78bfa,#60a5fa,#34d399); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; }
.main-header p { color:#94a3b8; font-size:1rem; margin-top:0.4rem; }
.flight-card { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:1.2rem 1.5rem; margin:0.5rem 0; }
.flight-card.best { border-color:rgba(52,211,153,0.5); background:rgba(52,211,153,0.05); }
.best-badge { background:linear-gradient(135deg,#059669,#34d399); color:white; font-size:0.7rem; font-weight:700; padding:2px 10px; border-radius:20px; }
.airline-name { color:#a78bfa; font-weight:700; font-size:1rem; }
.flight-time { font-family:'Space Mono',monospace !important; font-size:1.5rem; font-weight:700; color:white; }
.flight-code { color:#64748b; font-size:0.8rem; }
.duration-line { color:#94a3b8; font-size:0.8rem; text-align:center; }
.price-tag { font-family:'Space Mono',monospace !important; font-size:1.3rem; font-weight:700; color:#34d399; }
.stops-nonstop { background:rgba(52,211,153,0.15); color:#34d399; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:600; }
.stops-one { background:rgba(251,191,36,0.15); color:#fbbf24; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:600; }
.chip { display:inline-block; background:rgba(167,139,250,0.15); border:1px solid rgba(167,139,250,0.3); color:#a78bfa; padding:4px 12px; border-radius:20px; font-size:0.82rem; margin:3px; }
.metric-card { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:1rem; text-align:center; }
.metric-value { font-size:1.5rem; font-weight:800; color:#a78bfa; }
.metric-label { font-size:0.8rem; color:#64748b; }
section[data-testid="stSidebar"] { background:rgba(0,0,0,0.3) !important; border-right:1px solid rgba(255,255,255,0.08); }
section[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
hr { border-color:rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_count" not in st.session_state:
    st.session_state.search_count = 0
if "api_key" not in st.session_state:
    st.session_state.api_key = None

# --- SIDEBAR CẬP NHẬT ---
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Ô nhập API Key
    key_input = st.text_input(
        "SerpApi Key", 
        type="password", 
        placeholder="Enter key here...",
        help="Get your key at serpapi.com."
    )
    
    # Thêm nút Set Key để người dùng chủ động xác nhận
    if st.button("🚀 Set Key", use_container_width=True):
        if key_input:
            st.session_state.api_key = key_input
            st.success("API Key applied!")
        else:
            st.warning("Please enter a key first.")

    st.markdown("---")
    st.markdown("### 🌍 Supported Languages")
    st.markdown("🇬🇧 English | 🇻🇳 Vietnamese | 🇨🇳 Chinese")
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{st.session_state.search_count}</div><div class="metric-label">Searches</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len([m for m in st.session_state.messages if m["role"]=="user"])}</div><div class="metric-label">Messages</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.search_count = 0
        st.rerun()

st.markdown('<div class="main-header"><h1>✈️ AI Flight Agent</h1><p>Search Flights • Multi-language • IATA Codes</p></div>', unsafe_allow_html=True)

# --- Các hàm phụ trợ (Giữ nguyên) ---
def flight_card_html(f):
    is_best = f.get("is_best", False)
    card_class = "flight-card best" if is_best else "flight-card"
    stops = f.get("stops", 0)
    stops_label = "✅ Non-stop" if stops == 0 else f"🔄 {stops} Stop(s)"
    stops_class = "stops-nonstop" if stops == 0 else "stops-one"
    best_html = '<span class="best-badge">⭐ Best Option</span>' if is_best else ""
    return f"""<div class="{card_class}">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
    <span class="airline-name">✈ {f.get('airline','?')} <span style="color:#475569;font-size:0.8rem;">{f.get('flight_number','')}</span></span>
    <div>{best_html} <span class="{stops_class}">{stops_label}</span></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr auto 1fr auto;gap:0.5rem;align-items:center;">
    <div><div class="flight-time">{f.get('departure_time','?')}</div><div class="flight-code">{f.get('departure_airport','?')}</div></div>
    <div style="text-align:center;padding:0 0.5rem;"><div class="duration-line">──── {format_duration(f.get('duration',0))} ────</div><div style="font-size:0.7rem;color:#475569;">{f.get('travel_class','Economy')}</div></div>
    <div><div class="flight-time">{f.get('arrival_time','?')}</div><div class="flight-code">{f.get('arrival_airport','?')}</div></div>
    <div style="text-align:right;"><div class="price-tag">{format_price(f.get('price',0))}</div><div style="font-size:0.72rem;color:#475569;">/person</div></div>
  </div>
</div>"""

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "flights":
            st.markdown(f"### 🔍 {msg['origin']} → {msg['destination']}")
            for f in msg["flights"]:
                st.markdown(flight_card_html(f), unsafe_allow_html=True)
            st.success(msg.get("summary", ""))
        else:
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("✈️ Ask in English, Vietnamese, Chinese..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🧠 Analyzing request..."):
            info = extract_flight_info(prompt)

        if info.get("action") == "search_flight":
            origin_raw = info.get("origin", "")
            dest_raw = info.get("destination", "")
            travel_date = info.get("date", "")
            return_date = info.get("return_date")
            adults = info.get("adults", 1)
            lang = info.get("language", "en")
            
            origin_code = get_airport_code(origin_raw) if origin_raw else ""
            dest_code = get_airport_code(dest_raw) if dest_raw else ""

            if not origin_raw or not dest_raw or not travel_date:
                reply = "⚠️ Please provide origin, destination, and date."
                st.markdown(reply)
                st.session_state.messages.append({"role":"assistant","content":reply})
            else:
                with st.spinner(f"🔍 Searching {origin_code} → {dest_code}..."):
                    # Sử dụng key từ session_state (ưu tiên key người dùng vừa bấm nút Set)
                    result = search_flights(
                        origin_code, 
                        dest_code, 
                        travel_date, 
                        return_date, 
                        adults, 
                        api_key=st.session_state.api_key
                    )

                if result["success"] and result["flights"]:
                    st.session_state.search_count += 1
                    flights = result["flights"]
                    st.markdown(f"### 🔍 {origin_raw.upper()} → {dest_raw.upper()}")
                    for f in flights:
                        st.markdown(flight_card_html(f), unsafe_allow_html=True)
                    
                    min_p = format_price(min([f["price"] for f in flights]))
                    summary = f"✅ Found {len(flights)} flights. From {min_p}."
                    st.success(summary)
                    st.session_state.messages.append({"role":"assistant","type":"flights","flights":flights,"origin":origin_raw.upper(),"destination":dest_raw.upper(),"summary":summary,"content":summary})
                else:
                    err = f"😔 No flights found. {result.get('message', '')}"
                    st.warning(err)
                    st.session_state.messages.append({"role":"assistant","content":err})
        else:
            with st.spinner("🤖 Thinking..."):
                history = [{"role":m["role"],"content":m.get("content","")} for m in st.session_state.messages if m.get("content")]
                response = ollama.chat(model="llama3", messages=[{"role":"system","content":"Flight assistant. Respond in user language."}]+history)
                reply = response["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role":"assistant","content":reply})