import streamlit as st
import requests
import re

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def clean_rtf_content(text):
    """Clean RTF content by removing control sequences and formatting"""
    # Remove RTF control sequences
    text = re.sub(r'\\[a-z]{1,32}[-]{0,1}[0-9]*[ ]{0,1}', ' ', text)
    # Remove special characters and other RTF syntax
    text = re.sub(r'[{}\\]', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove font table and color table
    text = re.sub(r'{\*?\\[^{}]+}|{[^{}]+}', '', text)
    # Split into lines and clean
    lines = [line.strip() for line in text.split('\\par') if line.strip()]
    return '\n'.join(lines)

def format_content_preview(file, content):
    """Format content based on file type"""
    file_type = file.type if file.type else file.name.split('.')[-1].lower()
    
    try:
        if 'rtf' in file_type:
            cleaned_content = clean_rtf_content(content)
            return cleaned_content
        
        elif any(ext in file_type for ext in ['pdf', 'docx', 'doc', 'txt']):
            # Basic cleaning for other document types
            # Remove excessive whitespace and empty lines
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('\\') and not line.startswith('{'):
                    # Remove common control characters and noise
                    line = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', line)
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        else:
            # For unknown file types, do basic cleaning
            return re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)
            
    except Exception as e:
        return f"Note: Content preview might contain formatting artifacts.\n\n{content}"

def extract_text_content(uploaded_file):
    """Extract and decode file content"""
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
6. SUMMARY: Provide a brief summary of the document's main purpose

Please be precise and factual. If you're uncertain about any information, indicate that explicitly.

Document content to analyze:

{text}"""
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": prompt.format(text=text)}
            ],
            "max_tokens": 500,
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
    st.title("📄 Universal Document Analyzer")
    
    # File upload section with supported formats
    st.markdown("""
    ### Upload Document
    Supported formats: PDF, DOCX, RTF, TXT, and more
    """)
    
    uploaded_file = st.file_uploader("Choose a file", type=None)
    
    if uploaded_file:
        st.write("📄 Analyzing:", uploaded_file.name)
        
        # File details in a neat format
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col2:
            st.metric("File Type", uploaded_file.type if uploaded_file.type else uploaded_file.name.split('.')[-1].upper())
        
        try:
            # Extract and format content
            text_content = extract_text_content(uploaded_file)
            formatted_content = format_content_preview(uploaded_file, text_content)
            
            if formatted_content.strip():
                # Show formatted content in expander
                with st.expander("📝 Document Content"):
                    st.markdown("### Document Preview")
                    # Create a clean, formatted preview
                    st.markdown("""---""")
                    st.markdown(formatted_content[:5000] + ("..." if len(formatted_content) > 5000 else ""))
                    st.markdown("""---""")
                    if len(formatted_content) > 5000:
                        st.info("⚠️ Preview truncated for better performance")
                
                # Get analysis from Claude
                with st.spinner("🔍 Analyzing document..."):
                    analysis = analyze_with_claude(formatted_content)
                    if analysis:
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
                        
                        if st.button("💾 Save Analysis"):
                            st.session_state['last_analysis'] = {
                                'filename': uploaded_file.name,
                                'analysis': analysis,
                                'timestamp': str(pd.Timestamp.now())
                            }
                            st.success("✅ Analysis saved!")
            else:
                st.error("❗ No readable content found in the file")
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")
    
    # Display saved analysis if it exists
    if 'last_analysis' in st.session_state:
        with st.expander("📋 Previous Analysis"):
            saved = st.session_state['last_analysis']
            st.write(f"File: {saved['filename']}")
            st.write(f"Analyzed: {saved['timestamp']}")
            st.write(saved['analysis'])

if __name__ == "__main__":
    main()
