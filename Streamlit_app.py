import streamlit as st
import os
from PIL import Image
from io import BytesIO
import subprocess

# Set up app title
st.title("Document Review & Approval System")

# Define the upload folder
UPLOAD_FOLDER = './uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Assistant: Upload a document
st.header("Upload Document")
uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'pdf', 'docx'])

if uploaded_file is not None:
    # Save the uploaded file to the uploads directory
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    st.write(f"File saved to: {file_path}")
    
    # If it's an image, display the preview
    if uploaded_file.type.startswith('image/'):
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    # Admin: Review and Approve
    st.header("Admin Review")
    approve = st.button("Approve and Apply Stamp")

    if approve:
        # Simulate applying a stamp (example with bash)
        if uploaded_file.type.startswith('image/'):
            # Example of using external bash command on images
            stamp_command = f"echo 'Stamp applied to {file_path}'"
            result = subprocess.run(stamp_command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                st.success(f"Document approved. {result.stdout}")
            else:
                st.error(f"Error: {result.stderr}")
        else:
            st.info(f"Approval logic for {uploaded_file.type} to be added.")
else:
    st.info("Upload a document to start the review process.")

# Additional CSS Styling
st.markdown("""
<style>
    h1 {
        color: #4CAF50;
        font-size: 32px;
    }
    .stButton button {
        background-color: #28a745;
        color: white;
        border: none;
        padding: 10px;
        cursor: pointer;
    }
    .stButton button:hover {
        background-color: #218838;
    }
</style>
""", unsafe_allow_html=True)
