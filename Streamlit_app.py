import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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
    st.session_state['action_times'] = []  # To store (upload_time, action_time) pairs

def login_user(email, password):
    return email == "admin" and password == "admin123"

def check_expired_documents():
    current_time = datetime.now()
    for doc_id, expiration_time in list(st.session_state['document_removal_times'].items()):
        if current_time > expiration_time:
            # Remove document from display list
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
    # Check and remove expired documents
    check_expired_documents()

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
                st.rerun()

    # Main content
    st.title("Document Signer ✒️")
    
    # File Upload Section
    st.header("Upload Document(s)")
    uploaded_files = st.file_uploader("Choose files", type=['pdf', 'docx', 'png', 'jpg'], 
                                    accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
            st.session_state['doc_id_counter'] += 1
            upload_time = datetime.now()
            
            st.session_state['documents'].append({
                'id': doc_id,
                'name': uploaded_file.name,
                'status': 'Pending',
                'upload_time': upload_time
            })
        st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")

    # Document Status Section
    st.header("Document Status")
    pending_docs = [doc for doc in st.session_state['documents'] if doc['status'] == 'Pending']
    
    if pending_docs:
        for doc in pending_docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {doc['name']} | Status: {doc['status']}")
            with col2:
                if st.button(f"Accept", key=f"accept_{doc['id']}"):
                    doc['status'] = "Authorized"
                    action_time = datetime.now()
                    st.session_state['history'].append({
                        'date': action_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'id': doc['id'],
                        'name': doc['name'],
                        'status': 'Authorized'
                    })
                    # Store action time for analytics
                    st.session_state['action_times'].append(
                        (doc['upload_time'], action_time)
                    )
                    # Set document to expire in 1 minute
                    st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=1)
                    st.rerun()
            with col3:
                if st.button(f"Reject", key=f"reject_{doc['id']}"):
                    doc['status'] = "Rejected"
                    action_time = datetime.now()
                    st.session_state['history'].append({
                        'date': action_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'id': doc['id'],
                        'name': doc['name'],
                        'status': 'Rejected'
                    })
                    # Store action time for analytics
                    st.session_state['action_times'].append(
                        (doc['upload_time'], action_time)
                    )
                    # Set document to expire in 1 minute
                    st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=1)
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
        # Analytics 1: Document Status Distribution
        df_history = pd.DataFrame(st.session_state['history'])
        col1, col2 = st.columns(2)
        with col1:
            authorized_count = len(df_history[df_history['status'] == 'Authorized'])
            st.metric("Documents Authorized", authorized_count)
        with col2:
            rejected_count = len(df_history[df_history['status'] == 'Rejected'])
            st.metric("Documents Rejected", rejected_count)

        # Analytics 2: Average Time to Sign
        if st.session_state['action_times']:
            time_diffs = [(action - upload).total_seconds() 
                         for upload, action in st.session_state['action_times']]
            avg_time = sum(time_diffs) / len(time_diffs)
            st.metric("Average Time to Sign", f"{avg_time:.1f} seconds")

        # Analytics 3: Total Documents Summary
        total_docs = len(st.session_state['history'])
        st.metric("Total Documents Processed", total_docs)
