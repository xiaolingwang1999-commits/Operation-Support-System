  
import hmac  
import streamlit as st  
def check_password(): 
    def login_form(): 
        with st.form("Credentials"):  
            col0,col1, col2 = st.columns([0.2,0.6, 2.3],vertical_alignment="top")  
            with col0:  
                st.write("  ")  
            with col1:  
                st.image("./utils/logo.jpg",  width=90)  
            with col2:  
                st.markdown("## Operation Support System")  
            st.text_input("User Name", key="username")  
            st.text_input("Password", type="password", key="password")    
            cols = st.columns([1, 2, 1])
            with cols[1]:
                st.form_submit_button("Login", 
                        on_click=password_entered,
                        use_container_width=True)  
           
    def password_entered():  
        """Checks whether a password entered by the user is correct."""  
        if st.session_state["username"] in st.secrets[  
            "passwords"  
        ] and hmac.compare_digest(  
            st.session_state["password"],  
            st.secrets.passwords[st.session_state["username"]],  
        ):  
            st.session_state["password_correct"] = True
            if st.session_state["username"] == "admin":
                st.session_state["user_role"] = "admin"
            else:
                st.session_state["user_role"] = "user" 
            del st.session_state["password"]  
            del st.session_state["username"]  
        else:  
            st.session_state["password_correct"] = False  
    if st.session_state.get("password_correct", False):  
        return True   
    login_form()  
    if "password_correct" in st.session_state:  
        st.error("😕 Uncorrect Username or Password")  
    return False
def is_admin():
    return st.session_state.get("user_role") 
if not check_password():  
    st.stop()