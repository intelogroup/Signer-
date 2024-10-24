import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# Initialize session state
for key in ['logged_in', 'documents', 'history', 'doc_id_counter', 'document_removal_times', 'api_key', 'processed_docs']:
    if key not in st.session_state:
        st.session_state[key] = {
            'logged_in': False,
            'documents': [],
            'history': [],
            'doc_id_counter': 1,
            'document_removal_times': {},
            'api_key': None,
            'processed_docs': set()
        }[key]

# Status emojis
STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌'
}

# Analyze document function with API call
def analyze_with_claude(filename, file_type):
    if not st.session_state['api_key']:
        st.error("Please enter your Claude API key first")
        return None

    headers = {
        "x-api-key": st.session_state['api_key'],
        "content-type": "application/json",
    }
    data = {
        "model": "claude-3-opus-20240229",
        "messages": [{"role": "user", "content": f"Document {filename}, type {file_type}. Check for 'Kalinov Jim Rozensky DAMEUS' and provide processing recommendations."}]
    }

    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('content', [{}])[0].get('text', None)
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")

# Login function
def login_user(email, password):
    return email == "admin" and password == "admin123"

# Auto-remove expired documents from pending list
def check_expired_items():
    current_time = datetime.now()
    expired_docs = [doc_id for doc_id, exp_time in st.session_state['document_removal_times'].items() if current_time > exp_time]
    for doc_id in expired_docs:
        st.session_state['documents'] = [doc for doc in st.session_state['documents'] if doc['id'] != doc_id]
        del st.session_state['document_removal_times'][doc_id]

# Main logic for logged in user
if not st.session_state['logged_in']:
    st.title("Document Signer 📝")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login") and login_user(email, password):
        st.session_state['logged_in'] = True
        st.success("Login successful!")
        st.rerun()
else:
    check_expired_items()
    
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Enter Claude API Key", type="password")
    if st.sidebar.button("Save API Key"):
        st.session_state['api_key'] = api_key
        st.sidebar.success("API Key saved!")
        
    col1, col2 = st.columns([0.9, 0.1])
    with col2:
        with st.expander("👤"):
            if st.button("Logout"):
                st.session_state['logged_in'] = False
                st.rerun()

    st.title("Document Signer ✒️")
    uploaded_files = st.file_uploader("Upload Documents", type=['pdf', 'docx', 'png', 'jpg'], accept_multiple_files=True)

    if uploaded_files and st.session_state['api_key']:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state['processed_docs']:
                doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
                st.session_state['doc_id_counter'] += 1
                upload_time = datetime.now()
                
                analysis = analyze_with_claude(uploaded_file.name, uploaded_file.type)
                if analysis:
                    st.session_state['documents'].append({'id': doc_id, 'name': uploaded_file.name, 'status': 'Pending', 'upload_time': upload_time, 'analysis': analysis})
                    st.session_state['history'].append({'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"), 'id': doc_id, 'name': uploaded_file.name, 'status': f"Pending {STATUS_EMOJIS['Pending']}", 'analysis': analysis})
                    st.session_state['processed_docs'].add(uploaded_file.name)
                    st.success(f"{uploaded_file.name} uploaded successfully!")
    elif uploaded_files and not st.session_state['api_key']:
        st.warning("Please configure your API key first!")

    st.header("Document Status")
    pending_docs = [doc for doc in st.session_state['documents'] if doc['status'] == 'Pending']
    
    if pending_docs:
        for doc in pending_docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {doc['name']} | Status: {doc['status']} {STATUS_EMOJIS[doc['status']]}")
                with st.expander("Show Analysis"):
                    st.write(doc['analysis'])
            with col2:
                if st.button(f"Accept {doc['id']}", key=f"accept_{doc['id']}"):
                    doc['status'] = "Authorized"
                    st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=5)
                    st.rerun()
            with col3:
                if st.button(f"Reject {doc['id']}", key=f"reject_{doc['id']}"):
                    doc['status'] = "Rejected"
                    st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=5)
                    st.rerun()
    else:
        st.info("No pending documents")

    st.header("History of Signing")
    if st.session_state['history']:
        history_df = pd.DataFrame(st.session_state['history'])
        st.dataframe(history_df.sort_values('date', ascending=False), hide_index=True)
