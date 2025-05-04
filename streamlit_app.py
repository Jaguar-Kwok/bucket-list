import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime
import function_db as db

DB_NAME = "community_center.db"

# Session state setup
if 'selected_student' not in st.session_state:
    st.session_state.selected_student = None
if 'selected_event' not in st.session_state:
    st.session_state.selected_event = None



# Initialize database and fetch external events
db.init_db()
db.fetch_and_save_external_events()

# Data management in sidebar
st.sidebar.header("數據管理")
if st.sidebar.button("刷新外部活動數據"):
    db.fetch_and_save_external_events()
    st.sidebar.success("活動數據已更新")

if st.sidebar.button("導出所有數據"):
    with pd.ExcelWriter('community_data.xlsx') as writer:
        pd.read_sql("SELECT * FROM events", sqlite3.connect(DB_NAME)).to_excel(writer, sheet_name='Events', index=False)
        pd.read_sql("SELECT * FROM students", sqlite3.connect(DB_NAME)).to_excel(writer, sheet_name='Students', index=False)
        pd.read_sql("SELECT * FROM attendance", sqlite3.connect(DB_NAME)).to_excel(writer, sheet_name='Attendance', index=False)
    st.sidebar.success("數據導出成功")

pg = st.navigation([
    st.Page("page_home.py", title="Home"),
    st.Page("page_event.py", title="Events"),
    st.Page("page_students.py", title="Students"),
    st.Page("page_event_details.py", title="Event Details"),
    st.Page("page_student_details.py", title="Student Details")
])
pg.run()