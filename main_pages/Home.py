import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date, timedelta
import random
from utils.session_state import get_session_state, set_session_state

def show():
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🏠 Home")
        st.caption(f"Welcome back! Today is {datetime.now().strftime('%A, %B %d, %Y')}")
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Team", "📅 Calendar", "🔧 Tools"])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_team_info()
    
    with tab3:
        show_calendar()
    
    with tab4:
        show_tools()

def show_overview():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Employees", "42", "+3")
    
    with col2:
        st.metric("Present Today", "38", "94%")
    
    with col3:
        st.metric("On Leave", "4", "-2")
    
    with col4:
        st.metric("Projects", "15", "+1")

    st.subheader("📈 Recent Activity")

    activities = [
        {"time": "2 min ago", "action": "John Doe completed Project Alpha", "type": "success"},
        {"time": "15 min ago", "action": "Sarah Chen requested leave", "type": "warning"},
        {"time": "1 hour ago", "action": "New team member joined - Mike Zhang", "type": "info"},
        {"time": "3 hours ago", "action": "Monthly report generated", "type": "info"},
        {"time": "Yesterday", "action": "System maintenance completed", "type": "success"}
    ]
    
    for activity in activities:
        with st.container(border=True):
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.caption(activity["time"])
            with col_b:
                st.write(activity["action"])

def show_team_info():
    employees = [
        {"id": 1, "name": "John Doe", "position": "Software Engineer", "department": "IT", "email": "john@company.com", "status": "🟢 Online", "projects": 3},
        {"id": 2, "name": "Sarah Chen", "position": "Data Analyst", "department": "Analytics", "email": "sarah@company.com", "status": "🟡 Away", "projects": 2},
        {"id": 3, "name": "Mike Zhang", "position": "Product Manager", "department": "Product", "email": "mike@company.com", "status": "🟢 Online", "projects": 4},
        {"id": 4, "name": "Lisa Wang", "position": "UX Designer", "department": "Design", "email": "lisa@company.com", "status": "🔴 Offline", "projects": 2},
        {"id": 5, "name": "David Kim", "position": "QA Engineer", "department": "IT", "email": "david@company.com", "status": "🟢 Online", "projects": 3},
        {"id": 6, "name": "Emma Liu", "position": "Marketing Specialist", "department": "Marketing", "email": "emma@company.com", "status": "🟡 Away", "projects": 1}
    ]
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search employees", placeholder="Name, department, position...")
    
    with col2:
        department_filter = st.selectbox("Department", ["All", "IT", "Analytics", "Product", "Design", "Marketing"])
    filtered_employees = employees
    if search_term:
        filtered_employees = [e for e in employees if search_term.lower() in e["name"].lower() or 
                            search_term.lower() in e["department"].lower() or 
                            search_term.lower() in e["position"].lower()]
    
    if department_filter != "All":
        filtered_employees = [e for e in filtered_employees if e["department"] == department_filter]
    st.subheader(f"👥 Team Members ({len(filtered_employees)})")
    
    cols = st.columns(2)
    for i, employee in enumerate(filtered_employees):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{employee['name']}**")
                st.caption(f"{employee['position']} | {employee['department']}")
                st.write(f"📧 {employee['email']}")
                st.write(f"📊 Projects: {employee['projects']}")
                st.write(employee['status'])
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📞 Contact", key=f"contact_{employee['id']}", use_container_width=True):
                        st.toast(f"Contacting {employee['name']}...")
                with col_btn2:
                    if st.button("📋 Profile", key=f"profile_{employee['id']}", use_container_width=True):
                        st.session_state['selected_employee'] = employee
                        st.rerun()

def show_calendar():
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous"):
            st.session_state['calendar_month'] = (current_month - 2) % 12 + 1
            if current_month == 1:
                st.session_state['calendar_year'] = current_year - 1
            st.rerun()
    
    with col2:
        st.subheader(f"📅 {calendar.month_name[current_month]} {current_year}")
    
    with col3:
        if st.button("Next ➡️"):
            st.session_state['calendar_month'] = current_month % 12 + 1
            if current_month == 12:
                st.session_state['calendar_year'] = current_year + 1
            st.rerun()
    cal = calendar.monthcalendar(current_year, current_month)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    
    for i, day in enumerate(days):
        cols[i].write(f"**{day}**")
    events = {
        5: ["Team Meeting", "Project Review"],
        12: ["Deadline", "Client Call"],
        18: ["Training", "Lunch & Learn"],
        25: ["Holiday", "Company Event"]
    }
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                with cols[i]:
                    if day == today.day:
                        st.markdown(f"<div style='background-color: #e6f7ff; padding: 5px; border-radius: 5px;'><b>{day}</b></div>", unsafe_allow_html=True)
                    else:
                        st.write(f"**{day}**")
                    if day in events:
                        for event in events[day]:
                            st.caption(f"• {event}")

def show_tools():
    st.subheader("🛠️ Useful Tools")
    with st.expander("📝 Quick Notes", expanded=True):
        notes = st.text_area("Take quick notes", height=100, 
                           placeholder="Write your notes here...",
                           help="Your notes will be saved during this session")
        if st.button("💾 Save Notes"):
            set_session_state("quick_notes", notes)
            st.success("Notes saved!")

    with st.expander("🧮 Quick Calculator", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            num1 = st.number_input("Number 1", value=0.0)
        with col2:
            operation = st.selectbox("Operation", ["+", "-", "×", "÷"])
        with col3:
            num2 = st.number_input("Number 2", value=0.0)
        
        if st.button("Calculate"):
            if operation == "+":
                result = num1 + num2
            elif operation == "-":
                result = num1 - num2
            elif operation == "×":
                result = num1 * num2
            elif operation == "÷":
                result = num1 / num2 if num2 != 0 else "Error"
            
            st.metric("Result", result)

    with st.expander("📏 Unit Converter", expanded=True):
        conv_col1, conv_col2 = st.columns(2)
        
        with conv_col1:
            value = st.number_input("Value", value=1.0)
            from_unit = st.selectbox("From", ["Meters", "Feet", "Kilograms", "Pounds"])
        
        with conv_col2:
            to_unit = st.selectbox("To", ["Feet", "Meters", "Pounds", "Kilograms"])
            
            if st.button("Convert"):
                conversions = {
                    ("Meters", "Feet"): value * 3.28084,
                    ("Feet", "Meters"): value * 0.3048,
                    ("Kilograms", "Pounds"): value * 2.20462,
                    ("Pounds", "Kilograms"): value * 0.453592
                }
                
                result = conversions.get((from_unit, to_unit), value)
                st.metric("Converted Value", f"{result:.2f} {to_unit}")
