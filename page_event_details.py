import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import function_db as db

DB_NAME = "community_center.db"

st.title("活動詳情")

# Event selection with collapsible list and search functionality
events = db.get_events()
events.sort(key=lambda x: x['start_date'], reverse=True)  # Sort events by most recent

# Create event_map dynamically to fix the NameError
event_map = {event['id']: event for event in events}

search_term = st.text_input("搜索活動", placeholder="輸入活動編號、名稱或日期").lower()
filtered_events = [
    event for event in events 
    if (search_term in str(event['external_id']).lower() or  # Changed from 'id' to 'subActivityCode'
        search_term in event['name_tc'].lower() or 
        search_term in event['start_date'].lower())
]

with st.expander("所有活動", expanded=not st.session_state.selected_event):
    for event in filtered_events:
        event_label = f"{event['start_date']} - {event['external_id']} - {event['name_tc']}"  # Included subActivityCode
        if st.button(f"📅 {event_label}", key=f"all_event_{event['id']}"):
            st.session_state.selected_event = event['id']

# Selected event details
if st.session_state.selected_event:
    event = event_map.get(st.session_state.selected_event)  # Now event_map is defined
    if event:
        # Ensure no null values in lat/lon before creating DataFrame
        df = pd.DataFrame({
            'lat': [event['location_lat']],
            'lon': [event['location_lng']]
        }).dropna(subset=['lat', 'lon'])

        st.divider()
        st.subheader("活動詳細資料")
        col1, col2 = st.columns(2)
        with col1:
            if event['thumbnail_url']:
                st.image(event['thumbnail_url'], width=300)
            st.write(f"**活動編號:** {event['external_id']}")
            st.write(f"**開始日期:** {event['start_date']}")
            st.write(f"**結束日期:** {event['end_date']}")
            st.write(f"**名額:** {event['quota']}")
            
        with col2:
            st.write(f"**地點:** {event['location_address_tc']}")
            
            if not df.empty: 
                google_maps_location_url = f"https://www.google.com/maps?q={event['location_lat']},{event['location_lng']}"
                st.markdown(f"[📍 在Google地圖中查看]({google_maps_location_url})", unsafe_allow_html=True)
                google_maps_navigation_url = f"https://www.google.com/maps/dir/?api=1&origin=香港聖公會馬鞍山(南)青少年綜合服務中心+賽馬會青年幹線&destination={event['location_lat']},{event['location_lng']}"
                st.markdown(f"[📍 在Google地圖中導航]({google_maps_navigation_url})", unsafe_allow_html=True)

        if not df.empty:  # Only display the map if there are valid coordinates
            st.subheader("活動地點")
            st.map(df, use_container_width=True)

        st.divider()
        st.subheader("學生管理")
        
        all_students = db.get_students()
        current_reg_ids = db.get_current_registrations(event['id'])
        
        student_options = {s['id']: s['name'] for s in all_students}
        selected_ids = st.multiselect(
            "註冊學生",
            options=list(student_options.keys()),
            format_func=lambda x: student_options[x],
            default=current_reg_ids
        )
        
        if st.button("保存註冊名單"):
            db.save_registration_changes(event['id'], selected_ids)
            st.success("註冊名單已更新")
        
        st.subheader("出席記錄")
        attendance = db.get_attendance_records(event['id'])
        
        if not attendance.empty:
            edited_attendance = st.data_editor(
                attendance,
                column_config={
                    "student_id": None,
                    "name": st.column_config.TextColumn("學生姓名", disabled=True),
                    "attended": st.column_config.CheckboxColumn("出席")
                },
                hide_index=True,
                key=f"attendance_{event['id']}"
            )
            
            if not edited_attendance.equals(attendance):
                db.update_attendance_records(edited_attendance, event['id'])
                st.success("出席記錄已更新")
        else:
            st.info("暫無註冊學生")