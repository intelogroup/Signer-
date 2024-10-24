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

def analyze_with_claude(content, file_type):
    try:
        headers = {
            'x-api-key': st.secrets["CLAUDE_API_KEY"],
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "temperature": 0,
            "system": "You are a document analyzer. Provide a comprehensive summary of the document content, identify any names mentioned, and highlight any specific actions or requests, especially those directed at Kalinov Jim Rozensky DAMEUS.",
            "messages": [
                {
                    "role": "user",
                    "content": f"Analyze this {file_type} document content: {content}"
                }
            ]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            st.error(f"API Error: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None

def send_email(document_name, document_type, summary):
    try:
        sender_email = st.secrets["EMAIL_SENDER"]
        sender_password = st.secrets["EMAIL_PASSWORD"]
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
    uploaded_files = st.file_uploader("Choose files", type=['txt', 'pdf', 'docx'], 
                                    accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
            st.session_state['doc_id_counter'] += 1
            upload_time = datetime.now()
            
            # Read file content
            content = uploaded_file.read()
            try:
                content = content.decode('utf-8')
            except:
                content = str(content)
            
            # Analyze document
            analysis = analyze_with_claude(content, uploaded_file.type)
            
            if analysis:
                # Send email
                email_sent = send_email(
                    uploaded_file.name,
                    uploaded_file.type,
                    analysis
                )
                
                if email_sent:
                    st.success(f"Analysis sent to jimkalinov@gmail.com for {uploaded_file.name}")
            
            # Add to documents list
            if not any(doc['name'] == uploaded_file.name and doc['status'] == 'Pending' 
                      for doc in st.session_state['documents']):
                
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
                
        st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")

    # [Rest of your existing code remains the same...]
