import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# Initialize session state with all required variables
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
if 'selected_view' not in st.session_state:
    st.session_state['selected_view'] = 'Upload'

STATUS_EMOJIS = {
    'Pending': '⏳',
    'Authorized': '✅',
    'Rejected': '❌'
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

def check_expired_items():
    current_time = datetime.now()
    for doc_id, expiration_time in list(st.session_state['document_removal_times'].items()):
        if current_time > expiration_time:
            st.session_state['documents'] = [doc for doc in st.session_state['documents'] if doc['id'] != doc_id]
            del st.session_state['document_removal_times'][doc_id]

def show_upload_section():
    st.header("Upload Documents 📤")
    uploaded_files = st.file_uploader("Choose files", type=None, accept_multiple_files=True)
    
    if uploaded_files:
        with st.spinner("Processing documents..."):
            for uploaded_file in uploaded_files:
                doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
                st.session_state['doc_id_counter'] += 1
                upload_time = datetime.now()
                
                try:
                    text_content = extract_text_content(uploaded_file)
                    if text_content.strip():
                        analysis = analyze_with_claude(text_content)
                        
                        if analysis:
                            doc_data = {
                                'id': doc_id,
                                'name': uploaded_file.name,
                                'status': 'Pending',
                                'upload_time': upload_time,
                                'analysis': analysis,
                                'file_type': uploaded_file.type,
                                'file_size': uploaded_file.size
                            }
                            
                            st.session_state['documents'].append(doc_data)
                            st.session_state['history'].append({
                                'date': upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                                'id': doc_id,
                                'name': uploaded_file.name,
                                'status': f"Pending {STATUS_EMOJIS['Pending']}",
                                'analysis': analysis
                            })
                            
                            with st.expander(f"📄 Analysis for {uploaded_file.name}"):
                                tab1, tab2 = st.tabs(["Formatted Analysis", "Raw Analysis"])
                                
                                with tab1:
                                    sections = analysis.split('\n')
                                    for section in sections:
                                        if any(header in section for header in ["NAMES:", "KEY INFORMATION:", "DOCUMENT TYPE:", 
                                                                              "DATES & NUMBERS:", "RELATIONSHIPS:", "SUMMARY:"]):
                                            st.markdown(f"### {section}")
                                        elif section.strip():
                                            st.write(section)
                                
                                with tab2:
                                    st.text_area("Full Analysis", analysis, height=300)
                
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    continue
            
            st.success(f"Successfully processed {len(uploaded_files)} document(s)!")

def show_status_section():
    st.header("Document Status 📋")
    check_expired_items()
    
    # Filter options
    status_filter = st.selectbox("Filter by status", ["All", "Pending", "Authorized", "Rejected"])
    
    filtered_docs = st.session_state['documents']
    if status_filter != "All":
        filtered_docs = [doc for doc in filtered_docs if doc['status'] == status_filter]
    
    if filtered_docs:
        for doc in filtered_docs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"📄 {doc['name']} | Status: {doc['status']} {STATUS_EMOJIS[doc['status']]}")
                    st.caption(f"Uploaded: {doc['upload_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if doc['status'] == 'Pending':
                    with col2:
                        if st.button(f"View", key=f"view_{doc['id']}"):
                            with st.expander("Analysis", expanded=True):
                                st.write(doc['analysis'])
                    with col3:
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
                    with col4:
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
                st.divider()
    else:
        st.info("No documents found matching the selected filter")

def show_history_section():
    st.header("Document History 📚")
    
    if st.session_state['history']:
        # Add date range filter
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
        else:
            st.info("No documents found in selected date range")
    else:
        st.info("No document history available")

def show_analytics_section():
    st.header("Analytics Dashboard 📊")
    
    if st.session_state['history']:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status Distribution
            st.subheader("Document Status Distribution")
            df_history = pd.DataFrame(st.session_state['history'])
            status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
            st.bar_chart(status_counts)
            
            # Status Percentages
            st.subheader("Status Breakdown")
            total = len(df_history)
            for status, count in status_counts.items():
                percentage = (count / total) * 100
                st.metric(f"{status}", f"{percentage:.1f}%")
        
        with col2:
            # Time Analysis
            if st.session_state['action_times']:
                st.subheader("Processing Time Analysis")
                time_diffs = [(action - upload).total_seconds() for upload, action in st.session_state['action_times']]
                avg_time = sum(time_diffs) / len(time_diffs)
                max_time = max(time_diffs)
                min_time = min(time_diffs)
                
                st.metric("Average Processing Time", f"{avg_time:.1f} seconds")
                st.metric("Fastest Processing", f"{min_time:.1f} seconds")
                st.metric("Slowest Processing", f"{max_time:.1f} seconds")
                
                # Processing Time Distribution
                st.subheader("Processing Time Distribution")
                time_df = pd.DataFrame(time_diffs, columns=['seconds'])
                st.line_chart(time_df)
        
        # Document Volume Trends
        st.subheader("Document Volume Trends")
        df_history['date'] = pd.to_datetime(df_history['date'])
        daily_volumes = df_history.groupby(df_history['date'].dt.date).size()
        st.line_chart(daily_volumes)
    else:
        st.info("No data available for analytics")

def main():
    if not st.session_state['logged_in']:
        st.title("Document Analyzer & Signer 📝")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if login_user(email, password):
                    st.session_state['logged_in'] = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    else:
        # Header with profile menu
        header_col1, header_col2 = st.columns([0.7, 0.3])
        with header_col1:
            st.title("Document Analyzer & Signer ✒️")
        with header_col2:
            with st.expander("👤 Profile Menu"):
                st.write(f"Welcome, Admin!")
                st.divider()
                if st.button("📊 Dashboard"):
                    st.session_state['selected_view'] = 'Analytics'
                if st.button("👤 My Profile"):
                    st.info("Profile settings coming soon")
                if st.button("ℹ️ About"):
                    st.info("Document Analyzer & Signer v2.0")
                if st.button("🚪 Logout"):
                    st.session_state['logged_in'] = False
                    st.rerun()
        
        # Navigation
        st.sidebar.title("Navigation")
        view = st.sidebar.radio("Go to", 
                              ["Upload", "Status", "History", "Analytics"],
                              key="selected_view")
        
        # Main content based on selected view
        if view == "Upload":
            show_upload_section()
        elif view == "Status":
            show_status_section()
        elif view == "History":
            show_history_section()
        elif view == "Analytics":
            show_analytics_section()

if __name__ == "__main__":
    main()
