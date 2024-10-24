import streamlit as st
import requests

def analyze_with_claude(file_content, filename, api_key):
    """
    Sends the file content to Claude API for analysis.
    """
    # Prepare the API request body
    data = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": f"The document named {filename} has been uploaded. Here is the content:\n\n{file_content}\n\n"
                           "Please analyze this document."
            }
        ],
        "max_tokens": 500  # Adjust token limit based on response size needed
    }

    # API request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    # Send the POST request to Claude API
    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)

    # Check for successful response
    if response.status_code == 200:
        return response.json()['messages'][0]['content']
    else:
        return f"API Error {response.status_code}: {response.text}"

# Streamlit app logic
st.title("Document Analyzer with Claude")

# Input API key
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = st.text_input("Enter your Claude API key:", type="password")

# Upload a text file
uploaded_file = st.file_uploader("Upload a .txt document", type=["txt"])

if uploaded_file:
    # Read the content of the uploaded file
    file_content = uploaded_file.read().decode('utf-8', errors='ignore')  # Decode the text content

    # Analyze the file using Claude API if "Analyze" button is clicked
    if st.button("Analyze"):
        result = analyze_with_claude(file_content, uploaded_file.name, st.session_state['api_key'])
        
        # Display the analysis result
        st.write("Analysis Result:")
        st.write(result)
