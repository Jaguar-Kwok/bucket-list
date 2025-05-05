import streamlit as st
import function_db as db
from datetime import datetime
import pandas as pd

st.title("活動管理")

# Event selection for editing
events = db.get_events()
event_options = {e['id']: f"{e['name_tc']} ({e['start_date']})" for e in events}
selected_id = st.selectbox("選擇要編輯的活動", [None] + list(event_options.keys()),
                         format_func=lambda x: event_options.get(x, "新建活動"))

# Event form
with st.expander("活動表單", expanded=True):
    with st.form("event_form"):
        # Load existing data if editing
        if selected_id:
            existing = next(e for e in events if e['id'] == selected_id)
        else:
            existing = None
            
        name_tc = st.text_input("活動名稱（中文）", value=existing['name_tc'] if existing else "")
        name_en = st.text_input("活動名稱（英文）", value=existing['name_en'] if existing else "")
        description_tc = st.text_area("活動描述（中文）", value=existing['description_tc'] if existing else "")
        start_date = st.date_input("開始日期", value=datetime.strptime(existing['start_date'], "%Y-%m-%d").date() if existing else datetime.today())
        end_date = st.date_input("結束日期", value=datetime.strptime(existing['end_date'], "%Y-%m-%d").date() if existing else datetime.today())
        location = st.text_input("活動地點", value=existing['location_address_tc'] if existing else "")
        quota = st.number_input("名額", min_value=1, value=existing['quota'] if existing else 1)
        
        # Added Data Editor
        if selected_id:
            event_df = pd.DataFrame([existing])
            edited_event = st.data_editor(event_df, num_rows="fixed")
            new_event = edited_event.iloc[0].to_dict()
        else:
            new_event = {
                'name_tc': name_tc,
                'name_en': name_en,
                'description_tc': description_tc,
                'start_date': start_date,
                'end_date': end_date,
                'location_address_tc': location,
                'quota': quota,
                'organizer_tc': existing['organizer_tc'] if existing else "",
                'activity_nature_tc': existing['activity_nature_tc'] if existing else "",
                'sessions': existing['sessions'] if existing else "[]",
                'thumbnail_url': existing['thumbnail_url'] if existing else ""
            }
        
        if st.form_submit_button("保存活動"):
            if selected_id:
                new_event['id'] = selected_id
            db.save_event(new_event)
            st.rerun()