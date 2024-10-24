import streamlit as st
import requests

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
            "max_tokens": 1000,  # Increased token limit for more detailed analysis
            "temperature": 0.1    # Lower temperature for more focused, factual responses
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
    st.title("Enhanced Document Content Analyzer 📄")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a text file", type=['txt'])
    
    if uploaded_file:
        st.write("📄 Analyzing document:", uploaded_file.name)
        
        try:
            # Read text content
            text_content = uploaded_file.getvalue().decode('utf-8')
            
            if text_content.strip():
                # Show text content in expander
                with st.expander("📝 View Document Content"):
                    st.text_area("Original Text", text_content, height=200)
                
                # Get analysis from Claude
                with st.spinner("🔍 Analyzing document content..."):
                    analysis = analyze_with_claude(text_content)
                    if analysis:
                        st.subheader("📊 Analysis Results")
                        # Create tabs for better organization
                        tab1, tab2 = st.tabs(["Formatted Analysis", "Raw Analysis"])
                        
                        with tab1:
                            # Split analysis into sections and display with formatting
                            sections = analysis.split('\n')
                            current_section = ""
                            for section in sections:
                                if any(header in section for header in ["NAMES:", "KEY INFORMATION:", "DOCUMENT TYPE:", "DATES & NUMBERS:", "RELATIONSHIPS:"]):
                                    st.markdown(f"**{section}**")
                                    current_section = section
                                elif section.strip():
                                    st.write(section)
                        
                        with tab2:
                            st.text_area("Full Analysis", analysis, height=300)
                        
                        # Option to save analysis
                        if st.button("💾 Save Analysis"):
                            st.session_state['last_analysis'] = analysis
                            st.success("✅ Analysis saved successfully!")
            else:
                st.error("❗ The uploaded file is empty")
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")
    
    # Display saved analysis if it exists
    if 'last_analysis' in st.session_state:
        with st.expander("📋 View Last Saved Analysis"):
            st.write(st.session_state['last_analysis'])

if __name__ == "__main__":
    main()
