import streamlit as st
import requests

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def analyze_with_claude(text, filename):
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

Document name: {filename}

Document content to analyze:

{text}"""
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": prompt.format(text=text, filename=filename)}
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
    st.title("Multi-Document Text Analyzer 📄")
    
    # Initialize session state for analyses
    if 'analyses' not in st.session_state:
        st.session_state['analyses'] = {}
    
    # File upload - multiple text files
    uploaded_files = st.file_uploader(
        "Upload text documents", 
        type=['txt'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Process each file
        for uploaded_file in uploaded_files:
            try:
                # Read text content
                text_content = uploaded_file.getvalue().decode('utf-8')
                
                if text_content and text_content.strip():
                    # Create an expander for each document
                    with st.expander(f"📄 Document: {uploaded_file.name}"):
                        # Show original content
                        st.subheader("Original Content")
                        st.text_area("Text Content", text_content, height=150)
                        
                        # Analyze with Claude
                        if st.button(f"🔍 Analyze {uploaded_file.name}", key=f"analyze_{uploaded_file.name}"):
                            with st.spinner("Analyzing..."):
                                analysis = analyze_with_claude(text_content, uploaded_file.name)
                                if analysis:
                                    st.session_state['analyses'][uploaded_file.name] = analysis
                                    
                                    # Display analysis
                                    st.subheader("Analysis Results")
                                    tab1, tab2 = st.tabs(["Formatted", "Raw"])
                                    
                                    with tab1:
                                        sections = analysis.split('\n')
                                        for section in sections:
                                            if any(header in section for header in ["NAMES:", "KEY INFORMATION:", "DOCUMENT TYPE:", "DATES & NUMBERS:", "RELATIONSHIPS:"]):
                                                st.markdown(f"**{section}**")
                                            elif section.strip():
                                                st.write(section)
                                    
                                    with tab2:
                                        st.text_area("Full Analysis", analysis, height=200)
                else:
                    st.error(f"❌ The file {uploaded_file.name} is empty")
                    
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
    
    # View saved analyses
    if st.session_state['analyses']:
        st.sidebar.title("📋 Saved Analyses")
        for filename, analysis in st.session_state['analyses'].items():
            if st.sidebar.checkbox(f"Show analysis for {filename}"):
                st.sidebar.text_area(f"Analysis of {filename}", analysis, height=300)

if __name__ == "__main__":
    main()
