import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'documents' not in st.session_state:
    st.session_state['documents'] = []
if 'pending_analysis' not in st.session_state:
    st.session_state['pending_analysis'] = []
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'doc_id_counter' not in st.session_state:
    st.session_state['doc_id_counter'] = 1
if 'document_removal_times' not in st.session_state:
    st.session_state['document_removal_times'] = {}
if 'action_times' not in st.session_state:
    st.session_state['action_times'] = []
if 'user_actions' not in st.session_state:
    st.session_state['user_actions'] = []

STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌',
    'Processing': '🔄',
    'Analyzed': '🔍'
}

def extract_text_content(uploaded_file):
    """Attempt to extract text content from uploaded file"""
    try:
        content = uploaded_file.read()
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('latin-1')
    except Exception as e:
        st.warning(f"Note: File content might not be perfectly extracted. Proceeding with best effort.")
        return str(content)

def analyze_with_claude(text):
    try:
        headers = {
            "x-api-key": st.secrets["CLAUDE_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        prompt = """Please analyze this document content carefully. Provide a structured analysis with the following:

1. NAMES: List all person names found in the document, with their context if available
2. KEY INFORMATION: Extract and list the main points or facts
3. DOCUMENT TYPE: Identify the type or purpose of the document
4. DATES & NUMBERS: List any significant dates, numbers, or quantities
5. RELATIONSHIPS: Identify any relationships or connections between named entities
6. SUMMARY: Provide a brief summary of the document's main purpose

Please be precise and factual. If you're uncertain about any information, indicate that explicitly.

Document content to analyze:

{text}"""
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": prompt.format(text=text)}
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            st.error(f"API Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def login_user(email, password):
    return email == "admin" and password == "admin123"

def log_user_action(action, details):
    st.session_state['user_actions'].append({
        'timestamp': datetime.now(),
        'action': action,
        'details': details
    })

def check_expired_items():
    current_time = datetime.now()
    for doc_id, expiration_time in list(st.session_state['document_removal_times'].items()):
        if current_time > expiration_time:
            st.session_state['documents'] = [doc for doc in st.session_state['documents'] if doc['id'] != doc_id]
            del st.session_state['document_removal_times'][doc_id]

def get_navigation():
    st.sidebar.title("Navigation 📱")
    return st.sidebar.radio(
        "Go to",
        ["📤 Upload", "📋 Status", "📚 History", "📊 Analytics"],
        label_visibility="collapsed"
    ).split()[1]  # Get the second word (after emoji)

def show_upload_section():
    st.header("Upload Documents")
    
    # File uploader
    uploaded_files = st.file_uploader("Choose files", type=None, accept_multiple_files=True)
    
    if uploaded_files:
        with st.spinner("Processing uploads..."):
            for uploaded_file in uploaded_files:
                doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
                st.session_state['doc_id_counter'] += 1
                upload_time = datetime.now()
                
                # Add directly to documents list
                doc_data = {
                    'id': doc_id,
                    'name': uploaded_file.name,
                    'status': 'Pending',
                    'upload_time': upload_time,
                    'file_type': uploaded_file.type,
                    'file_size': uploaded_file.size,
                    'content': extract_text_content(uploaded_file),
                    'analysis': None
                }
                
                # Add to both lists
                st.session_state['documents'].append(doc_data)
                st.session_state['pending_analysis'].append(doc_data.copy())
                
                # Add to history
                st.session_state['history'].append({
                    'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'id': doc_id,
                    'name': uploaded_file.name,
                    'status': f"Pending {STATUS_EMOJIS['Pending']}",
                    'analysis': None
                })
                
                log_user_action('upload', f"Uploaded document: {uploaded_file.name}")

        st.success(f"Successfully uploaded {len(uploaded_files)} document(s)!")

    # Show pending analysis section
    if st.session_state['pending_analysis']:
        st.subheader("Documents Available for Analysis")
        
        # Create columns for the header
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write("Document Name")
        with col2:
            st.write("Analyze")
        
        st.divider()
        
        # List documents with analyze buttons
        for doc in st.session_state['pending_analysis']:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📄 {doc['name']} ({doc['file_size']/1024:.1f} KB)")
            with col2:
                if st.button("🔍 Analyze", key=f"analyze_{doc['id']}"):
                    with st.spinner(f"Analyzing {doc['name']}..."):
                        analysis = analyze_with_claude(doc['content'])
                        
                        # Update document with analysis
                        for stored_doc in st.session_state['documents']:
                            if stored_doc['id'] == doc['id']:
                                stored_doc['analysis'] = analysis
                                break
                        
                        # Update history
                        for hist_doc in st.session_state['history']:
                            if hist_doc['id'] == doc['id']:
                                hist_doc['analysis'] = analysis
                        
                        # Remove from pending analysis
                        st.session_state['pending_analysis'] = [
                            d for d in st.session_state['pending_analysis'] if d['id'] != doc['id']
                        ]
                        
                        log_user_action('analyze', f"Analyzed document: {doc['name']}")
                        st.success(f"Analysis completed for {doc['name']}")
                        st.rerun()

def show_status_section():
    st.header("Document Status")
    check_expired_items()
    
    # Filter options
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Pending", "Authorized", "Rejected"]
    )
    
    filtered_docs = st.session_state['documents']
    if status_filter != "All":
        filtered_docs = [doc for doc in filtered_docs if doc['status'] == status_filter]
    
    if filtered_docs:
        for doc in filtered_docs:
            with st.container():
                # Document info and actions
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"📄 {doc['name']} | {doc['status']} {STATUS_EMOJIS[doc['status']]}")
                    st.caption(f"Uploaded: {doc['upload_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if doc['status'] == 'Pending':
                    with col2:
                        if st.button("✅ Accept", key=f"accept_{doc['id']}", type="primary"):
                            doc['status'] = "Authorized"
                            action_time = datetime.now()
                            
                            # Update history
                            for hist_doc in st.session_state['history']:
                                if hist_doc['id'] == doc['id']:
                                    hist_doc['status'] = f"Authorized {STATUS_EMOJIS['Authorized']}"
                                    hist_doc['date'] = action_time.strftime("%Y-%m-%d %H:%M:%S")
                            
                            st.session_state['action_times'].append((doc['upload_time'], action_time))
                            st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=5)
                            log_user_action('authorize', f"Authorized document: {doc['name']}")
                            st.rerun()
                    
                    with col3:
                        if st.button("❌ Reject", key=f"reject_{doc['id']}"):
                            doc['status'] = "Rejected"
                            action_time = datetime.now()
                            
                            # Update history
                            for hist_doc in st.session_state['history']:
                                if hist_doc['id'] == doc['id']:
                                    hist_doc['status'] = f"Rejected {STATUS_EMOJIS['Rejected']}"
                                    hist_doc['date'] = action_time.strftime("%Y-%m-%d %H:%M:%S")
                            
                            st.session_state['action_times'].append((doc['upload_time'], action_time))
                            st.session_state['document_removal_times'][doc['id']] = datetime.now() + timedelta(minutes=5)
                            log_user_action('reject', f"Rejected document: {doc['name']}")
                            st.rerun()
                
                # Analysis section
                if doc.get('analysis'):
                    with st.expander("View Analysis"):
                        st.write("Document Analysis:")
                        sections = doc['analysis'].split('\n')
                        for section in sections:
                            if any(header in section for header in ["NAMES:", "KEY INFORMATION:", 
                                                                  "DOCUMENT TYPE:", "DATES & NUMBERS:", 
                                                                  "RELATIONSHIPS:", "SUMMARY:"]):
                                st.markdown(f"### {section}")
                            elif section.strip():
                                st.write(section)
                
                st.divider()
    else:
        st.info("No documents found matching the selected filter")

def show_history_section():
    st.header("Document History")
    
    if st.session_state['history']:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End date", value=datetime.now())
        
        # Convert history to DataFrame
        history_df = pd.DataFrame(st.session_state['history'])
        history_df['date'] = pd.to_datetime(history_df['date'])
        
        # Apply date filter
        mask = (history_df['date'].dt.date >= start_date) & (history_df['date'].dt.date <= end_date)
        filtered_df = history_df[mask]
        
        if not filtered_df.empty:
            # Show history table
            st.dataframe(
                filtered_df.sort_values('date', ascending=False),
                hide_index=True,
                column_config={
                    "date": "Timestamp",
                    "id": "Document ID",
                    "name": "Document Name",
                    "status": "Status"
                }
            )
            
            # Export option
            if st.button("📥 Export History"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "document_history.csv",
                    "text/csv",
                    key='download-csv'
                )
        else:
            st.info("No documents found in selected date range")
    else:
        st.info("No document history available")

def show_enhanced_analytics():
    st.header("Analytics Dashboard")
    
    if not st.session_state['history']:
        st.info("No data available for analytics yet")
        return
        
    # Create tabs for different analytics views
    tab1, tab2, tab3 = st.tabs(["📊 Document Stats", "👥 User Activity", "⚡ Performance"])
    
    with tab1:
        st.subheader("Document Statistics")
        
        # Document counts and stats
        col1, col2 = st.columns(2)
        
        with col1:
            total_docs = len(st.session_state['documents'])
            pending_docs = len([d for d in st.session_state['documents'] if d['status'] == 'Pending'])
            analyzed_docs = len([d for d in st.session_state['documents'] if d.get('analysis')])
            
            st.metric("Total Documents", total_docs)
            st.metric("Pending Documents", pending_docs)
            st.metric("Analyzed Documents", analyzed_docs)
        
        with col2:
            # Status Distribution
            st.subheader("Status Distribution")
            df_history = pd.DataFrame(st.session_state['history'])
            status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
            st.bar_chart(status_counts)
    
    with tab2:
        st.subheader("User Activity")
        
        if st.session_state['user_actions']:
            df_actions = pd.DataFrame(st.session_state['user_actions'])
            df_actions['timestamp'] = pd.to_datetime(df_actions['timestamp'])
            
            # Activity Timeline
            st.subheader("Daily Activity")
            daily_activity = df_actions.groupby(df_actions['timestamp'].dt.date).size()
            st.line_chart(daily_activity)
            
            # Recent Actions
            st.subheader("Recent Actions")
            recent = df_actions.tail(5)
            for _, action in recent.iterrows():
                st.write(f"🔹 {action['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {action['action']}: {action['details']}")
    
    with tab3:
        st.subheader("Performance Metrics")
        
        if st.session_state['action_times']:
            time_diffs = [(action - upload).total_seconds() 
                         for upload, action in st.session_state['action_times']]
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_time = sum(time_diffs) / len(time_diffs)
                st.metric("Average Processing Time", f"{avg_time:.1f}s")
                
                # Success Rates
                df_history = pd.DataFrame(st.session_state['history'])
                total = len(df_history)
                if total > 0:
                    approved = len(df_history[df_history['status'].str.contains('Authorized')])
                    rejected = len(df_history[df_history['status'].str.contains('Rejected')])
                    
                    st.metric("Approval Rate", f"{(approved/total*100):.1f}%")
                    st.metric("Rejection Rate", f"{(rejected/total*100):.1f}%")
            
            with col2:
                # Processing Time Trend
                st.subheader("Processing Times")
                time_df = pd.DataFrame(time_diffs, columns=['seconds'])
                st.line_chart(time_df)

def main():
    if not st.session_state['logged_in']:
        # Login page
        st.title("Document Analyzer & Signer 📝")
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.write("### Login")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    if login_user(email, password):
                        st.session_state['logged_in'] = True
                        log_user_action('login', 'User logged in')
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
    else:
        # Main application
        st.title("Document Analyzer & Signer ✒️")
        
        # Sidebar
        with st.sidebar:
            # User info
            st.write("### 👤 Welcome, Admin!")
            if st.button("🚪 Logout"):
                st.session_state['logged_in'] = False
                log_user_action('logout', 'User logged out')
                st.rerun()
            
            st.divider()
            
            # Navigation
            view = get_navigation()
        
        # Main content
        if view == "Upload":
            show_upload_section()
        elif view == "Status":
            show_status_section()
        elif view == "History":
            show_history_section()
        elif view == "Analytics":
            show_enhanced_analytics()

if __name__ == "__main__":
    main()

