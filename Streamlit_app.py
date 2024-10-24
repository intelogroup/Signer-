import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Initialize session state for login, documents, history, etc.
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'documents' not in st.session_state:
    st.session_state['documents'] = []

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'doc_id_counter' not in st.session_state:
    st.session_state['doc_id_counter'] = 1

if 'document_removal_times' not in st.session_state:
    st.session_state['document_removal_times'] = {}

if 'action_times' not in st.session_state:
    st.session_state['action_times'] = []  # To store (upload_time, action_time) pairs

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
def check_expired_documents():
    current_time = datetime.now()
    for doc_id, expiration_time in list(st.session_state['document_removal_times'].items()):
        if current_time > expiration_time:
            st.session_state['documents'] = [doc for doc in st.session_state['documents'] if doc['ID'] != doc_id]
            del st.session_state['document_removal_times'][doc_id]

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
    # Check and remove expired documents
    check_expired_documents()

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
            upload_time = datetime.now()

            # Add document to the list
            st.session_state['documents'].append({
                'Document Name': uploaded_file.name,
                'ID': doc_id,
                'Status': 'Pending',
                'Date': upload_time
            })

        st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")

    # Display documents (only pending ones) and allow action
    st.header("Document Status")
    pending_documents = [doc for doc in st.session_state['documents'] if doc['Status'] == 'Pending']
    
    if pending_documents:
        for doc in pending_documents:
            st.write(f"Document: {doc['Document Name']} | Status: {doc['Status']}")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Accept {doc['ID']}"):
                    doc['Status'] = "Authorized"
                    action_time = datetime.now()
                    st.session_state['history'].append({
                        'Date': action_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'ID': doc['ID'],
                        'Document Name': doc['Document Name'],
                        'Status': doc['Status']
                    })
                    # Store the time taken to sign
                    st.session_state['action_times'].append((doc['Date'], action_time))
                    # Set a timer for document removal (1 minute from now)
                    st.session_state['document_removal_times'][doc['ID']] = datetime.now() + timedelta(seconds=60)

            with col2:
                if st.button(f"Reject {doc['ID']}"):
                    doc['Status'] = "Rejected"
                    action_time = datetime.now()
                    st.session_state['history'].append({
                        'Date': action_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'ID': doc['ID'],
                        'Document Name': doc['Document Name'],
                        'Status': doc['Status']
                    })
                    # Store the time taken to sign
                    st.session_state['action_times'].append((doc['Date'], action_time))
                    # Set a timer for document removal (1 minute from now)
                    st.session_state['document_removal_times'][doc['ID']] = datetime.now() + timedelta(seconds=60)

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

    # --- Analytics Section ---
    st.header("Analytics and Activity Tracking")

    # A. Analytics 1: Number of Approved and Rejected Documents
    if st.session_state['history']:
        df_history = pd.DataFrame(st.session_state['history'])
        approved_count = len(df_history[df_history['Status'] == 'Authorized'])
        rejected_count = len(df_history[df_history['Status'] == 'Rejected'])

        # Bar chart for approved/rejected documents
        st.subheader("Document Approval/Reject Overview")
        fig, ax = plt.subplots()
        ax.bar(["Approved", "Rejected"], [approved_count, rejected_count], color=["green", "red"])
        ax.set_ylabel('Number of Documents')
        ax.set_title('Document Approval/Reject Status')
        st.pyplot(fig)

    # B. Analytics 2: Average time to sign documents
    if st.session_state['action_times']:
        time_diffs = [(action - upload).total_seconds() for upload, action in st.session_state['action_times']]
        average_time = sum(time_diffs) / len(time_diffs)

        st.subheader(f"Average Time to Sign Documents: {average_time:.2f} seconds")

    # C. Summary: Total number of documents uploaded
    total_documents = len(st.session_state['documents'])
    st.subheader(f"Total Documents Uploaded: {total_documents}")
