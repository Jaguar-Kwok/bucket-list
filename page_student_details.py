import streamlit as st
import sqlite3
import pandas as pd
import function_db as db

DB_NAME = "community_center.db"

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