import streamlit as st
import requests
import docx
import PyPDF2
import io

# Get API key from Streamlit secrets
CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]

def extract_text_from_docx(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def extract_text_from_pdf(file_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = []
    for page in pdf_reader.pages:
        text.append(page.extract_text())
    return '\n'.join(text)

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
    
    uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'docx'])
    
    if uploaded_file:
        st.write("Analyzing document:", uploaded_file.name)
        
        # Extract text based on file type
        try:
            file_bytes = uploaded_file.read()
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(file_bytes)
            else:  # docx
                text = extract_text_from_docx(file_bytes)
            
            if text.strip():
                # Get analysis from Claude
                with st.spinner("Getting analysis from Claude..."):
                    analysis = analyze_with_claude(text)
                    if analysis:
                        st.subheader("Analysis Results")
                        st.write(analysis)
                        
                        # Show extracted text in expander
                        with st.expander("View Extracted Text"):
                            st.text(text)
            else:
                st.error("No text could be extracted from the document")
                
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")

if __name__ == "__main__":
    main()
