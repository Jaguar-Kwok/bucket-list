import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime
import function_db as db

# Display upcoming events
st.subheader("即將到來的活動")
all_events = db.get_events()
upcoming_events = [event for event in all_events if event['start_date'] >= str(datetime.now().date())][:5]
if upcoming_events:
    for event in upcoming_events:
        st.markdown(f"""
        - **{event['name_tc']}**  
          日期: {event['start_date']}  
          地點: {event['location_address_tc']}
        """)
else:
    st.info("暫無即將到來的活動")

# Optional: Display some statistics
st.subheader("統計數據")
all_students = db.get_students()
total_students = len(all_students)
total_events = len(all_events)

st.markdown(f"""
- 總學生數: {total_students}
- 總活動數: {total_events}
""")