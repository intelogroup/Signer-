import streamlit as st
import requests
import PyPDF2
import docx
import io
import pandas as pd

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in pdf_reader.pages:
            text.append(page.extract_text())
        return '\n'.join(text)
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return None

def extract_text_from_file(uploaded_file):
    try:
        # Get the file bytes
        file_bytes = uploaded_file.getvalue()
        
        # Extract text based on file type
        if uploaded_file.type == "application/pdf":
            return extract_text_from_pdf(file_bytes)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(file_bytes)
        elif uploaded_file.type == "text/plain":
            return file_bytes.decode('utf-8')
        else:
            st.error(f"Unsupported file type: {uploaded_file.type}")
            return None
    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")
        return None

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
    st.title("Multi-Document Content Analyzer 📄")
    
    # Initialize session state for analyses
    if 'analyses' not in st.session_state:
        st.session_state['analyses'] = {}
    
    # File upload - now accepts multiple files
    uploaded_files = st.file_uploader(
        "Upload documents", 
        type=['txt', 'pdf', 'docx'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Create a container for the progress bar
        progress_container = st.empty()
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files):
            # Update progress
            progress = (i + 1) / len(uploaded_files)
            progress_container.progress(progress, f"Processing {uploaded_file.name}")
            
            try:
                # Extract text content
                text_content = extract_text_from_file(uploaded_file)
                
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
                    st.error(f"❌ Could not extract text from {uploaded_file.name}")
                    
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        
        # Clear progress bar after completion
        progress_container.empty()
    
    # View saved analyses
    if st.session_state['analyses']:
        st.sidebar.title("📋 Saved Analyses")
        for filename, analysis in st.session_state['analyses'].items():
            if st.sidebar.checkbox(f"Show analysis for {filename}"):
                st.sidebar.text_area(f"Analysis of {filename}", analysis, height=300)

if __name__ == "__main__":
    main()
