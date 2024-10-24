import streamlit as st
import os
from PIL import Image
from io import BytesIO
import subprocess

# Predefined user credentials (for MVP, hardcoded users)
users = {
    "admin@example.com": "admin123",
    "assistant@example.com": "assist456"
}

# Set up app title
st.title("Document Review & Approval System")

# Authentication functions
def login_user(email, password):
    if email in users and users[email] == password:
        return True
    else:
        return False

# Logout function
def logout():
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
        del st.session_state['email']

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# User login
if not st.session_state['logged_in']:
    # User login form
    st.subheader("Login to access")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(email, password):
            st.session_state['logged_in'] = True
            st.session_state['email'] = email
            st.success("Login successful!")
        else:
            st.error("Invalid email or password")

else:
    # Logout button
    if st.button("Logout"):
        logout()
        st.success("Logged out successfully!")
        st.stop()  # Stop the app execution to refresh the login state

    # Main app logic once logged in
    st.header(f"Welcome, {st.session_state['email']}!")

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
