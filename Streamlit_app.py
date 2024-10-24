import streamlit as st
import requests
from streamlit_document_ai import process_document

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

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
    
    # File upload - now accepts multiple files and more formats
    uploaded_files = st.file_uploader(
        "Upload documents", 
        type=['txt', 'pdf', 'docx', 'doc', 'rtf', 'odt'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"📄 Processing document: {uploaded_file.name}")
            
            try:
                # Extract text using streamlit-document-ai
                text_content = process_document(uploaded_file)
                
                if text_content and text_content.strip():
                    # Create a unique key for this document
                    doc_key = f"{uploaded_file.name}_{hash(text_content)}"
                    
                    # Show text content in expander
                    with st.expander(f"📝 View Content: {uploaded_file.name}"):
                        st.text_area("Original Text", text_content, height=200)
                    
                    # Get analysis from Claude
                    with st.spinner(f"🔍 Analyzing {uploaded_file.name}..."):
                        analysis = analyze_with_claude(text_content)
                        if analysis:
                            st.subheader(f"📊 Analysis Results: {uploaded_file.name}")
                            
                            # Create tabs for this document
                            tab1, tab2 = st.tabs([f"Formatted Analysis - {uploaded_file.name}", 
                                                f"Raw Analysis - {uploaded_file.name}"])
                            
                            with tab1:
                                # Split analysis into sections and display with formatting
                                sections = analysis.split('\n')
                                current_section = ""
                                for section in sections:
                                    if any(header in section for header in ["NAMES:", "KEY INFORMATION:", 
                                                                          "DOCUMENT TYPE:", "DATES & NUMBERS:", 
                                                                          "RELATIONSHIPS:"]):
                                        st.markdown(f"**{section}**")
                                        current_section = section
                                    elif section.strip():
                                        st.write(section)
                            
                            with tab2:
                                st.text_area("Full Analysis", analysis, height=300)
                            
                            # Save analysis to session state
                            st.session_state['analyses'][doc_key] = {
                                'name': uploaded_file.name,
                                'content': text_content,
                                'analysis': analysis
                            }
                else:
                    st.error(f"❗ Could not extract text from {uploaded_file.name}")
                    
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
    
    # Display saved analyses
    if st.session_state['analyses']:
        st.subheader("📋 Saved Analyses")
        for doc_key, doc_data in st.session_state['analyses'].items():
            with st.expander(f"View Analysis: {doc_data['name']}"):
                st.write(doc_data['analysis'])
                if st.button(f"Remove Analysis for {doc_data['name']}", key=f"remove_{doc_key}"):
                    del st.session_state['analyses'][doc_key]
                    st.rerun()

if __name__ == "__main__":
    main()
