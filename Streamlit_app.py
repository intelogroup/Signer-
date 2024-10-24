import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'documents' not in st.session_state:
    st.session_state['documents'] = []
if 'doc_id_counter' not in st.session_state:
    st.session_state['doc_id_counter'] = 1
if 'document_removal_times' not in st.session_state:
    st.session_state['document_removal_times'] = {}
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None

STATUS_EMOJIS = {'Pending': '⏳', 'Authorized': '✅', 'Rejected': '❌'}

def analyze_with_claude(filename):
    try:
        if not st.session_state['api_key']:
            st.error("Enter your Claude API key first")
            return None

        headers = {
            "x-api-key": st.session_state['api_key'],
            "content-type": "application/json",
        }
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": f"Analyze document {filename}. Focus on key names like Kalinov Jim Rozensky DAMEUS. Limit response to 200 tokens."}
            ],
            "max_tokens_to_sample": 200  # Limit to 200 tokens
        }
        
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['completion']
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None

def login_user(email, password):
    return email == "admin" and password == "admin123"

def check_expired_items():
    current_time = datetime.now()
    for doc_id, expiration_time in list(st.session_state['document_removal_times'].items()):
        if current_time > expiration_time:
            st.session_state['documents'] = [doc for doc in st.session_state['documents'] if doc['id'] != doc_id]
            del st.session_state['document_removal_times'][doc_id]

# Authentication
if not st.session_state['logged_in']:
    st.title("Document Signer 📝")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            st.session_state['logged_in'] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password")
else:
    # API Key
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Enter Claude API Key", type="password")
    if st.sidebar.button("Save API Key"):
        st.session_state['api_key'] = api_key
        st.sidebar.success("API Key saved!")

    # Document Upload and Analysis
    st.title("Document Signer ✒️")
    uploaded_files = st.file_uploader("Upload Document(s)", type=['pdf', 'docx'], accept_multiple_files=True)
    
    if uploaded_files and st.session_state['api_key']:
        for uploaded_file in uploaded_files:
            doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
            st.session_state['doc_id_counter'] += 1
            upload_time = datetime.now()

            # Claude Analysis
            analysis = analyze_with_claude(uploaded_file.name)
            if analysis:
                st.session_state['documents'].append({'id': doc_id, 'name': uploaded_file.name, 'status': 'Pending', 'analysis': analysis})
                st.session_state['document_removal_times'][doc_id] = upload_time + timedelta(minutes=5)
                with st.expander(f"Analysis for {uploaded_file.name}"):
                    st.write(analysis)

    # Display Documents
    st.header("Document Status")
    for doc in st.session_state['documents']:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{doc['name']} | {doc['status']} {STATUS_EMOJIS[doc['status']]}")
        with col2:
            if st.button(f"Authorize {doc['id']}", key=f"auth_{doc['id']}"):
                doc['status'] = 'Authorized'
                st.rerun()
