import streamlit as st
import requests

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def extract_text_content(uploaded_file):
    """Attempt to extract text content from uploaded file"""
    try:
        # Try to decode as text
        content = uploaded_file.read()
        try:
            # First try utf-8
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # If utf-8 fails, try latin-1 as fallback
            return content.decode('latin-1')
    except Exception as e:
        st.warning(f"Note: File content might not be perfectly extracted. Proceeding with best effort.")
        return str(content)  # Return as string representation if all else fails

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
    st.title("📄 Universal Document Analyzer")
    
    # File upload - now accepts any file type
    uploaded_file = st.file_uploader("Upload any document", type=None)
    
    if uploaded_file:
        st.write("📄 Analyzing:", uploaded_file.name)
        file_details = {
            "Filename": uploaded_file.name,
            "File type": uploaded_file.type,
            "File size": f"{uploaded_file.size / 1024:.2f} KB"
        }
        
        # Display file details in expander
        with st.expander("📌 File Details"):
            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")
        
        try:
            # Extract text content
            text_content = extract_text_content(uploaded_file)
            
            if text_content.strip():
                # Show text content in expander
                with st.expander("📝 View Extracted Content"):
                    st.text_area("Content Preview", text_content[:5000] + ("..." if len(text_content) > 5000 else ""), 
                                height=200)
                
                # Get analysis from Claude
                with st.spinner("🔍 Analyzing document..."):
                    analysis = analyze_with_claude(text_content)
                    if analysis:
                        st.subheader("📊 Analysis Results")
                        
                        tab1, tab2 = st.tabs(["Formatted Analysis", "Raw Analysis"])
                        
                        with tab1:
                            sections = analysis.split('\n')
                            current_section = ""
                            for section in sections:
                                if any(header in section for header in ["NAMES:", "KEY INFORMATION:", "DOCUMENT TYPE:", 
                                                                      "DATES & NUMBERS:", "RELATIONSHIPS:", "SUMMARY:"]):
                                    st.markdown(f"### {section}")
                                    current_section = section
                                elif section.strip():
                                    st.write(section)
                        
                        with tab2:
                            st.text_area("Full Analysis", analysis, height=300)
                        
                        # Save analysis
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
