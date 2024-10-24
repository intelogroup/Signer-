import streamlit as st
import os
import pandas as pd
import subprocess
from datetime import datetime
from PIL import Image

# Initialize user login state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'documents' not in st.session_state:
    st.session_state['documents'] = []

# Authentication function
def login_user(email, password):
    users = {"admin@example.com": "admin123", "assistant@example.com": "assist456"}
    if email in users and users[email] == password:
        return True
    return False

# Logout function
def logout():
    st.session_state['logged_in'] = False

# Style
st.markdown(
    """
    <style>
    body {
        background-color: #f0f0f0;
    }
    .stApp {
        background-color: #1f1f1f;
    }
    .persona {
        color: #ffffff;
        font-size: 20px;
        padding: 10px;
    }
    .hero {
        font-size: 30px;
        font-weight: bold;
        color: #29a745;
    }
    .hero-sub {
        font-size: 18px;
        color: #f1f1f1;
    }
    .btn-style {
        background-color: #e67e22;
        color: white;
        border-radius: 8px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #28a745;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
    }
    .profile-dropdown {
        background-color: #1f1f1f;
        border: 1px solid #e67e22;
        padding: 10px;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True
)

# Sidebar Persona Icon for Profile and Logout
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/50/ffffff/user-male-circle.png", width=80)
    if st.button("My Profile"):
        st.info("My Profile page is under development.")
    if st.button("Contact Developer"):
        st.info("Contact Developer: Email example@example.com.")
    if st.button("About Us"):
        st.info("We provide solutions for managers on the go.")
    if st.button("Logout"):
        logout()
        st.success("Logged out successfully!")
        st.stop()

# Login Form
if not st.session_state['logged_in']:
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            st.session_state['logged_in'] = True
            st.success("Login successful!")
        else:
            st.error("Invalid email or password")
else:
    # Hero Section
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://img.icons8.com/external-flat-juicy-fish/64/ffffff/external-stamp-marketing-flat-flat-juicy-fish.png", width=100)
    with col2:
        st.markdown("<div class='hero'>Signer</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-sub'>A solution for traveling managers</div>", unsafe_allow_html=True)

    # File Upload Section
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'pdf', 'docx'])

    if uploaded_file is not None:
        # Save file and generate unique document ID
        file_path = f"./uploads/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        doc_id = f"signer{len(st.session_state['documents']) + 1:03}"
        date_time = datetime.now().strftime("%Y%m%d%H%M%S")
        st.success(f"Document '{uploaded_file.name}' uploaded successfully!")

        # Add document details to session state
        st.session_state['documents'].append({
            'Document Name': uploaded_file.name,
            'ID': doc_id,
            'Status': 'Pending',
            'Date': date_time
        })

        # Show Document Table
        if st.session_state['documents']:
            st.header("Document Status")
            df = pd.DataFrame(st.session_state['documents'])
            st.dataframe(df)

        # Approve and Update Status
        if st.button("Approve and Apply Stamp"):
            for doc in st.session_state['documents']:
                if doc['Document Name'] == uploaded_file.name:
                    doc['Status'] = "Authorized"
                    st.success(f"Document '{uploaded_file.name}' has been authorized.")
    
    else:
        st.info("Upload a document to start the review process.")
