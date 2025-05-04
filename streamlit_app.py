import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime
import function_db as db

DB_NAME = "community_center.db"

API_URL = "https://activity.striveandrise.gov.hk/api/activities?targetGroups=SKHWC"


# Session state setup
if 'selected_student' not in st.session_state:
    st.session_state.selected_student = None
if 'selected_event' not in st.session_state:
    st.session_state.selected_event = None


def students_page():
    st.title("學生管理")
    
    # Student selection for editing
    students = db.get_students()
    student_options = {s['id']: s['name'] for s in students}
    selected_id = st.selectbox("選擇要編輯的學生", [None] + list(student_options.keys()),
                             format_func=lambda x: student_options.get(x, "新建學生"))
    
    # Student form
    with st.expander("學生表單", expanded=True):
        with st.form("student_form"):
            # Load existing data if editing
            if selected_id:
                existing = next(s for s in students if s['id'] == selected_id)
            else:
                existing = None
                
            name = st.text_input("學生姓名", value=existing['name'] if existing else "")
            contact = st.text_input("聯絡方式", value=existing['contact'] if existing else "")
            
            if st.form_submit_button("保存學生"):
                student = {'name': name, 'contact': contact}
                if selected_id:
                    student['id'] = selected_id
                db.save_student(student)
                st.rerun()

def event_details_page():
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

def student_details_page():
    st.title("學生詳情")
    
    # All students list
    st.subheader("選擇學生")
    students = db.get_students()
    cols = st.columns(3)
    for idx, student in enumerate(students):
        with cols[idx % 3]:
            if st.button(f"👤 {student['name']}", key=f"all_student_{student['id']}"):
                st.session_state.selected_student = student['id']
    
    # Selected student details
    if st.session_state.selected_student:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Add this line
        student = conn.execute('SELECT * FROM students WHERE id = ?', 
                            (st.session_state.selected_student,)).fetchone()
        attendance = conn.execute('''SELECT events.name_tc, events.start_date, attendance.attended
                                FROM attendance
                                JOIN events ON attendance.event_id = events.id
                                WHERE student_id = ?''', 
                                (st.session_state.selected_student,)).fetchall()
        conn.close()
        df = pd.DataFrame(attendance, columns=['活動名稱', '日期', '出席'])
     
        st.divider()
        st.subheader("學生詳細資料")
        
        st.write(f"**姓名:** {student['name']}")
        st.write(f"**聯絡方式:** {student['contact']}")
        st.write(f"**註冊時間:** {student['registered_at']}")
        if attendance:
            st.write(f"Registed Event: {len(df.index)} Attended Event: {(df['出席'] == 1).sum()} ")
        st.subheader("出席記錄")
        if attendance:
            df['出席'] = df['出席'].map({1: '✅', 0: '❌'})
            st.dataframe(df, hide_index=True)
        else:
            st.info("暫無出席記錄")


# Initialize database and fetch external events
db.init_db()
external_events = db.fetch_external_events()
for event in external_events:
    db.save_external_event(event)

# Data management in sidebar
st.sidebar.header("數據管理")
if st.sidebar.button("刷新外部活動數據"):
    external_events = db.fetch_external_events()
    for event in external_events:
        db.save_external_event(event)
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
    st.Page(students_page, title="Students"),
    st.Page(event_details_page, title="Event Details"),
    st.Page(student_details_page, title="Student Details")
])
pg.run()