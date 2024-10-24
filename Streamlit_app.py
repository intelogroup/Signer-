import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'documents' not in st.session_state:
    st.session_state['documents'] = []
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'doc_id_counter' not in st.session_state:
    st.session_state['doc_id_counter'] = 1
if 'document_removal_times' not in st.session_state:
    st.session_state['document_removal_times'] = {}
if 'action_times' not in st.session_state:
    st.session_state['action_times'] = []
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None
if 'processed_docs' not in st.session_state:
    st.session_state['processed_docs'] = set()  # To track processed documents

# Status emojis
STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌'
}

def analyze_with_claude(filename, file_type):
    try:
        if not st.session_state['api_key']:
            st.error("Please enter your Claude API key first")
            return None
            
        headers = {
            "x-api-key": st.session_state['api_key'],
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {
                    "role": "user",
                    "content": f"A document named {filename} of type {file_type} has been uploaded for review. Please provide:\n1. Brief acknowledgment of the document type\n2. Note to check for any mention of Kalinov Jim Rozensky DAMEUS\n3. Standard processing recommendations."
                }
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'content' in result and len(result['content']) > 0:
                return result['content'][0]['text']
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
            st.session_state['documents'] = [doc for doc in st.session_state['documents'] 
                                           if doc['id'] != doc_id]
            del st.session_state['document_removal_times'][doc_id]

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
    check_expired_items()

    # API Key Configuration
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Enter Claude API Key", type="password")
    if st.sidebar.button("Save API Key"):
        st.session_state['api_key'] = api_key
        st.sidebar.success("API Key saved!")

    # Profile dropdown in header
    col1, col2 = st.columns([0.9, 0.1])
    with col2:
        with st.expander("👤"):
            if st.button("My Profile"):
                st.info("Profile settings coming soon")
            if st.button("About Us"):
                st.info("Document Signer App v1.0")
            if st.button("Logout"):
                st.session_state['logged_in'] = False
                st.session_state['api_key'] = None
                st.rerun()

    # Main content
    st.title("Document Signer ✒️")
    
    # File Upload Section
    st.header("Upload Document(s)")
    uploaded_files = st.file_uploader("Choose files", type=['pdf', 'docx', 'png', 'jpg'], 
                                    accept_multiple_files=True)

    if uploaded_files and st.session_state['api_key']:
        for uploaded_file in uploaded_files:
            # Check if document has already been processed
            if uploaded_file.name not in st.session_state['processed_docs']:
                doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
                st.session_state['doc_id_counter'] += 1
                upload_time = datetime.now()
                
                # Get Claude's analysis
                analysis = analyze_with_claude(uploaded_file.name, uploaded_file.type)
                
                if analysis:
                    # Add to documents list
                    st.session_state['documents'].append({
                        'id': doc_id,
                        'name': uploaded_file.name,
                        'status': 'Pending',
                        'upload_time': upload_time,
                        'analysis': analysis
                    })
                    
                    # Add to history with Pending status
                    st.session_state['history'].append({
                        'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'id': doc_id,
                        'name': uploaded_file.name,
                        'status': f"Pending {STATUS_EMOJIS['Pending']}",
                        'analysis': analysis
                    })
                    
                    # Mark document as processed
                    st.session_state['processed_docs'].add(uploaded_file.name)
                    
                    # Show analysis
                    with st.expander(f"Analysis for {uploaded_file.name}"):
                        st.write(analysis)
                
        st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")
    elif uploaded_files and not st.session_state['api_key']:
        st.warning("Please configure your Claude API key in the sidebar first")

    # Document Status Section
    st.header("Document Status")
    pending_docs = [doc for doc in st.session_state['documents'] 
                   if doc['status'] == 'Pending' and 
                   doc['id'] not in st.session_state['document_removal_times']]
    
    if pending_docs:
        for doc in pending_docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {doc['name']} | Status: {doc['status']} {STATUS_EMOJIS[doc['status']]}")
                with st.expander("Show Analysis"):
                    st.write(doc.get('analysis', 'No analysis available'))
            with col2:
                if st.button(f"Accept", key=f"accept_{doc['id']}"):
                    doc['status'] = "Authorized"
                    action_time = datetime.now()
                    
                    for hist_doc in st.session_state['history']:
                        if hist_doc['id'] == doc['id']:
                            hist_doc['status'] = f"Authorized {STATUS_EMOJIS['Authorized']}"
                            hist_doc['date'] = action_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.session_state['action_times'].append((doc['upload_time'], action_time))
                    st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=5)
                    st.rerun()
            with col3:
                if st.button(f"Reject", key=f"reject_{doc['id']}"):
                    doc['status'] = "Rejected"
                    action_time = datetime.now()
                    
                    for hist_doc in st.session_state['history']:
                        if hist_doc['id'] == doc['id']:
                            hist_doc['status'] = f"Rejected {STATUS_EMOJIS['Rejected']}"
                            hist_doc['date'] = action_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.session_state['action_times'].append((doc['upload_time'], action_time))
                    st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=5)
                    st.rerun()
    else:
        st.info("No pending documents")

    # History Section
    st.header("History of Signing")
    if st.session_state['history']:
        history_df = pd.DataFrame(st.session_state['history'])
        st.dataframe(history_df.sort_values('date', ascending=False),
                    hide_index=True)

    # Analytics Section
    st.header("Analytics and Activity Tracking")
    
    if st.session_state['history']:
        df_history = pd.DataFrame(st.session_state['history'])
        
        # Status Distribution
        st.subheader("Document Status Distribution")
        status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
        
        # Display color legend
        st.write("Status Colors:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"🟡 Pending {STATUS_EMOJIS['Pending']}")
        with col2:
            st.markdown(f"🟢 Authorized {STATUS_EMOJIS['Authorized']}")
        with col3:
            st.markdown(f"🔴 Rejected {STATUS_EMOJIS['Rejected']}")
            
        st.bar_chart(status_counts)
        
        # Time Analysis
        if st.session_state['action_times']:
            st.subheader("Processing Time Analysis")
            time_diffs = [(action - upload).total_seconds() 
                         for upload, action in st.session_state['action_times']]
            avg_time = sum(time_diffs) / len(time_diffs)
            
            time_data = pd.DataFrame({
                'Document': range(1, len(time_diffs) + 1),
                'Time (seconds)': time_diffs
            })
            st.line_chart(time_data.set_index('Document'))
            st.metric("Average Time to Sign", f"{avg_time:.1f} seconds")

        # Document Volume
        st.subheader("Total Documents")
        st.metric("Total Documents Processed", len(st.session_state['history']))
