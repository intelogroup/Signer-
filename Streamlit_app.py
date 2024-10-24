import streamlit as st
import requests
import io

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def read_file_content(uploaded_file):
    """Read content from uploaded file"""
    try:
        # For text files, read directly
        content = uploaded_file.read()
        
        # Try to decode as text
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # If can't decode, return as binary
            return str(content)
            
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def analyze_with_claude(text):
    try:
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        prompt = """Please analyze this document content carefully. Provide a structured analysis with the following:

1. NAMES: List all person names found in the document, with their context if available
2. KEY INFORMATION: Extract and list the main points or facts
3. DOCUMENT TYPE: Identify the type or purpose of the document
4. DATES & NUMBERS: List any significant dates, numbers, or quantities
5. RELATIONSHIPS: Identify any relationships or connections between named entities

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

def main():
    st.title("Multi-Document Content Analyzer 📄")
    
    # Initialize session state for storing multiple analyses
    if 'analyses' not in st.session_state:
        st.session_state['analyses'] = {}
    
    # File upload - multiple files
    uploaded_files = st.file_uploader(
        "Upload documents", 
        type=['txt', 'csv', 'json', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Add select all/none buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select All"):
                st.session_state['selected_files'] = [file.name for file in uploaded_files]
        with col2:
            if st.button("Clear Selection"):
                st.session_state['selected_files'] = []
        
        # Initialize selected files if not exists
        if 'selected_files' not in st.session_state:
            st.session_state['selected_files'] = []
        
        # File selection
        selected_files = st.multiselect(
            "Select files to analyze:",
            [file.name for file in uploaded_files],
            default=st.session_state['selected_files']
        )
        
        if st.button("Analyze Selected Documents"):
            for uploaded_file in uploaded_files:
                if uploaded_file.name in selected_files:
                    st.write(f"📄 Processing: {uploaded_file.name}")
                    
                    try:
                        # Read file content
                        text_content = read_file_content(uploaded_file)
                        
                        if text_content and text_content.strip():
                            # Create a unique key for this document
                            doc_key = f"{uploaded_file.name}_{hash(text_content)}"
                            
                            # Show text content in expander
                            with st.expander(f"📝 Content: {uploaded_file.name}"):
                                st.text_area("Original Text", text_content, height=200)
                            
                            # Get analysis from Claude
                            with st.spinner(f"🔍 Analyzing {uploaded_file.name}..."):
                                analysis = analyze_with_claude(text_content)
                                if analysis:
                                    st.subheader(f"📊 Results: {uploaded_file.name}")
                                    
                                    # Create tabs for this document
                                    tab1, tab2 = st.tabs([f"Formatted - {uploaded_file.name}", 
                                                        f"Raw - {uploaded_file.name}"])
                                    
                                    with tab1:
                                        sections = analysis.split('\n')
                                        for section in sections:
                                            if any(header in section for header in [
                                                "NAMES:", "KEY INFORMATION:", 
                                                "DOCUMENT TYPE:", "DATES & NUMBERS:", 
                                                "RELATIONSHIPS:"
                                            ]):
                                                st.markdown(f"**{section}**")
                                            elif section.strip():
                                                st.write(section)
                                    
                                    with tab2:
                                        st.text_area("Full Analysis", analysis, height=300)
                                    
                                    # Save analysis
                                    st.session_state['analyses'][doc_key] = {
                                        'name': uploaded_file.name,
                                        'content': text_content,
                                        'analysis': analysis
                                    }
                        else:
                            st.error(f"❗ Could not read {uploaded_file.name}")
                            
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
    
    # Display saved analyses
    if st.session_state['analyses']:
        st.subheader("📋 Saved Analyses")
        for doc_key, doc_data in st.session_state['analyses'].items():
            with st.expander(f"View Analysis: {doc_data['name']}"):
                st.write(doc_data['analysis'])
                if st.button(f"Remove", key=f"remove_{doc_key}"):
                    del st.session_state['analyses'][doc_key]
                    st.rerun()

if __name__ == "__main__":
    main()
