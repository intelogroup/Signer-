import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import numpy as np
import json
import io

# Initialize session state with all required variables
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
if 'selected_view' not in st.session_state:
    st.session_state['selected_view'] = 'Upload'
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

def show_upload_section():
    st.header("Upload Documents 📤")
    
    # File uploader
    uploaded_files = st.file_uploader("Choose files", type=None, accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
            st.session_state['doc_id_counter'] += 1
            
            # Add to pending analysis
            if not any(doc['name'] == uploaded_file.name for doc in st.session_state['pending_analysis']):
                doc_data = {
                    'id': doc_id,
                    'name': uploaded_file.name,
                    'status': 'Pending',
                    'upload_time': datetime.now(),
                    'file_type': uploaded_file.type,
                    'file_size': uploaded_file.size,
                    'content': extract_text_content(uploaded_file),
                    'analyzed': False
                }
                st.session_state['pending_analysis'].append(doc_data)
                log_user_action('upload', f"Uploaded document: {uploaded_file.name}")
        
        st.success(f"Successfully uploaded {len(uploaded_files)} document(s)!")

    # Show pending documents
    if st.session_state['pending_analysis']:
        st.subheader("Documents Pending Analysis")
        
        selected_docs = []
        for doc in st.session_state['pending_analysis']:
            col1, col2 = st.columns([4, 1])
            with col1:
                selected = st.checkbox(
                    f"📄 {doc['name']} ({doc['file_type']}) - {doc['file_size']/1024:.1f} KB",
                    key=f"select_{doc['id']}"
                )
                if selected:
                    selected_docs.append(doc)
        
        if selected_docs:
            if st.button(f"Process Selected Documents ({len(selected_docs)})", type="primary"):
                with st.spinner("Processing selected documents..."):
                    for doc in selected_docs:
                        # Analyze document
                        analysis = analyze_with_claude(doc['content'])
                        
                        # Add to documents list
                        doc_data = {
                            'id': doc['id'],
                            'name': doc['name'],
                            'status': 'Pending',
                            'upload_time': doc['upload_time'],
                            'analysis': analysis,
                            'file_type': doc['file_type'],
                            'file_size': doc['file_size']
                        }
                        
                        st.session_state['documents'].append(doc_data)
                        st.session_state['history'].append({
                            'date': doc['upload_time'].strftime("%Y-%m-%d %H:%M:%S"),
                            'id': doc['id'],
                            'name': doc['name'],
                            'status': f"Pending {STATUS_EMOJIS['Pending']}",
                            'analysis': analysis
                        })
                        
                        # Remove from pending
                        st.session_state['pending_analysis'] = [
                            d for d in st.session_state['pending_analysis'] if d['id'] != doc['id']
                        ]
                        
                        log_user_action('process', f"Processed document: {doc['name']}")
                
                st.success("Selected documents processed successfully!")
                st.rerun()

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
                                if doc.get('analysis'):
                                    tab1, tab2 = st.tabs(["Formatted Analysis", "Raw Analysis"])
                                    
                                    with tab1:
                                        sections = doc['analysis'].split('\n')
                                        for section in sections:
                                            if any(header in section for header in ["NAMES:", "KEY INFORMATION:", 
                                                                                  "DOCUMENT TYPE:", "DATES & NUMBERS:", 
                                                                                  "RELATIONSHIPS:", "SUMMARY:"]):
                                                st.markdown(f"### {section}")
                                            elif section.strip():
                                                st.write(section)
                                    
                                    with tab2:
                                        st.text_area("Full Analysis", doc['analysis'], height=300)
                                else:
                                    st.info("No analysis available")
                    
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
                            log_user_action('authorize', f"Authorized document: {doc['name']}")
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
                            log_user_action('reject', f"Rejected document: {doc['name']}")
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
            
            # Export option
            if st.button("Export History"):
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
                    log_user_action('login', 'User logged in')
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
                    st.info("Document Analyzer & Signer v3.0")
                if st.button("🚪 Logout"):
                    log_user_action('logout', 'User logged out')
                    st.session_state['logged_in'] = False
                    st.rerun()
        
        # Navigation
        st.sidebar.title("Navigation")
        view = st.sidebar.radio("Go to", 
                              ["Upload", "Status", "History", "Analytics"],
                              key="selected_view")
        
        # Main content based on selected view
        # Main content based on selected view
        if view == "Upload":
            show_upload_section()
        elif view == "Status":
            show_status_section()
        elif view == "History":
            show_history_section()
        elif view == "Analytics":
            st.header("Analytics Dashboard 📊")
            
            # Basic analytics - Part 1 (more advanced features coming in Part 2)
            if st.session_state['history']:
                tab1, tab2 = st.tabs(["Document Overview", "Processing Times"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        # Status Distribution
                        st.subheader("Document Status Distribution")
                        df_history = pd.DataFrame(st.session_state['history'])
                        status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
                        st.bar_chart(status_counts)
                    
                    with col2:
                        # Quick Stats
                        st.subheader("Quick Statistics")
                        total_docs = len(df_history)
                        pending_docs = len([d for d in st.session_state['documents'] if d['status'] == 'Pending'])
                        analyzed_docs = len([d for d in st.session_state['documents'] if 'analysis' in d])
                        
                        st.metric("Total Documents", total_docs)
                        st.metric("Pending Documents", pending_docs)
                        st.metric("Analyzed Documents", analyzed_docs)
                
                with tab2:
                    if st.session_state['action_times']:
                        st.subheader("Processing Time Analysis")
                        time_diffs = [(action - upload).total_seconds() 
                                    for upload, action in st.session_state['action_times']]
                        
                        avg_time = sum(time_diffs) / len(time_diffs)
                        max_time = max(time_diffs)
                        min_time = min(time_diffs)
                        
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Average Time", f"{avg_time:.1f}s")
                        with cols[1]:
                            st.metric("Fastest", f"{min_time:.1f}s")
                        with cols[2]:
                            st.metric("Slowest", f"{max_time:.1f}s")
                        
                        # Processing Time Trend
                        st.subheader("Processing Time Trend")
                        time_df = pd.DataFrame(time_diffs, columns=['seconds'])
                        st.line_chart(time_df)
                
                # Document Volume Trend
                st.subheader("Document Volume Trend")
                df_history['date'] = pd.to_datetime(df_history['date'])
                daily_volumes = df_history.groupby(df_history['date'].dt.date).size()
                st.area_chart(daily_volumes)
                
                # Pending Analysis
                if st.session_state['pending_analysis']:
                    st.subheader("Documents Awaiting Analysis")
                    pending_df = pd.DataFrame(st.session_state['pending_analysis'])
                    st.dataframe(
                        pending_df[['name', 'upload_time', 'file_type', 'file_size']],
                        hide_index=True
                    )
            else:
                st.info("No data available for analytics yet")

if __name__ == "__main__":
    main()  

def generate_custom_report(start_date, end_date, metrics):
    """Generate custom report based on selected metrics"""
    report_data = {}
    
    df_history = pd.DataFrame(st.session_state['history'])
    df_history['date'] = pd.to_datetime(df_history['date'])
    mask = (df_history['date'].dt.date >= start_date) & (df_history['date'].dt.date <= end_date)
    filtered_df = df_history[mask]
    
    if 'document_stats' in metrics:
        report_data['document_stats'] = {
            'total_documents': len(filtered_df),
            'status_distribution': filtered_df['status'].apply(lambda x: x.split()[0]).value_counts().to_dict(),
            'file_types': pd.DataFrame(st.session_state['documents'])['file_type'].value_counts().to_dict(),
            'avg_file_size': pd.DataFrame(st.session_state['documents'])['file_size'].mean() / 1024  # KB
        }
    
    if 'processing_times' in metrics:
        time_diffs = [(action - upload).total_seconds() 
                     for upload, action in st.session_state['action_times']]
        report_data['processing_times'] = {
            'average_time': sum(time_diffs) / len(time_diffs) if time_diffs else 0,
            'max_time': max(time_diffs) if time_diffs else 0,
            'min_time': min(time_diffs) if time_diffs else 0,
            'time_distribution': pd.qcut(time_diffs, 4).value_counts().to_dict() if time_diffs else {}
        }
    
    if 'user_activity' in metrics:
        df_actions = pd.DataFrame(st.session_state['user_actions'])
        if not df_actions.empty:
            df_actions['timestamp'] = pd.to_datetime(df_actions['timestamp'])
            mask = (df_actions['timestamp'].dt.date >= start_date) & 
                  (df_actions['timestamp'].dt.date <= end_date)
            filtered_actions = df_actions[mask]
            
            report_data['user_activity'] = {
                'total_actions': len(filtered_actions),
                'action_types': filtered_actions['action'].value_counts().to_dict(),
                'daily_activity': filtered_actions.groupby(
                    filtered_actions['timestamp'].dt.date
                ).size().to_dict()
            }
    
    if 'performance_metrics' in metrics:
        report_data['performance_metrics'] = {
            'approval_rate': len(filtered_df[filtered_df['status'].str.contains('Authorized')]) / 
                           len(filtered_df) if len(filtered_df) > 0 else 0,
            'rejection_rate': len(filtered_df[filtered_df['status'].str.contains('Rejected')]) / 
                            len(filtered_df) if len(filtered_df) > 0 else 0,
            'average_processing_time': np.mean(time_diffs) if time_diffs else 0
        }
    
    return report_data

def show_enhanced_analytics():
    st.title("Enhanced Analytics Dashboard 📊")
    
    # Main Analytics Tabs
    tabs = st.tabs(["Document Analytics", "User Activity", "Performance Metrics", "Custom Reports"])
    
    with tabs[0]:  # Document Analytics
        st.header("Document Analytics")
        
        if st.session_state['history']:
            col1, col2 = st.columns(2)
            
            with col1:
                # Enhanced Status Distribution
                st.subheader("Status Distribution")
                df_history = pd.DataFrame(st.session_state['history'])
                status_counts = df_history['status'].apply(lambda x: x.split()[0]).value_counts()
                fig_status = px.pie(values=status_counts.values, 
                                  names=status_counts.index, 
                                  title="Document Status Distribution")
                st.plotly_chart(fig_status)
                
                # Document Types Analysis
                st.subheader("Document Types")
                doc_types = pd.DataFrame(st.session_state['documents'])['file_type'].value_counts()
                fig_types = px.bar(x=doc_types.index, 
                                 y=doc_types.values, 
                                 title="Document Types Distribution")
                st.plotly_chart(fig_types)
            
            with col2:
                # Processing Time Distribution
                if st.session_state['action_times']:
                    st.subheader("Processing Time Distribution")
                    time_diffs = [(action - upload).total_seconds() 
                                for upload, action in st.session_state['action_times']]
                    fig_time = px.histogram(x=time_diffs, 
                                          title="Processing Time Distribution",
                                          labels={'x': 'Time (seconds)'})
                    st.plotly_chart(fig_time)
                
                # Document Size Analysis
                st.subheader("Document Sizes")
                doc_sizes = pd.DataFrame(st.session_state['documents'])['file_size'] / 1024  # KB
                fig_sizes = px.box(doc_sizes, 
                                 title="Document Size Distribution (KB)")
                st.plotly_chart(fig_sizes)
    
    with tabs[1]:  # User Activity
        st.header("User Activity Analysis")
        
        if st.session_state['user_actions']:
            df_actions = pd.DataFrame(st.session_state['user_actions'])
            df_actions['timestamp'] = pd.to_datetime(df_actions['timestamp'])
            
            # Activity Timeline
            st.subheader("Activity Timeline")
            daily_activity = df_actions.groupby(df_actions['timestamp'].dt.date).size()
            fig_timeline = px.line(x=daily_activity.index, 
                                 y=daily_activity.values,
                                 title="Daily Activity Volume")
            st.plotly_chart(fig_timeline)
            
            # Action Type Distribution
            st.subheader("Action Type Distribution")
            action_counts = df_actions['action'].value_counts()
            fig_actions = px.pie(values=action_counts.values,
                               names=action_counts.index,
                               title="User Actions Distribution")
            st.plotly_chart(fig_actions)
            
            # Hourly Activity Heatmap
            st.subheader("Hourly Activity Pattern")
            hourly_activity = df_actions.groupby([
                df_actions['timestamp'].dt.dayofweek,
                df_actions['timestamp'].dt.hour
            ]).size().unstack()
            fig_heatmap = px.imshow(hourly_activity,
                                  title="Activity Heatmap by Hour and Day",
                                  labels=dict(x="Hour of Day", y="Day of Week"))
            st.plotly_chart(fig_heatmap)
    
    with tabs[2]:  # Performance Metrics
        st.header("Performance Metrics")
        
        if st.session_state['history']:
            col1, col2 = st.columns(2)
            
            with col1:
                # Processing Efficiency
                st.subheader("Processing Efficiency")
                processing_times = pd.Series([(action - upload).total_seconds() 
                                           for upload, action in st.session_state['action_times']])
                
                efficiency_metrics = {
                    "Average Processing Time": f"{processing_times.mean():.1f}s",
                    "90th Percentile": f"{processing_times.quantile(0.9):.1f}s",
                    "Processing Time StdDev": f"{processing_times.std():.1f}s"
                }
                
                for metric, value in efficiency_metrics.items():
                    st.metric(metric, value)
                
                # Efficiency Trend
                fig_trend = px.line(y=processing_times.rolling(5).mean(),
                                  title="Processing Time Trend (5-doc rolling average)")
                st.plotly_chart(fig_trend)
            
            with col2:
                # Success Metrics
                st.subheader("Success Metrics")
                df_history = pd.DataFrame(st.session_state['history'])
                total_docs = len(df_history)
                
                approval_rate = len(df_history[df_history['status'].str.contains('Authorized')]) / total_docs
                rejection_rate = len(df_history[df_history['status'].str.contains('Rejected')]) / total_docs
                
                st.metric("Approval Rate", f"{approval_rate:.1%}")
                st.metric("Rejection Rate", f"{rejection_rate:.1%}")
                
                # Daily Success Rates
                df_history['date'] = pd.to_datetime(df_history['date'])
                daily_rates = df_history.groupby(df_history['date'].dt.date).agg({
                    'status': lambda x: sum(x.str.contains('Authorized')) / len(x)
                })
                
                fig_rates = px.line(daily_rates,
                                  title="Daily Approval Rates")
                st.plotly_chart(fig_rates)
    
    with tabs[3]:  # Custom Reports
        st.header("Custom Report Generator")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", 
                                     value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date",
                                   value=datetime.now())
        
        # Select metrics to include
        st.subheader("Select Metrics to Include")
        metrics = st.multiselect(
            "Choose metrics for your report",
            ["document_stats", "processing_times", "user_activity", "performance_metrics"],
            default=["document_stats"]
        )
        
        if st.button("Generate Report"):
            report_data = generate_custom_report(start_date, end_date, metrics)
            
            st.subheader("Generated Report")
            st.json(report_data)
            
            # Export options
            export_format = st.selectbox("Export Format", ["JSON", "CSV", "Excel"])
            if st.button("Export Report"):
                if export_format == "JSON":
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(report_data, indent=2),
                        file_name="analytics_report.json",
                        mime="application/json"
                    )
                elif export_format == "CSV":
                    df_report = pd.json_normalize(report_data)
                    st.download_button(
                        "Download CSV",
                        data=df_report.to_csv(index=False),
                        file_name="analytics_report.csv",
                        mime="text/csv"
                    )
                else:  # Excel
                    with io.BytesIO() as buffer:
                        df_report = pd.json_normalize(report_data)
                        df_report.to_excel(buffer, index=False)
                        st.download_button(
                            "Download Excel",
                            data=buffer.getvalue(),
                            file_name="analytics_report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

# Update the main function to use enhanced analytics
def main():
    # ... (previous main code remains the same until the view selection)
    
    if view == "Analytics":
        show_enhanced_analytics()
    # ... (rest of the main function remains the same)

