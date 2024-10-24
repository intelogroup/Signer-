import requests
import streamlit as st

def analyze_with_claude(filename, file_type):
    """
    Analyzes a document using the Claude API, sending a request with the document's filename and type, and returns a response.
    Includes error handling and user prompts.
    """
    try:
        # Ensure API key is present
        if not st.session_state.get('api_key'):
            st.error("Please enter your Claude API key first")
            return None

        # Define the necessary headers, including the correct 'anthropic-version' header
        headers = {
            "x-api-key": st.session_state['api_key'],
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"  # Correct version for the Claude API
        }

        # Define the request body for Claude API
        data = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {
                    "role": "user",
                    "content": f"A document named {filename} of type {file_type} has been uploaded for review. "
                               "Please provide:\n1. Brief acknowledgment of the document type.\n"
                               "2. Note to check for any mention of Kalinov Jim Rozensky DAMEUS.\n"
                               "3. Standard processing recommendations."
                }
            ],
            "max_tokens": 500  # Setting the maximum number of tokens for the response
        }

        # Send the POST request to Claude API
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )

        # Process the API response
        if response.status_code == 200:
            result = response.json()

            # Check if the response contains content and handle it
            if 'content' in result and len(result['content']) > 0:
                return result['content'][0]['text']

        # Handle errors by providing detailed feedback
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None

    # Catch and display any exceptions that occur during the API request
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None


# Example usage with Streamlit
st.title("Document Analyzer with Claude")

# Add input fields for the API key, filename, and file type
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ""

st.session_state['api_key'] = st.text_input("Enter your Claude API key:", type="password")

# Document upload logic (Streamlit allows file uploading)
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])

# Optional: Detect file type based on the file extension
if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]  # Get file extension
    st.write(f"Uploaded file: {uploaded_file.name} of type {file_type}")

    # Trigger the analysis when the "Analyze" button is clicked
    if st.button("Analyze"):
        result = analyze_with_claude(uploaded_file.name, file_type)
        if result:
            st.write("Analysis Result:")
            st.write(result)
