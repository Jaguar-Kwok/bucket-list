import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime
import function_db as db

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
                  address TEXT,
                  english_name TEXT,  
                  region TEXT, 
                  school TEXT, 
                  remarks TEXT,
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
                      name=?, contact=?, address=?, english_name=?, region=?, school=?, remarks=?
                      WHERE id=?''',
                   (student['name'], student['contact'], student['address'], student['english_name'],
                    student['region'], student['school'], student['remarks'], student['id']))
    else:
        conn.execute('''INSERT INTO students 
                      (name, contact, address, english_name, region, school, remarks, registered_at)
                      VALUES (?,?,?,?,?,?,?,?)''',
                   (student['name'], student['contact'], student['address'], student['english_name'],
                    student['region'], student['school'], student['remarks'], datetime.now()))
    conn.commit()
    conn.close()


def get_current_registrations(event_id):
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute('''SELECT student_id FROM attendance WHERE event_id = ?''', (event_id,)).fetchall()
    conn.close()
    return [r[0] for r in result]


def save_registration_changes(event_id, selected_ids):
    conn = sqlite3.connect(DB_NAME)
    try:
        # Remove unselected students
        if selected_ids:
            conn.execute('''DELETE FROM attendance WHERE event_id = ? AND student_id NOT IN ({})'''.format(','.join(['?']*len(selected_ids))), [event_id] + selected_ids)
        else:
            conn.execute('''DELETE FROM attendance WHERE event_id = ?''', (event_id,))
        
        # Add new registrations
        for student_id in selected_ids:
            conn.execute('''INSERT OR IGNORE INTO attendance (event_id, student_id, attended, updated_at) VALUES (?,?,?,?)''', (event_id, student_id, False, datetime.now()))
        conn.commit()
    finally:
        conn.close()


def get_attendance_records(event_id):
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql('''SELECT students.id as student_id, students.name, attendance.attended FROM attendance JOIN students ON attendance.student_id = students.id WHERE event_id = ?''', conn, params=(event_id,))
    finally:
        conn.close()
    return df


def update_attendance_records(edited_attendance, event_id):
    conn = sqlite3.connect(DB_NAME)
    try:
        for _, row in edited_attendance.iterrows():
            conn.execute('''UPDATE attendance SET attended = ?, updated_at = ? WHERE event_id = ? AND student_id = ?''', (row['attended'], datetime.now(), event_id, row['student_id']))
        conn.commit()
    finally:
        conn.close()
