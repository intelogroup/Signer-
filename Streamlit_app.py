import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Document Signer",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'documents' not in st.session_state:
    st.session_state['documents'] = []
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'doc_id_counter' not in st.session_state:
    st.session_state['doc_id_counter'] = 1

# Authentication function
def login_user(username, password):
    return username == "admin" and password == "admin123"

# Main layout
if not st.session_state['logged_in']:
    st.title("Welcome to Document Signer 📝")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if login_user(username, password):
                st.session_state['logged_in'] = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials!")

else:
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("📤 Upload Documents"):
            st.session_state['page'] = 'upload'
        if st.button("📋 Document Status"):
            st.session_state['page'] = 'status'
        if st.button("📊 Analytics"):
            st.session_state['page'] = 'analytics'
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # Main content
    if 'page' not in st.session_state:
        st.session_state['page'] = 'upload'

    if st.session_state['page'] == 'upload':
        st.header("Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'png', 'jpg', 'docx'],
            accept_multiple_files=True
        )

        if uploaded_files:
            for file in uploaded_files:
                doc_id = f"DOC{st.session_state['doc_id_counter']:03d}"
                st.session_state['doc_id_counter'] += 1
                
                st.session_state['documents'].append({
                    'id': doc_id,
                    'name': file.name,
                    'status': 'Pending',
                    'upload_time': datetime.now(),
                    'file_type': file.type,
                })
            
            st.success(f"Successfully uploaded {len(uploaded_files)} document(s)")

    elif st.session_state['page'] == 'status':
        st.header("Document Status")
        
        pending_docs = [doc for doc in st.session_state['documents'] if doc['status'] == 'Pending']
        
        if not pending_docs:
            st.info("No pending documents")
        else:
            for doc in pending_docs:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"📄 {doc['name']} ({doc['id']})")
                
                with col2:
                    if st.button("✅ Accept", key=f"accept_{doc['id']}"):
                        doc['status'] = 'Accepted'
                        st.session_state['history'].append({
                            'id': doc['id'],
                            'name': doc['name'],
                            'action': 'Accepted',
                            'time': datetime.now()
                        })
                        st.rerun()
                
                with col3:
                    if st.button("❌ Reject", key=f"reject_{doc['id']}"):
                        doc['status'] = 'Rejected'
                        st.session_state['history'].append({
                            'id': doc['id'],
                            'name': doc['name'],
                            'action': 'Rejected',
                            'time': datetime.now()
                        })
                        st.rerun()

    elif st.session_state['page'] == 'analytics':
        st.header("Analytics Dashboard")
        
        if st.session_state['history']:
            # Create DataFrame for analysis
            df = pd.DataFrame(st.session_state['history'])
            
            # Show summary metrics
            col1, col2 = st.columns(2)
            with col1:
                accepted = len(df[df['action'] == 'Accepted'])
                st.metric("Documents Accepted", accepted)
            with col2:
                rejected = len(df[df['action'] == 'Rejected'])
                st.metric("Documents Rejected", rejected)
            
            # Show history table
            st.subheader("Recent Activity")
            st.dataframe(
                df[['id', 'name', 'action', 'time']].sort_values('time', ascending=False),
                hide_index=True
            )
        else:
            st.info("No activity recorded yet")
