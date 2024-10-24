import streamlit as st
import requests
from PyPDF2 import PdfReader
from docx import Document

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ''.join([page.extract_text() for page in reader.pages])
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

# Function to analyze document content using the Claude API
def analyze_with_claude(file, filename, file_type, api_key):
    # Extract the document text based on the file type
    if file_type == 'pdf':
        file_content = extract_text_from_pdf(file)
    elif file_type == 'docx':
        file_content = extract_text_from_docx(file)
    else:
        file_content = file.read().decode('utf-8', errors='ignore')  # For text files

    # Define the request body for the Claude API
    data = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": f"The document named {filename} has been uploaded. Here is the content:\n\n{file_content}\n\n"
                           "Please analyze this document."
            }
        ],
        "max_tokens": 500  # Adjust the token limit based on expected response length
    }

    # Define the necessary headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    # Send the request to Claude API
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=data
    )

    # Check the API response
    if response.status_code == 200:
        return response.json()['messages'][0]['content']
    else:
        return f"API Error {response.status_code}: {response.text}"

# Streamlit UI
st.title("Document Analyzer with Claude")

# Input for API Key
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = st.text_input("Enter your Claude API key:", type="password")

# File uploader
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]  # Detect file type by extension
    if st.button("Analyze"):
        result = analyze_with_claude(uploaded_file, uploaded_file.name, file_type, st.session_state['api_key'])
        st.write("Analysis Result:")
        st.write(result)
