import streamlit as st
from datetime import datetime, timedelta
import time
import threading

# Initialize session state for login, documents, history, etc.
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'documents' not in st.session_state:
    st.session_state['documents'] = []

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'doc_id_counter' not in st.session_state:
    st.session_state['doc_id_counter'] = 1

# Authentication function
def login_user(email, password):
    users = {"admin@example.com": "admin123", "assistant@example.com": "assist456"}
    if email in users and users[email] == password:
        return True
    return False

# Logout function
def logout():
    st.session_state['logged_in'] = False

# Function to handle document expiration after 1 minute
def expire_document(doc_id):
    time.sleep(60)  # Wait 1 minute before expiring document
    st.session_state['documents'] = [doc for doc in st.session_state['documents'] if doc['ID'] != doc_id]
    st.experimental_rerun()  # Manually refresh to remove document

# Profile menu
def profile_menu():
    st.markdown("<div class='dropdown-menu'>", unsafe_allow_html=True)
    if st.button("My Profile"):
        st.info("My Profile page is under development.")
    if st.button("Contact Developer"):
        st.info("Contact Developer: Email example@example.com.")
    if st.button("About Us"):
        st.info("We provide solutions for managers on the go.")
    if st.button("Logout"):
        logout()
        st.success("Logged out successfully!")
        st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# Login form
if not st.session_state['logged_in']:
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            st.session_state['logged_in'] = True
            st.success("Login successful!")
        else:
            st.error("Invalid email or password")
else:
    # Persona Icon (profile dropdown)
    st.markdown("<span class='persona-icon'>👤</span>", unsafe_allow_html=True)
    if st.button("Show Profile Menu"):
        profile_menu()

    # Hero Section
    st.title("Signer ✒️")
    st.write("A solution for traveling managers")

    # File Upload Section (multiple file uploads)
    st.header("Upload Document(s)")
    uploaded_files = st.file_uploader("Choose files", type=['png', 'jpg', 'pdf', 'docx'], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Generate document ID and date
            doc_id = f"signer{st.session_state['doc_id_counter']:03}"
            st.session_state['doc_id_counter'] += 1
            date_time = datetime.now().strftime("%Y%m%d%H%M%S")

            # Add document to the list
            st.session_state['documents'].append({
                'Document Name': uploaded_file.name,
                'ID': doc_id,
                'Status': 'Pending',
                'Date': date_time
            })

        st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")

    # Display documents and allow action
    if st.session_state['documents']:
        st.header("Document Status")
        for doc in st.session_state['documents']:
            st.write(f"Document: {doc['Document Name']} | Status: {doc['Status']}")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Accept {doc['ID']}"):
                    doc['Status'] = "Authorized"
                    st.session_state['history'].append({
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'ID': doc['ID'],
                        'Document Name': doc['Document Name'],
                        'Status': doc['Status']
                    })
                    # Start the timer for document expiration in a new thread
                    threading.Thread(target=expire_document, args=(doc['ID'],)).start()
                    st.experimental_rerun()

            with col2:
                if st.button(f"Reject {doc['ID']}"):
                    doc['Status'] = "Rejected"
                    st.session_state['history'].append({
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'ID': doc['ID'],
                        'Document Name': doc['Document Name'],
                        'Status': doc['Status']
                    })
                    # Start the timer for document expiration in a new thread
                    threading.Thread(target=expire_document, args=(doc['ID'],)).start()
                    st.experimental_rerun()

    # History of Signing Section
    st.header("History of Signing")
    if st.session_state['history']:
        st.write("Here are the documents that have been signed or rejected:")
        # Create a table for history
        history_data = st.session_state['history'][::-1]  # Reverse to show latest first
        st.table([{
            'Date': doc['Date'],
            'ID': doc['ID'],
            'Document Name': doc['Document Name'],
            'Status': doc['Status']
        } for doc in history_data])
