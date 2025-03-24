import streamlit as st
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta
import time
import database as db

# Initialize session state for authentication
def init_auth_session_state():
    """Initialize authentication related session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None

def check_password():
    """Returns True if the user entered the correct password."""
    # Initialize session state
    init_auth_session_state()
        
    if st.session_state.authenticated:
        # Check if the session has expired (optional - 12 hour timeout)
        if st.session_state.login_time:
            if time.time() - st.session_state.login_time > 12 * 3600:  # 12 hours
                st.session_state.authenticated = False
                st.warning("Your session has expired. Please login again.")
                return False
        return True
    
    # Make sure the database is initialized
    db.init_db()
    
    # Create a default admin user if no users exist
    # Check if we have at least one user in the database
    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    
    if user_count == 0:
        # Create default admin user
        admin_id = str(uuid.uuid4())
        admin_password = "admin123"  # Change this in production!
        admin_pass_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        
        db.save_user(
            user_id=admin_id,
            username="admin",
            name="Administrator",
            email="admin@example.com",
            password_hash=admin_pass_hash
        )
        st.success("Default admin user created. Username: admin, Password: admin123")
        st.warning("Please change the default password after logging in!")
    
    # Login form
    st.header("Login to EchoScript AI")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password")
            return False
        
        # Get user from database
        user = db.get_user_by_username(username)
        
        if user and user['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_id = user['id']
            st.session_state.name = user['name']
            st.session_state.login_time = time.time()
            st.success(f"Welcome, {user['name']}!")
            time.sleep(1)  # Give time for the success message to be seen
            st.experimental_rerun()
            return True
        else:
            st.error("Invalid username or password")
            return False
    
    return False

def create_account():
    """Creates a new user account."""
    st.header("Create an Account")
    
    new_name = st.text_input("Full Name")
    new_email = st.text_input("Email Address")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Create Account"):
        if not new_name or not new_username or not new_password or not new_email:
            st.error("All fields are required")
            return
            
        if new_password != confirm_password:
            st.error("Passwords do not match")
            return
        
        # Check if username exists
        existing_user = db.get_user_by_username(new_username)
        if existing_user:
            st.error("Username already exists")
            return
        
        # Create the new user
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        if db.save_user(
            user_id=user_id,
            username=new_username,
            name=new_name,
            email=new_email,
            password_hash=password_hash
        ):
            st.success("Account created! You can now log in.")
            time.sleep(1)  # Give time for success message
            st.experimental_rerun()
        else:
            st.error("There was a problem creating your account. Please try a different username.")

def logout():
    """Logs out the current user"""
    if st.session_state.authenticated:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.name = None
        st.session_state.login_time = None
        st.success("You have been logged out.")
        time.sleep(1)  # Give time for the success message to be seen
        st.experimental_rerun()

def get_current_user():
    """Returns the current user's information"""
    if st.session_state.authenticated and st.session_state.username:
        return db.get_user_by_username(st.session_state.username)
    return None 