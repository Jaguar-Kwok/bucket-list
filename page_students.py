import streamlit as st
import function_db as db

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