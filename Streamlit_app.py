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
        
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": f"Analyze this document content. Focus on key information and names:\n\n{text}"}
            ],
            "max_tokens": 500
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
    st.title("Document Content Analyzer 📄")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a text file", type=['txt'])
    
    if uploaded_file:
        st.write("Analyzing document:", uploaded_file.name)
        
        try:
            # Read text content
            text_content = uploaded_file.getvalue().decode('utf-8')
            
            if text_content.strip():
                # Show text content in expander
                with st.expander("View Document Content"):
                    st.text(text_content)
                
                # Get analysis from Claude
                with st.spinner("Getting analysis from Claude..."):
                    analysis = analyze_with_claude(text_content)
                    if analysis:
                        st.subheader("Analysis Results")
                        st.write(analysis)
                        
                        # Option to save analysis
                        if st.button("Save Analysis"):
                            st.session_state['last_analysis'] = analysis
                            st.success("Analysis saved!")
            else:
                st.error("The uploaded file is empty")
                
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")
    
    # Display saved analysis if it exists
    if 'last_analysis' in st.session_state:
        with st.expander("View Last Saved Analysis"):
            st.write(st.session_state['last_analysis'])

if __name__ == "__main__":
    main()
