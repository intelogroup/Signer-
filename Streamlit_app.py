import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# Status emojis
STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌'
}

def analyze_with_claude(content):
    try:
        api_key = "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"
        
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {
                    "role": "user",
                    "content": f"Analyze this document and provide:\n1. Brief summary\n2. Names mentioned\n3. Any actions requested specifically for Kalinov Jim Rozensky DAMEUS.\n\nDocument content: {content}"
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
        
        st.error(f"API Error {response.status_code}: {response.text}")
        return None
            
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None

def send_email(document_name, document_type, summary):
    try:
        sender_email = "jimkalinov@gmail.com"
        sender_password = "Jimkali90"
        receiver_email = "jimkalinov@gmail.com"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"{document_name} from Signer - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
This is a summary of the document:

Document Name: {document_name}
Document Type: {document_type}

Summary Analysis:
{summary}

Best regards,
Document Signer App
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

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
    uploaded_files = st.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                # Read file content
                content = uploaded_file.getvalue().decode('utf-8')
                
                # Analyze with Claude
                st.info(f"Analyzing {uploaded_file.name}...")
                analysis = analyze_with_claude(content)
                
                if analysis:
                    st.success("Analysis completed!")
                    with st.expander(f"Show analysis for {uploaded_file.name}"):
                        st.write(analysis)
                    
                    # Process document
                    doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
                    st.session_state['doc_id_counter'] += 1
                    upload_time = datetime.now()
                    
                    # Add to documents list
                    if not any(doc['name'] == uploaded_file.name and doc['status'] == 'Pending' 
                              for doc in st.session_state['documents']):
                        
                        doc_data = {
                            'id': doc_id,
                            'name': uploaded_file.name,
                            'status': 'Pending',
                            'upload_time': upload_time,
                            'analysis': analysis
                        }
                        
                        st.session_state['documents'].append(doc_data)
                        
                        # Add to history
                        st.session_state['history'].append({
                            'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'id': doc_id,
                            'name': uploaded_file.name,
                            'status': f"Pending {STATUS_EMOJIS['Pending']}",
                            'analysis': analysis
                        })
                        
                        # Try to send email
                        try:
                            email_sent = send_email(
                                uploaded_file.name,
                                'text/plain',
                                analysis
                            )
                            if email_sent:
                                st.success(f"Analysis sent to jimkalinov@gmail.com")
                        except Exception as e:
                            st.warning(f"Could not send email: {str(e)}")
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                continue
                
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
    st.header("Analytics")
    if st.session_state['history']:
        df_history = pd.DataFrame(st.session_state['history'])
        
        # Status Distribution
        st.subheader("Document Status Distribution")
        status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
        st.bar_chart(status_counts)
        
        # Time Analysis
        if st.session_state['action_times']:
            st.subheader("Processing Time Analysis")
            time_diffs = [(action - upload).total_seconds() 
                         for upload, action in st.session_state['action_times']]
            avg_time = sum(time_diffs) / len(time_diffs)
            st.metric("Average Processing Time", f"{avg_time:.1f} seconds")

        # Document Volume
        st.subheader("Total Documents")
        st.metric("Total Documents Processed", len(st.session_state['history']))
