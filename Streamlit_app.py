import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from anthropic import Anthropic
import os
from dotenv import load_dotenv
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Email configuration
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')  # Gmail App Password

def analyze_document(file_content, filename):
    try:
        # Convert file content to text for analysis
        content = file_content.decode('utf-8')
        
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are a document analyzer. Extract key information including: 1) Brief summary 2) Names mentioned 3) Any actions requested specifically for Kalinov Jim Rozensky DAMEUS. Keep the analysis concise.",
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this document content: {content}"
                }
            ]
        )
        
        analysis = message.content
        
        # Check if any of the specified names are mentioned
        names = ["kalinov", "jim", "rozensky", "dameus"]
        if any(name in content.lower() for name in names):
            send_email_alert(filename, analysis)
            
        return analysis
    except Exception as e:
        return f"Error analyzing document: {str(e)}"

def send_email_alert(filename, analysis):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = "jimkalinov@gmail.com"
        msg['Subject'] = f"Document Analysis Alert: {filename}"
        
        body = f"""
        Document Analysis Report
        
        Filename: {filename}
        
        Analysis:
        {analysis}
        
        This is an automated alert from your Document Signer system.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")

# [Rest of your existing code remains the same until the file upload section]

    # File Upload Section
    st.header("Upload Document(s)")
    uploaded_files = st.file_uploader("Choose files", type=['pdf', 'docx', 'png', 'jpg', 'txt'], 
                                    accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
            st.session_state['doc_id_counter'] += 1
            upload_time = datetime.now()
            
            if not any(doc['name'] == uploaded_file.name and doc['status'] == 'Pending' 
                      for doc in st.session_state['documents']):
                
                # Read and analyze document content
                file_content = uploaded_file.read()
                analysis = analyze_document(file_content, uploaded_file.name)
                
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
                
        st.success(f"{len(uploaded_files)} document(s) uploaded and analyzed successfully!")

# [Rest of your existing code remains the same]
```

📋 **.env** file (Create this in your project root):
```text
ANTHROPIC_API_KEY=your_claude_api_key_here
EMAIL_ADDRESS=your_gmail_address
EMAIL_APP_PASSWORD=your_gmail_app_password
