import streamlit as st
import requests

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def read_file_content(uploaded_file):
    """Read content from uploaded file"""
    try:
        content = uploaded_file.read()
        return content.decode('utf-8')
    except UnicodeDecodeError:
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

# Initialize session state
if 'analyses' not in st.session_state:
    st.session_state['analyses'] = {}

st.title("Multi-Document Content Analyzer 📄")

# File upload section
uploaded_files = st.file_uploader(
    "Upload documents", 
    type=['txt', 'csv', 'json', 'md'],
    accept_multiple_files=True
)

if uploaded_files:
    # Process new files
    for uploaded_file in uploaded_files:
        st.write(f"📄 Processing: {uploaded_file.name}")
        
        try:
            # Read file content
            text_content = read_file_content(uploaded_file)
            
            if text_content and text_content.strip():
                # Show content
                st.text_area(f"Content of {uploaded_file.name}", text_content, height=150)
                
                # Analyze button for each file
                if st.button(f"Analyze {uploaded_file.name}"):
                    with st.spinner("Analyzing..."):
                        analysis = analyze_with_claude(text_content)
                        if analysis:
                            # Store in session state
                            st.session_state['analyses'][uploaded_file.name] = {
                                'content': text_content,
                                'analysis': analysis
                            }
                            st.success(f"Analysis completed for {uploaded_file.name}")
                            st.rerun()
                
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")

# Display analyses section
if st.session_state['analyses']:
    st.header("📋 Analyses")
    
    # Create tabs for each analysis
    analysis_names = list(st.session_state['analyses'].keys())
    if analysis_names:
        tabs = st.tabs(analysis_names)
        
        for tab, name in zip(tabs, analysis_names):
            with tab:
                analysis_data = st.session_state['analyses'][name]
                
                # Display formatted analysis
                st.subheader("Analysis Results")
                sections = analysis_data['analysis'].split('\n')
                for section in sections:
                    if any(header in section for header in [
                        "NAMES:", "KEY INFORMATION:", 
                        "DOCUMENT TYPE:", "DATES & NUMBERS:", 
                        "RELATIONSHIPS:"
                    ]):
                        st.markdown(f"**{section}**")
                    elif section.strip():
                        st.write(section)
                
                # Remove analysis button
                if st.button(f"Remove Analysis", key=f"remove_{name}"):
                    del st.session_state['analyses'][name]
                    st.rerun()

# Clear all button
if st.session_state['analyses']:
    if st.button("Clear All Analyses"):
        st.session_state['analyses'] = {}
        st.rerun()
