import streamlit as st
import requests
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

def main():
    if not st.session_state['logged_in']:
        st.title("Document Analyzer & Signer 📝")
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
        # Profile dropdown in header
        col1, col2 = st.columns([0.9, 0.1])
        with col2:
            with st.expander("👤"):
                if st.button("My Profile"):
                    st.info("Profile settings coming soon")
                if st.button("About Us"):
                    st.info("Document Analyzer & Signer v1.0")
                if st.button("Logout"):
                    st.session_state['logged_in'] = False
                    st.rerun()

        st.title("Document Analyzer & Signer ✒️")
        
        # File Upload Section
        uploaded_file = st.file_uploader("Upload document", type=None)
        
        if uploaded_file:
            doc_id = f"SIGN{st.session_state['doc_id_counter']:03d}"
            st.session_state['doc_id_counter'] += 1
            upload_time = datetime.now()
            
            try:
                # Extract and analyze content
                text_content = extract_text_content(uploaded_file)
                if text_content.strip():
                    with st.spinner("🔍 Analyzing document..."):
                        analysis = analyze_with_claude(text_content)
                        
                        if analysis:
                            # Add to documents list
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
                            
                            # Display Analysis
                            st.subheader("📊 Analysis Results")
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
                st.error(f"Error processing document: {str(e)}")

        # Document Status Section
        st.header("Document Status")
        check_expired_items()
        
        pending_docs = [doc for doc in st.session_state['documents'] if doc['status'] == 'Pending']
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
        st.header("History")
        if st.session_state['history']:
            history_df = pd.DataFrame(st.session_state['history'])
            st.dataframe(history_df.sort_values('date', ascending=False), hide_index=True)

            # Analytics Section
            st.header("Analytics")
            
            # Status Distribution
            st.subheader("Document Status Distribution")
            status_counts = history_df['status'].apply(lambda x: x.split()[0]).value_counts()
            st.bar_chart(status_counts)
            
            # Time Analysis
            if st.session_state['action_times']:
                st.subheader("Processing Time Analysis")
                time_diffs = [(action - upload).total_seconds() for upload, action in st.session_state['action_times']]
                avg_time = sum(time_diffs) / len(time_diffs)
                st.metric("Average Processing Time", f"{avg_time:.1f} seconds")

if __name__ == "__main__":
    main()
