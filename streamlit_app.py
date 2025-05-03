import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# Database setup
DB_NAME = "community_center.db"
API_URL = "https://activity.striveandrise.gov.hk/api/activities?targetGroups=SKHWC"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  external_id TEXT UNIQUE,
                  name_tc TEXT,
                  name_en TEXT,
                  description_tc TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  location_address_tc TEXT,
                  location_lat REAL,
                  location_lng REAL,
                  quota INTEGER,
                  organizer_tc TEXT,
                  activity_nature_tc TEXT,
                  sessions TEXT,
                  thumbnail_url TEXT,
                  created_at TIMESTAMP)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  contact TEXT,
                  registered_at TIMESTAMP)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (event_id INTEGER,
                  student_id INTEGER,
                  attended BOOLEAN,
                  updated_at TIMESTAMP,
                  PRIMARY KEY (event_id, student_id))''')
    conn.commit()
    conn.close()

def fetch_external_events():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()['results']
    except Exception as e:
        st.error(f"Error fetching external events: {e}")
        return []

def save_external_event(event):
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute('''INSERT OR IGNORE INTO events 
                      (external_id, name_tc, name_en, description_tc,
                       start_date, end_date, location_address_tc,
                       location_lat, location_lng, quota, organizer_tc,
                       activity_nature_tc, sessions, thumbnail_url, created_at)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (event['subActivityCode'],
                    event['name_tc'],
                    event['name_en'],
                    event['description_tc'],
                    event['sessions'][0]['startDate'] if event['sessions'] else None,
                    event['sessions'][0]['endDate'] if event['sessions'] else None,
                    event['locationAddress_tc'],
                    event['locationLatLng']['lat'] if event['locationLatLng'] else None,
                    event['locationLatLng']['lng'] if event['locationLatLng'] else None,
                    event['quota'],
                    event['supportingOrganiserName_tc'],
                    event['activityNature']['name_tc'],
                    str(event['sessions']),
                    event['thumbnailUrl_tc'],
                    datetime.now()))
        conn.commit()
    finally:
        conn.close()

# Database operations
def get_events():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM events", conn)
    conn.close()
    return df.to_dict('records')

def get_students():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM students", conn)
    conn.close()
    return df.to_dict('records')

def save_event(event):
    conn = sqlite3.connect(DB_NAME)
    if 'id' in event:
        conn.execute('''UPDATE events SET 
                      name_tc=?, name_en=?, description_tc=?, start_date=?, 
                      end_date=?, location_address_tc=?, location_lat=?, 
                      location_lng=?, quota=?, organizer_tc=?, 
                      activity_nature_tc=?, sessions=?, thumbnail_url=?
                      WHERE id=?''',
                   (event['name_tc'], event['name_en'], event['description_tc'],
                    event['start_date'], event['end_date'], event['location_address_tc'],
                    event['location_lat'], event['location_lng'], event['quota'],
                    event['organizer_tc'], event['activity_nature_tc'],
                    event['sessions'], event['thumbnail_url'], event['id']))
    else:
        conn.execute('''INSERT INTO events 
                      (name_tc, name_en, description_tc, start_date, end_date,
                       location_address_tc, location_lat, location_lng, quota,
                       organizer_tc, activity_nature_tc, sessions, thumbnail_url, created_at)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (event['name_tc'], event['name_en'], event['description_tc'],
                    event['start_date'], event['end_date'], event['location_address_tc'],
                    event['location_lat'], event['location_lng'], event['quota'],
                    event['organizer_tc'], event['activity_nature_tc'],
                    event['sessions'], event['thumbnail_url'], datetime.now()))
    conn.commit()
    conn.close()

def save_student(student):
    conn = sqlite3.connect(DB_NAME)
    if 'id' in student:
        conn.execute('''UPDATE students SET 
                      name=?, contact=?
                      WHERE id=?''',
                   (student['name'], student['contact'], student['id']))
    else:
        conn.execute('''INSERT INTO students 
                      (name, contact, registered_at)
                      VALUES (?,?,?)''',
                   (student['name'], student['contact'], datetime.now()))
    conn.commit()
    conn.close()

# Initialize database and fetch external events
init_db()
external_events = fetch_external_events()
for event in external_events:
    save_external_event(event)

# Session state setup
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'selected_student' not in st.session_state:
    st.session_state.selected_student = None
if 'selected_event' not in st.session_state:
    st.session_state.selected_event = None

# Page configurations
def home_page():
    st.title("社區中心管理系統")
    st.write("歡迎使用社區中心管理系統")

def events_page():
    st.title("活動管理")
    
    # Event creation form
    with st.expander("新增活動", expanded=False):
        with st.form("event_form"):
            name_tc = st.text_input("活動名稱（中文）")
            name_en = st.text_input("活動名稱（英文）")
            description_tc = st.text_area("活動描述（中文）")
            start_date = st.date_input("開始日期")
            end_date = st.date_input("結束日期")
            location = st.text_input("活動地點")
            quota = st.number_input("名額", min_value=1)
            submitted = st.form_submit_button("保存活動")
            
            if submitted:
                new_event = {
                    'name_tc': name_tc,
                    'name_en': name_en,
                    'description_tc': description_tc,
                    'start_date': start_date,
                    'end_date': end_date,
                    'location_address_tc': location,
                    'quota': quota,
                    'organizer_tc': '',
                    'activity_nature_tc': '',
                    'sessions': '[]',
                    'thumbnail_url': ''
                }
                save_event(new_event)
                st.rerun()

    # Events list
    st.subheader("所有活動")
    events = get_events()
    if events:
        cols = st.columns(3)
        for idx, event in enumerate(events):
            with cols[idx % 3]:
                if st.button(f"📅 {event['name_tc']}", key=f"event_{event['id']}"):
                    st.session_state.selected_event = event['id']
                    st.session_state.page = 'Event Details'
                if event['thumbnail_url']:
                    st.image(event['thumbnail_url'], use_container_width=True)
                st.caption(f"開始日期: {event['start_date']}")
    else:
        st.info("暫無活動資料")

def students_page():
    st.title("學生管理")
    
    # Student creation form
    with st.expander("新增學生", expanded=False):
        with st.form("student_form"):
            name = st.text_input("學生姓名")
            contact = st.text_input("聯絡方式")
            submitted = st.form_submit_button("保存學生")
            
            if submitted:
                save_student({'name': name, 'contact': contact})
                st.rerun()

    # Students list
    st.subheader("所有學生")
    students = get_students()
    if students:
        cols = st.columns(3)
        for idx, student in enumerate(students):
            with cols[idx % 3]:
                if st.button(f"👤 {student['name']}", key=f"student_{student['id']}"):
                    st.session_state.selected_student = student['id']
                    st.session_state.page = 'Student Details'
                st.caption(f"聯絡: {student['contact']}")
    else:
        st.info("暫無學生資料")

def event_details_page():
    st.title("活動詳情")
    
    # All events list
    st.subheader("選擇活動")
    events = get_events()
    cols = st.columns(3)
    for idx, event in enumerate(events):
        with cols[idx % 3]:
            if st.button(f"📅 {event['name_tc']}", key=f"all_event_{event['id']}"):
                st.session_state.selected_event = event['id']
    
    # Selected event details
    if st.session_state.selected_event:
        conn = sqlite3.connect(DB_NAME)
        event = conn.execute('''SELECT * FROM events 
                              WHERE id = ?''', 
                           (st.session_state.selected_event,)).fetchone()
        conn.close()
        
        st.divider()
        st.subheader("活動詳細資料")
        
        col1, col2 = st.columns(2)
        with col1:
            if event['thumbnail_url']:
                st.image(event['thumbnail_url'], use_container_width=True)
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

def student_details_page():
    st.title("學生詳情")
    
    # All students list
    st.subheader("選擇學生")
    students = get_students()
    cols = st.columns(3)
    for idx, student in enumerate(students):
        with cols[idx % 3]:
            if st.button(f"👤 {student['name']}", key=f"all_student_{student['id']}"):
                st.session_state.selected_student = student['id']
    
    # Selected student details
    if st.session_state.selected_student:
        conn = sqlite3.connect(DB_NAME)
        student = conn.execute('''SELECT * FROM students 
                                WHERE id = ?''', 
                             (st.session_state.selected_student,)).fetchone()
        attendance = conn.execute('''SELECT events.name_tc, events.start_date, attendance.attended
                                   FROM attendance
                                   JOIN events ON attendance.event_id = events.id
                                   WHERE student_id = ?''', 
                                (st.session_state.selected_student,)).fetchall()
        conn.close()
        
        st.divider()
        st.subheader("學生詳細資料")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**姓名:** {student['name']}")
            st.write(f"**聯絡方式:** {student['contact']}")
            st.write(f"**註冊時間:** {student['registered_at']}")
        
        with col2:
            st.subheader("出席記錄")
            if attendance:
                df = pd.DataFrame(attendance, columns=['活動名稱', '日期', '出席'])
                df['出席'] = df['出席'].map({1: '✅', 0: '❌'})
                st.dataframe(df, hide_index=True)
            else:
                st.info("暫無出席記錄")

# Main app layout
st.sidebar.title("導航")
page = st.sidebar.radio("前往頁面", [
    'Home', 
    'Events', 
    'Students',
    'Event Details',
    'Student Details'
])

# Page routing
if page == 'Home':
    home_page()
elif page == 'Events':
    events_page()
elif page == 'Students':
    students_page()
elif page == 'Event Details':
    event_details_page()
elif page == 'Student Details':
    student_details_page()

# Data management in sidebar
st.sidebar.header("數據管理")
if st.sidebar.button("刷新外部活動數據"):
    external_events = fetch_external_events()
    for event in external_events:
        save_external_event(event)
    st.sidebar.success("活動數據已更新")

if st.sidebar.button("導出所有數據"):
    with pd.ExcelWriter('community_data.xlsx') as writer:
        pd.read_sql("SELECT * FROM events", sqlite3.connect(DB_NAME)).to_excel(writer, sheet_name='Events', index=False)
        pd.read_sql("SELECT * FROM students", sqlite3.connect(DB_NAME)).to_excel(writer, sheet_name='Students', index=False)
        pd.read_sql("SELECT * FROM attendance", sqlite3.connect(DB_NAME)).to_excel(writer, sheet_name='Attendance', index=False)
    st.sidebar.success("數據導出成功")