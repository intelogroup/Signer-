import streamlit as st
from datetime import datetime

# Initialize session state for login, documents, etc.
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'documents' not in st.session_state:
    st.session_state['documents'] = []

# Authentication function
def login_user(email, password):
    users = {"admin@example.com": "admin123", "assistant@example.com": "assist456"}
    if email in users and users[email] == password:
        return True
    return False

# Logout function
def logout():
    st.session_state['logged_in'] = False

# Simple styling using emojis for profile icon
st.markdown(
    """
    <style>
    .persona-icon {
        font-size: 30px;
        cursor: pointer;
    }
    .dropdown-menu {
        padding: 10px;
        margin-top: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        background-color: #f8f8f8;
    }
    </style>
    """, unsafe_allow_html=True
)

# User profile dropdown
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

    # Hero Section with description and image
    st.title("Signer")
    st.write("A solution for traveling managers")
    st.image("https://img.icons8.com/external-flat-juicy-fish/64/ffffff/external-stamp-marketing-flat-flat-juicy-fish.png", width=120)

    # File Upload Section
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'pdf', 'docx'])

    if uploaded_file is not None:
        # Generate document ID and date
        doc_id = f"signer{len(st.session_state['documents']) + 1:03}"
        date_time = datetime.now().strftime("%Y%m%d%H%M%S")

        # Add document to the list
        st.session_state['documents'].append({
            'Document Name': uploaded_file.name,
            'ID': doc_id,
            'Status': 'Pending',
            'Date': date_time
        })

        st.success(f"Document '{uploaded_file.name}' uploaded successfully!")

    # Display documents and allow action
    if st.session_state['documents']:
        st.header("Document Status")
        for doc in st.session_state['documents']:
            st.write(f"Document: {doc['Document Name']} | Status: {doc['Status']}")
            # Action buttons to accept or reject the document
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Accept {doc['ID']}"):
                    doc['Status'] = "Authorized"
                    st.success(f"Document {doc['Document Name']} has been authorized.")
            with col2:
                if st.button(f"Reject {doc['ID']}"):
                    doc['Status'] = "Rejected"
                    st.error(f"Document {doc['Document Name']} has been rejected.")
