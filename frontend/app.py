import streamlit as st
import os
import sys
import requests
import pandas as pd

# 確保路徑對齊
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline import run_full_pipeline
# 引入妳後端真實的資料庫，不要再用假的 data.py 了！
from core.miles_core import CREDIT_CARD_DB, AIRLINE_ALLIANCE_DB

st.set_page_config(layout="wide", page_title="SkyNode AI Dashboard")

# --- 1. 自動抓取後端的「動態資料列表」 ---
# 從妳的 miles_core.py 裡面抓出所有的信用卡名字
AVAILABLE_CARDS = list(CREDIT_CARD_DB.keys())
# 從妳的資料庫抓出所有航空公司
AVAILABLE_AIRLINES = [name for name in AIRLINE_ALLIANCE_DB.keys() if len(name) > 3]

# --- 2. Onboarding 閘門 (輸入個人資料) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("✈️ SkyNode: Initialize Your Agent")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", "Claire")
            # 這裡就是動態的了！讀取自 miles_core.py
            card = st.selectbox("Your Primary Credit Card", AVAILABLE_CARDS)
        with col2:
            miles = st.number_input("Current Miles", value=18000)
            airline = st.selectbox("Frequent Flyer Program", AVAILABLE_AIRLINES)
        
        if st.button("Connect Google Calendar & Enter 🚀", use_container_width=True):
            st.session_state.user_profile = {
                "name": name,
                "card": card,
                "current_miles": miles,
                "ff_airline": airline
            }
            # 嘗試觸發登入
            try: requests.get("http://127.0.0.1:8005/login", timeout=1)
            except: pass
            
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# ============================================================
# 3. Dashboard 主畫面 (完全接上 Pipeline)
# ============================================================

# --- 側邊欄：顯示「真的」個人狀態 ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_profile['name']}")
    st.write(f"💳 **Card:** {st.session_state.user_profile['card']}")
    st.write(f"✈️ **Miles:** {st.session_state.user_profile['current_miles']:,} ({st.session_state.user_profile['ff_airline']})")
    if st.button("Reset Session"):
        st.session_state.logged_in = False
        st.rerun()

# --- 主搜尋框 ---
prompt = st.chat_input("Where to? (e.g., Flights from TPE to HAN on 2026-06-01)")

# --- 左側：當週日曆 (呼叫真實 API) ---
left_col, right_col = st.columns([1, 3], gap="large")

with left_col:
    st.subheader("📅 Your Itinerary")
    try:
        # 呼叫妳 8005 的真實資料
        cal_data = requests.get("http://127.0.0.1:8005/get-calendar", timeout=2).json()
        events = cal_data.get("calendar_events", [])
        for ev in events[:5]:
            st.markdown(f"""
            <div style="border-left:4px solid #34d399; background:rgba(52,211,153,0.1); padding:10px; margin-bottom:10px; border-radius:4px;">
                <div style="font-size:0.8rem; color:#a78bfa;">{ev.get('start', {}).get('dateTime', 'All Day')}</div>
                <div style="font-weight:600;">{ev.get('summary', 'Busy')}</div>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.info("Calendar service is sleeping... Run login.py first!")

# --- 右側：Pipeline 結果 ---
with right_col:
    if not prompt:
        st.write("✨ **Status:** Ready. Input your travel intent to start the multi-agent analysis.")
    else:
        with st.spinner("🤖 Agents are working..."):
            # 真正的後端呼叫！
            result = run_full_pipeline(prompt, st.session_state.user_profile)
            
            if "error" in result:
                st.error(result["error"])
            elif result.get("stage") == "complete":
                rec = result["recommendation"]
                st.success(f"🏆 {rec['headline']}")
                
                # 顯示機票 (真正的 SerpApi 結果)
                for f in result["flights"]:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.markdown(f"**{f['airline']}** ({f['flight_number']})")
                        c2.write(f"🕒 {f['departure_time']}")
                        c3.subheader(f"${f['price_usd']:.0f}")
                
                with st.expander("📊 Full Rewards Analysis"):
                    st.markdown(rec["full_report"])
            elif result.get("stage") == "need_more_info":
                st.info(result.get("message", "Please provide more information about your travel plans."))