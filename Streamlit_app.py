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
    st.session_state['action_times'] = []

# Status emojis
STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌'
}

def login_user(email, password):
    return email == "admin" and password == "admin123"

def check_expired_items():
    current_time = datetime.now()
    
    # Check documents that should be removed after action (5 minutes)
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
    # Check and remove expired items
    check_expired_items()

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
            
            if not any(doc['name'] == uploaded_file.name and doc['status'] == 'Pending' 
                      for doc in st.session_state['documents']):
                # Add to documents list
                st.session_state['documents'].append({
                    'id': doc_id,
                    'name': uploaded_file.name,
                    'status': 'Pending',
                    'upload_time': upload_time
                })
                
                # Add to history with Pending status
                st.session_state['history'].append({
                    'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'id': doc_id,
                    'name': uploaded_file.name,
                    'status': f"Pending {STATUS_EMOJIS['Pending']}"
                })
                
        st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")

    # Document Status Section
    st.header("Document Status")
    pending_docs = [doc for doc in st.session_state['documents'] 
                   if doc['status'] == 'Pending']
    
    if pending_docs:
        for doc in pending_docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {doc['name']} | Status: {doc['status']} {STATUS_EMOJIS[doc['status']]}")
            with col2:
                if st.button(f"Accept", key=f"accept_{doc['id']}"):
                    doc['status'] = "Authorized"
                    action_time = datetime.now()
                    
                    # Update history status
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
                    
                    # Update history status
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

    # Analytics Section with Graphs
    st.header("Analytics and Activity Tracking")
    
    if st.session_state['history']:
        df_history = pd.DataFrame(st.session_state['history'])
        
        # 1. Document Status Distribution
        st.subheader("Document Status Distribution")
        
        # Clean status column by removing emojis for counting
        status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
        
        # Create the chart data
        chart_data = pd.DataFrame({
            'Status': status_counts.index,
            'Count': status_counts.values
        })
        
        # Display color legend
        st.write("Status Colors:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"🟡 Pending {STATUS_EMOJIS['Pending']}")
        with col2:
            st.markdown(f"🟢 Authorized {STATUS_EMOJIS['Authorized']}")
        with col3:
            st.markdown(f"🔴 Rejected {STATUS_EMOJIS['Rejected']}")
            
        st.bar_chart(chart_data.set_index('Status'))
        
        # 2. Time to Sign Analysis
        st.subheader("Signing Time Analysis")
        if st.session_state['action_times']:
            time_diffs = [(action - upload).total_seconds() 
                         for upload, action in st.session_state['action_times']]
            avg_time = sum(time_diffs) / len(time_diffs)
            
            time_data = pd.DataFrame({
                'Document': range(1, len(time_diffs) + 1),
                'Time (seconds)': time_diffs
            })
            st.line_chart(time_data.set_index('Document'))
            st.metric("Average Time to Sign", f"{avg_time:.1f} seconds")

        # 3. Document Volume Metrics
        st.subheader("Document Volume")
        total_docs = len(st.session_state['history'])
        daily_docs = df_history.groupby(df_history['date'].str[:10]).size()
        st.line_chart(daily_docs)
        st.metric("Total Documents Processed", total_docs)
