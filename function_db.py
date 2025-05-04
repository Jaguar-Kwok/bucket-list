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
