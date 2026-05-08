import streamlit as st
import pandas as pd
import numpy as np
import data as data # Import our utility functions

# Set page to wide mode to fit the dashboard layout
st.set_page_config(layout="wide", page_title="SkyNode AI Dashboard")

# --- DATA INITIALIZATION ---
# Fetching data from data.py to keep the main script clean
user_info = data.get_user_profile()
calendar_events = data.get_calendar_events()

# Initialize session state for the search query to enable interactive chips
if "search_val" not in st.session_state:
    st.session_state.search_val = ""

# --- HEADER SECTION ---
# Top bar: Logo | Search Input | Profile
header_left, header_mid, header_right = st.columns([1, 4, 1])

with header_left:
    st.title("SkyNode")

with header_mid:
    # Large input for natural language queries 
    search_query = st.text_input(
        "Search", 
        value=st.session_state.search_val, 
        placeholder="Where to? (e.g., 'Flights for my SG trip')", 
        label_visibility="collapsed"
    )

    # Suggestion Chips: Clicking these updates the session state
    st.caption("Quick search from calendar:")
    chip_cols = st.columns(len(calendar_events) + 5)
    for i, event in enumerate(calendar_events):
        if chip_cols[i].button(f"📅 {event['name']}", key=f"btn_{i}"):
            st.session_state.search_val = f"Find tickets for {event['name']} in {event['loc']}"
            st.rerun() # Refresh to update the text input value

with header_right:
    # User profile popover using data from user_info
    with st.popover("👤 Profile"):
        st.markdown(f"**Settings for {user_info['name']}**")
        st.checkbox("Membership Status", value=True)
        st.selectbox("Default Class", ["Economy", "Premium Economy", "Business", "First"])
        st.number_input("Max Budget ($)", value=user_info['budget'])


# --- MAIN CONTENT ---
# Split into Left Column (Widgets) and Right Column (Main View)
left_col, right_col = st.columns([1, 3], gap="medium")

# --- LEFT COLUMN: Side Widgets ---
with left_col:
    # Calendar widget with "red/green light" indicators
    st.subheader("📅 Calendar")
    st.date_input("Travel Dates", label_visibility="collapsed")
    st.caption("🟢 Green: High point value | 🔴 Red: Low value")
    
    st.divider()
    
    # Miles info
    st.subheader("💳 Miles")
    st.progress(0.65, text="Miles Progress: 65%")
    
    st.divider()
    
    # Credit Card info
    st.subheader("💳 Cards")
    st.write(f"Active Cards: {', '.join(user_info['cards'])}")
    
    st.divider()

    # Storage Strategy (Placeholder for carousel)
    st.subheader("📦 Storage Strategy")
    st.info("Current Strategy: Maximize Transfer Bonuses")

# --- RIGHT COLUMN: Analytics & Flights ---
with right_col:
    # Status bar
    status_container = st.container(border=True)
    with status_container:
        st.write("✨ **Status:** Ready to analyze your next trip...")
    
    # Buy/Wait Indicator & Price Trend Chart
    indicator_col, chart_col = st.columns([1, 3])
    
    with indicator_col:
        st.metric(label="Action Signal", value="BUY", delta="Price Trending Up")
        st.write("AI Suggestion: Book within 48 hours.")
        
    with chart_col:
        # Fetching chart data from data.py
        price_data = data.get_price_trend_data()
        st.line_chart(price_data, height=180)

    # Search Optimization Filters
    st.write("---")
    f_col1, f_col2, f_col3 = st.columns(3)
    f_col1.selectbox("Filter by Event", ["All Events"] + [e['name'] for e in calendar_events], label_visibility="collapsed")
    f_col2.button("🚀 Optimize Departure", use_container_width=True)
    f_col3.button("🛬 Optimize Arrival", use_container_width=True)

    # Flight Results (Collapsed/Expanded States)
    st.subheader("✈️ Recommended Flights")
    
    # Fetch results based on current search query
    flights = data.get_recommended_flights(search_query)

    for flight in flights:
        label = f"{flight['airline']} | {flight['time']} ({flight['route']}) | ${flight['price']} USD | {flight['badge']}"

        with st.expander(label):
            # Expanded State Content
            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                st.write("**Flight Segments**")
                st.caption(f"Class: {flight['class']}")
                st.caption(f"Aircraft: {flight['aircraft']}")
            with e_col2:
                st.write("**Miles Architect**")
                st.write(f"Earn: {flight['miles']}")
                st.write("Route Bonus: +500 pts")
            with e_col3:
                st.write("**Credit Card Strategy**")
                st.success(flight['card_strategy'])

# --- FOOTER ---
# Hardware Dashboard at the bottom
st.divider()
st.subheader("🖥️ AMD Ryzen™ AI Monitor")
hw_col1, hw_col2, hw_col3, hw_col4 = st.columns(4)
hw_col1.metric("NPU Load", "12%")
hw_col2.metric("Inference Latency", "45ms")
hw_col3.metric("Privacy Status", "Encrypted")
hw_col4.metric("Process", "Edge (Local)")