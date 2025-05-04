import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import function_db as db

DB_NAME = "community_center.db"

st.title("活動詳情")

# Event selection with collapsible list
events = db.get_events()
event_map = {e['id']: e for e in events}

with st.expander("所有活動", expanded=not st.session_state.selected_event):
    cols = st.columns(3)
    for idx, event in enumerate(events):
        with cols[idx % 3]:
            if st.button(f"📅 {event['name_tc']}", key=f"all_event_{event['id']}"):
                st.session_state.selected_event = event['id']

# Selected event details
if st.session_state.selected_event:
    event = event_map.get(st.session_state.selected_event)
    if event:
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
            st.write(f"**主辦單位:** {event['organizer_tc']}")
            st.write(f"**活動性質:** {event['activity_nature_tc']}")
            st.write(f"**描述:** {event['description_tc']}")
        
        if event['location_lat'] and event['location_lng']:
            st.subheader("活動地點")
            df = pd.DataFrame({
                'lat': [event['location_lat']],
                'lon': [event['location_lng']]
            })
            st.map(df, use_container_width=True)
        
        st.divider()
        st.subheader("學生管理")
        
        # Get all students and current registrations
        all_students = db.get_students()
        conn = sqlite3.connect(DB_NAME)
        current_reg = conn.execute('''SELECT student_id FROM attendance 
                                   WHERE event_id = ?''', 
                                (event['id'],)).fetchall()
        conn.close()
        current_reg_ids = [r[0] for r in current_reg]
        
        # Student registration multiselect
        student_options = {s['id']: s['name'] for s in all_students}
        selected_ids = st.multiselect(
            "註冊學生",
            options=list(student_options.keys()),
            format_func=lambda x: student_options[x],
            default=current_reg_ids
        )
        
        # Save registration changes
        if st.button("保存註冊名單"):
            conn = sqlite3.connect(DB_NAME)
            # Remove unselected students
            conn.execute('''DELETE FROM attendance 
                         WHERE event_id = ? AND student_id NOT IN ({})'''.format(
                             ','.join(['?']*len(selected_ids))),
                         [event['id']] + selected_ids)
            # Add new registrations
            for student_id in selected_ids:
                conn.execute('''INSERT OR IGNORE INTO attendance 
                             (event_id, student_id, attended, updated_at)
                             VALUES (?,?,?,?)''',
                          (event['id'], student_id, False, datetime.now()))
            conn.commit()
            conn.close()
            st.success("註冊名單已更新")
        
        # Attendance editor
        st.subheader("出席記錄")
        conn = sqlite3.connect(DB_NAME)
        attendance = pd.read_sql('''SELECT students.id as student_id, students.name, attendance.attended
                                  FROM attendance
                                  JOIN students ON attendance.student_id = students.id
                                  WHERE event_id = ?''', 
                               conn, params=(event['id'],))
        conn.close()
        
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
            
            # Save attendance changes
            if not edited_attendance.equals(attendance):
                conn = sqlite3.connect(DB_NAME)
                for _, row in edited_attendance.iterrows():
                    conn.execute('''UPDATE attendance SET attended = ?, updated_at = ?
                                 WHERE event_id = ? AND student_id = ?''',
                              (row['attended'], datetime.now(), event['id'], row['student_id']))
                conn.commit()
                conn.close()
                st.success("出席記錄已更新")
        else:
            st.info("暫無註冊學生")         


