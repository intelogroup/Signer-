import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from anthropic import Anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
if 'claude_api_key' not in st.session_state:
    st.session_state['claude_api_key'] = None

# Status emojis
STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌'
}

def send_email(document_name, document_type, summary):
    try:
        # Email configuration
        sender_email = "your_email@gmail.com"  # Replace with your email
        sender_password = "your_app_password"  # Replace with your app password
        receiver_email = "jimkalinov@gmail.com"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"{document_name} from Signer - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Email body
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
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def analyze_document(file_content, file_type):
    try:
        if not st.session_state['claude_api_key']:
            st.error("Claude API key not configured!")
            return None
            
        anthropic = Anthropic(api_key=st.session_state['claude_api_key'])
        
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are a document analyzer. Provide a comprehensive summary of the document content, identify any names mentioned, and highlight any specific actions or requests, especially those directed at Kalinov Jim Rozensky DAMEUS.",
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this {file_type} document content: {file_content}"
                }
            ]
        )
        
        return message.content
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None

def login_user(email, password):
    return email == "admin" and password == "admin123"

# [Previous check_expired_items function remains the same]

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
    # First login configuration
    if st.session_state['claude_api_key'] is None:
        st.title("Configure Claude API")
        api_key = st.text_input("Enter your Claude API key", type="password")
        if st.button("Save API Key"):
            st.session_state['claude_api_key'] = api_key
            st.success("API key saved successfully!")
            st.rerun()
    else:
        # [Previous header code remains the same]

        # File Upload Section
        st.header("Upload Document(s)")
        uploaded_files = st.file_uploader("Choose files", type=['pdf', 'docx', 'png', 'jpg', 'txt'], 
                                        accept_multiple_files=True)

        if uploaded_files:
            for uploaded_file in uploaded_files:
                doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
                st.session_state['doc_id_counter'] += 1
                upload_time = datetime.now()
                
                # Read file content
                file_content = uploaded_file.read()
                try:
                    file_content = file_content.decode('utf-8')
                except:
                    file_content = str(file_content)
                
                # Analyze document
                analysis = analyze_document(file_content, uploaded_file.type)
                
                if analysis:
                    # Send email
                    email_sent = send_email(
                        uploaded_file.name,
                        uploaded_file.type,
                        analysis
                    )
                    
                    if email_sent:
                        st.success(f"Analysis sent to jimkalinov@gmail.com for {uploaded_file.name}")
                
                # Add to documents list and history
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
                    st.session_state['history'].append({
                        'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'id': doc_id,
                        'name': uploaded_file.name,
                        'status': f"Pending {STATUS_EMOJIS['Pending']}",
                        'analysis': analysis
                    })
                    
            st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")

        # [Rest of your existing code remains the same]
