"""
Streamlit frontend for Multi-Tenant RAG System
A simple, detachable frontend interface for testing the RAG system
"""
import streamlit as st
import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import io

# Configuration
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

    # Page configuration
st.set_page_config(
    page_title="Multi-Tenant RAG System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
/* Main layout improvements */
.main > div {
    padding-top: 2rem;
}
.stAlert {
    margin-top: 1rem;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #1e2937;
}

/* Section headers in sidebar */
.sidebar-section {
    color: #f9fafb;
    padding: 8px 0;
    margin: 20px 0 10px 0;
    font-weight: 600;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid #4b5563;
}

/* User and organization info styling */
.info-card {
    background-color: #374151;
    border: 1px solid #4b5563;
    border-radius: 8px;
    padding: 16px;
    margin: 10px 0;
    color: #f3f4f6;
}

.info-label {
    color: #9ca3af;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.info-value {
    color: #f9fafb;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 12px;
}

/* Navigation styling */
.nav-container {
    padding: 10px 0;
    margin: 15px 0;
}

/* Navigation buttons */
.nav-button {
    margin: 5px 0;
}

.nav-button button {
    width: 100%;
    background-color: #374151 !important;
    color: #f9fafb !important;
    border: 1px solid #4b5563 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    font-weight: 500 !important;
    text-align: left !important;
    transition: all 0.3s ease !important;
}

.nav-button button:hover {
    background-color: #4b5563 !important;
    border-color: #6b7280 !important;
    transform: translateX(4px) !important;
}

.nav-button.active button {
    background-color: #3b82f6 !important;
    border-color: #2563eb !important;
    color: white !important;
    font-weight: 600 !important;
}

/* Default button styling */
.stButton > button {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: #e5e7eb;
    border-color: #9ca3af;
}

/* Primary button styling */
.primary-button button {
    background-color: #3b82f6 !important;
    color: white !important;
    border: 1px solid #2563eb !important;
}

.primary-button button:hover {
    background-color: #2563eb !important;
    border-color: #1d4ed8 !important;
}

/* Form submit button styling */
.stForm button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 28px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}

.stForm button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
}

.stForm button[kind="secondary"], .stForm button:not([kind]) {
    background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 28px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3) !important;
}

.stForm button[kind="secondary"]:hover, .stForm button:not([kind]):hover {
    background: linear-gradient(135deg, #4b5563 0%, #374151 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(107, 114, 128, 0.4) !important;
}

/* Logout button special styling */
.logout-btn button {
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.logout-btn button:hover {
    background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%) !important;
    transform: translateY(-1px) !important;
}

/* Upload section */
.upload-section {
    border: 2px dashed #6366f1;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    text-align: center;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    transition: all 0.3s ease;
}

.upload-section:hover {
    border-color: #4f46e5;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

/* Query response styling */
.query-response {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    padding: 20px;
    border-radius: 12px;
    margin: 10px 0;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* Context documents styling */
.context-doc {
    background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
    color: #f7fafc;
    padding: 18px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 4px solid #3b82f6;
    border: 1px solid #4b5563;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.context-doc:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.context-doc strong {
    color: #60a5fa;
    font-weight: 600;
}

.context-doc em {
    color: #cbd5e1;
}

/* Metrics styling */
.metric-card {
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    padding: 16px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #d1d5db;
}

/* Radio button styling */
.stRadio > div {
    background-color: transparent;
}

/* Divider styling */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(to right, transparent, #4b5563, transparent);
    margin: 20px 0;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 16px;
    justify-content: center;
    margin-bottom: 32px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(55, 65, 81, 0.8);
    color: #d1d5db;
    border-radius: 12px;
    border: none;
    padding: 14px 28px;
    font-weight: 600;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
    outline: none;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(75, 85, 99, 0.9);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
}

.stTabs [aria-selected="true"] {
    background: #555555;
    color: white;
    transform: translateY(-1px);
}




/* Clean Form Container */
.stForm {
    background: rgba(31, 41, 55, 0.95);
    border: 1px solid rgba(55, 65, 81, 0.8);
    border-radius: 12px;
    padding: 28px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(8px);
}

/* Universal Input Styling - All Fields Same */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #374151 !important;
    border: 1px solid #4b5563 !important;
    border-radius: 8px !important;
    color: #f9fafb !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
    outline: none !important;
    width: 100% !important;
    box-sizing: border-box !important;
    height: 40px !important;
    line-height: 1.5 !important;
}

/* Focus States - All Fields Same */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    background-color: #374151 !important;
}

/* Hover States - All Fields Same */
.stTextInput > div > div > input:hover,
.stTextArea > div > div > textarea:hover,
.stSelectbox > div > div:hover {
    border-color: #6b7280 !important;
    background-color: #374151 !important;
}

/* Textarea Special Height */
.stTextArea > div > div > textarea {
    height: 80px !important;
    resize: vertical !important;
}

/* Selectbox Inner Content */
.stSelectbox > div > div > div {
    background: transparent !important;
    border: none !important;
    color: #f9fafb !important;
    padding: 0 !important;
    height: auto !important;
    line-height: inherit !important;
}

/* Labels Consistent */
.stTextInput label,
.stTextArea label,
.stSelectbox label {
    color: #d1d5db !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    margin-bottom: 6px !important;
}

/* Completely hide password reveal button */
.stTextInput button {
    display: none !important;
}

/* Container Uniformity */
.stTextInput,
.stTextArea,
.stSelectbox {
    margin-bottom: 16px !important;
}

.stTextInput > div,
.stTextArea > div,
.stSelectbox > div {
    width: 100% !important;
}

/* Dropdown Arrow */
.stSelectbox svg {
    color: #9ca3af !important;
}

/* Remove all default outlines */
* {
    outline: none !important;
}

*:focus {
    outline: none !important;
}
</style>
""", unsafe_allow_html=True)


class APIClient:
    """Simple API client for the RAG system"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def login(self, email: str, password: str, tenant_identifier: str = None) -> Dict:
        """Login user"""
        data = {
            "email": email,
            "password": password,
            "tenant_identifier": tenant_identifier
        }
        response = self.session.post(f"{self.base_url}/auth/login", json=data)
        response.raise_for_status()
        return response.json()
    
    def signup(self, organization_name: str, admin_email: str, admin_username: str, 
               admin_password: str, subdomain: str = None, llm_provider: str = "openai", 
               llm_model: str = "gpt-3.5-turbo") -> Dict:
        """Sign up for new organization"""
        data = {
            "organization_name": organization_name,
            "admin_email": admin_email,
            "admin_username": admin_username,
            "admin_password": admin_password,
            "subdomain": subdomain,
            "llm_provider": llm_provider,
            "llm_model": llm_model
        }
        response = self.session.post(f"{self.base_url}/auth/signup", json=data)
        response.raise_for_status()
        return response.json()
    
    def upload_document(self, file_data: bytes, filename: str, metadata: Dict = None) -> Dict:
        """Upload document"""
        files = {"file": (filename, io.BytesIO(file_data), "application/octet-stream")}
        data = {}
        if metadata:
            data["metadata"] = json.dumps(metadata)
        
        response = self.session.post(f"{self.base_url}/documents/upload", files=files, data=data)
        response.raise_for_status()
        return response.json()
    
    def list_documents(self, skip: int = 0, limit: int = 20) -> Dict:
        """List documents"""
        params = {"skip": skip, "limit": limit}
        response = self.session.get(f"{self.base_url}/documents/", params=params)
        response.raise_for_status()
        return response.json()
    
    def rag_query(self, query: str, max_chunks: int = 5, stream: bool = False, **kwargs) -> Dict:
        """Submit RAG query"""
        data = {
            "query": query,
            "max_chunks": max_chunks,
            "stream": stream,
            **kwargs
        }
        
        if stream:
            response = self.session.post(f"{self.base_url}/queries/rag/stream", json=data, stream=True)
        else:
            response = self.session.post(f"{self.base_url}/queries/rag", json=data)
        
        response.raise_for_status()
        return response.json() if not stream else response
    
    def debug_vector_status(self) -> Dict:
        """Check vector store status (debug)"""
        response = self.session.get(f"{self.base_url}/queries/debug/vector-status")
        response.raise_for_status()
        return response.json()
    
    def get_query_history(self, skip: int = 0, limit: int = 10) -> Dict:
        """Get query history"""
        params = {"skip": skip, "limit": limit}
        response = self.session.get(f"{self.base_url}/queries/history", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_tenant_info(self) -> Dict:
        """Get current tenant info"""
        response = self.session.get(f"{self.base_url}/tenant/info")
        response.raise_for_status()
        return response.json()


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(API_BASE_URL)
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    if "tenant_info" not in st.session_state:
        st.session_state.tenant_info = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def login_form():
    """Display login and signup forms"""
    st.title("Multi-Tenant RAG System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login to Your Account")
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="user@example.com")
                password = st.text_input("Password", type="password")
                tenant_identifier = st.text_input(
                    "Tenant ID or Subdomain (optional)", 
                    placeholder="my-company or tenant-uuid"
                )
                
                submit = st.form_submit_button("Login", use_container_width=True, type="secondary")
                
                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password")
                        return
                    
                    try:
                        with st.spinner("Logging in..."):
                            response = st.session_state.api_client.login(
                                email=email,
                                password=password,
                                tenant_identifier=tenant_identifier or None
                            )
                        
                        # Store authentication data
                        st.session_state.api_client.set_auth_token(response["access_token"])
                        st.session_state.authenticated = True
                        st.session_state.user_info = response["user"]
                        st.session_state.tenant_info = response["tenant"]
                        
                        st.success("Login successful!")
                        st.rerun()
                        
                    except requests.exceptions.RequestException as e:
                        if hasattr(e, 'response') and e.response is not None:
                            error_detail = e.response.json().get("detail", "Login failed")
                            st.error(f"Login failed: {error_detail}")
                        else:
                            st.error("Unable to connect to the server. Please check if the API is running.")
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
        
        with tab2:
            st.subheader("Create New Organization")
            st.info("Sign up to create a new organization and become its administrator.")
            
            with st.form("signup_form"):
                st.markdown("**Organization Information**")
                organization_name = st.text_input(
                    "Organization Name *", 
                    placeholder="Acme Corporation",
                    help="The name of your organization"
                )
                subdomain = st.text_input(
                    "Subdomain (optional)", 
                    placeholder="acme-corp",
                    help="Optional subdomain for your organization (lowercase, letters, numbers, and hyphens only)"
                )
                
                st.markdown("**Administrator Account**")
                admin_email = st.text_input(
                    "Admin Email *", 
                    placeholder="admin@acme.com",
                    help="This will be your login email"
                )
                admin_username = st.text_input(
                    "Admin Username *", 
                    placeholder="admin",
                    help="Your username (3-50 characters)"
                )
                admin_password = st.text_input(
                    "Admin Password *", 
                    type="password",
                    help="Must be at least 8 characters long"
                )
                confirm_password = st.text_input(
                    "Confirm Password *", 
                    type="password"
                )
                
                st.markdown("**AI Configuration**")
                col_a, col_b = st.columns(2)
                with col_a:
                    llm_provider = st.selectbox(
                        "LLM Provider", 
                        ["openai", "anthropic"],
                        help="Choose your preferred AI provider"
                    )
                with col_b:
                    if llm_provider == "openai":
                        llm_model = st.selectbox("Model", ["gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1"])
                    else:
                        llm_model = st.selectbox("Model", ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"])
                
                submit_signup = st.form_submit_button("Create Organization", use_container_width=True, type="primary")
                
                if submit_signup:
                    # Validation
                    if not organization_name or not admin_email or not admin_username or not admin_password:
                        st.error("Please fill in all required fields (marked with *)")
                        return
                    
                    if len(admin_password) < 8:
                        st.error("Password must be at least 8 characters long")
                        return
                    
                    if admin_password != confirm_password:
                        st.error("Passwords do not match")
                        return
                    
                    if len(admin_username) < 3 or len(admin_username) > 50:
                        st.error("Username must be between 3 and 50 characters")
                        return
                    
                    if subdomain and not subdomain.replace('-', '').replace('_', '').isalnum():
                        st.error("Subdomain can only contain letters, numbers, and hyphens")
                        return
                    
                    try:
                        with st.spinner("Creating your organization..."):
                            response = st.session_state.api_client.signup(
                                organization_name=organization_name,
                                admin_email=admin_email,
                                admin_username=admin_username,
                                admin_password=admin_password,
                                subdomain=subdomain if subdomain else None,
                                llm_provider=llm_provider,
                                llm_model=llm_model
                            )
                        
                        # Store authentication data (user is automatically logged in)
                        st.session_state.api_client.set_auth_token(response["access_token"])
                        st.session_state.authenticated = True
                        st.session_state.user_info = response["admin_user"]
                        st.session_state.tenant_info = response["tenant"]
                        
                        st.success(f"{response['message']} Welcome to your RAG system!")
                        st.rerun()
                        
                    except requests.exceptions.RequestException as e:
                        if hasattr(e, 'response') and e.response is not None:
                            error_detail = e.response.json().get("detail", "Signup failed")
                            st.error(f"Signup failed: {error_detail}")
                        else:
                            st.error("Unable to connect to the server. Please check if the API is running.")
                    except Exception as e:
                        st.error(f"Signup failed: {str(e)}")


def sidebar():
    """Display sidebar with user info and navigation"""
    with st.sidebar:
        if st.session_state.authenticated:
            # Initialize current page if not set
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "Chat"
            
            # User info section
            st.markdown('<div class="sidebar-section">User Information</div>', unsafe_allow_html=True)
            st.markdown(f'''
            <div class="info-card">
                <div class="info-label">Email</div>
                <div class="info-value">{st.session_state.user_info['email']}</div>
                <div class="info-label">Role</div>
                <div class="info-value">{st.session_state.user_info['role'].title()}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Organization info section
            st.markdown('<div class="sidebar-section">Organization</div>', unsafe_allow_html=True)
            tenant = st.session_state.tenant_info
            st.markdown(f'''
            <div class="info-card">
                <div class="info-label">Organization</div>
                <div class="info-value">{tenant['name']}</div>
                <div class="info-label">LLM Provider</div>
                <div class="info-value">{tenant['llm_provider'].upper()}</div>
                <div class="info-label">Model</div>
                <div class="info-value">{tenant['llm_model']}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Navigation section
            st.markdown('<div class="nav-container">', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
            
            # Navigation buttons
            pages = ["Chat", "Documents", "History"]
            for page in pages:
                is_active = st.session_state.current_page == page
                active_class = "active" if is_active else ""
                
                st.markdown(f'<div class="nav-button {active_class}">', unsafe_allow_html=True)
                if st.button(page, key=f"nav_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            

            
            return st.session_state.current_page
        
        return "Chat"  # Default page when not authenticated


def document_management():
    """Document management interface"""
    st.header("Document Management")
    
    # Upload section
    st.markdown("### Upload New Document")

    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=['pdf', 'txt', 'docx'],
        help="Supported formats: PDF, TXT, DOCX (Max 10MB)"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # Metadata input
        with st.expander("Document Metadata (Optional)"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title", value=uploaded_file.name)
                tags = st.text_input("Tags (comma-separated)", placeholder="finance, report, 2024")
            
            with col2:
                category = st.selectbox("Category", ["General", "Finance", "Legal", "Technical", "Other"])
                description = st.text_area("Description", placeholder="Brief description of the document")
        
        if st.button("Upload Document", type="primary"):
            try:
                # Prepare metadata
                metadata = {
                    "title": title,
                    "category": category,
                    "description": description,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()]
                }
                
                with st.spinner("Uploading document..."):
                    file_data = uploaded_file.read()
                    response = st.session_state.api_client.upload_document(
                        file_data=file_data,
                        filename=uploaded_file.name,
                        metadata=metadata
                    )
                
                st.success(f"Document uploaded successfully! ID: {response['id']}")
                st.info("Document is being processed in the background. It will be available for queries once processing is complete.")
                
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")
    
    st.markdown("---")
    
    # Document list
    st.markdown("### Your Documents")
    
    try:
        with st.spinner("Loading documents..."):
            docs_response = st.session_state.api_client.list_documents()
        
        documents = docs_response["documents"]
        
        if not documents:
            st.info("No documents uploaded yet.")
        else:
            for doc in documents:
                with st.expander(f"📄 {doc['original_filename']} ({doc['status']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Status:** {doc['status']}")
                        st.write(f"**Size:** {doc['file_size']:,} bytes")
                        st.write(f"**Chunks:** {doc['processed_chunks']}/{doc['total_chunks']}")
                        st.write(f"**Language:** {doc['language']}")
                    
                    with col2:
                        st.write(f"**Uploaded:** {doc['uploaded_at'][:19]}")
                        if doc['processed_at']:
                            st.write(f"**Processed:** {doc['processed_at'][:19]}")
                        st.write(f"**Word Count:** {doc['word_count']:,}")
                        if doc['tags']:
                            st.write(f"**Tags:** {', '.join(doc['tags'])}")
    
    except Exception as e:
        st.error(f"Failed to load documents: {str(e)}")


def chat_interface():
    """Main chat interface for RAG queries"""
    st.header("RAG Chat Interface")
    
    # Query configuration
    with st.expander("Query Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_chunks = st.slider("Max Context Chunks", 1, 10, 5)
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        
        with col2:
            score_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.3, 0.1)
            max_tokens = st.slider("Max Response Tokens", 100, 2000, 1000, 100)
        
        with col3:
            include_sources = st.checkbox("Include Sources", value=True)
            stream_response = st.checkbox("Stream Response", value=False)
    
    # Chat history display
    st.markdown("### Conversation")
    
    # Display chat history
    for i, msg in enumerate(st.session_state.chat_history):
        if msg["type"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Assistant:** {msg['content']}")
            
            if "context_documents" in msg and include_sources:
                with st.expander(f"Sources ({len(msg['context_documents'])} documents)"):
                    for j, doc in enumerate(msg["context_documents"], 1):
                        st.markdown(f"""
                        <div class="context-doc">
                            <strong>Source {j}: {doc['source']}</strong><br>
                            <em>Score: {doc['score']:.3f} | Page: {doc.get('page_number', 'N/A')}</em><br>
                            {doc['text'][:200]}{'...' if len(doc['text']) > 200 else ''}
                        </div>
                        """, unsafe_allow_html=True)
        
        if i < len(st.session_state.chat_history) - 1:
            st.markdown("---")
    
    # Query input
    st.markdown("### Ask a Question")
    
    query = st.text_area(
        "Enter your question:",
        placeholder="Ask anything about your uploaded documents...",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        submit_query = st.button("Submit Query", type="primary", use_container_width=True)
    
    with col2:
        clear_history = st.button("Clear History", use_container_width=True)
    
    if clear_history:
        st.session_state.chat_history = []
        st.rerun()
    
    if submit_query and query.strip():
        # Add user message to history
        st.session_state.chat_history.append({
            "type": "user",
            "content": query,
            "timestamp": datetime.now()
        })
        
        try:
            with st.spinner("Generating response..."):
                response = st.session_state.api_client.rag_query(
                    query=query,
                    max_chunks=max_chunks,
                    score_threshold=score_threshold,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    include_sources=include_sources,
                    stream=stream_response
                )
            
            # Add assistant response to history
            assistant_msg = {
                "type": "assistant",
                "content": response["response"],
                "timestamp": datetime.now(),
                "processing_time": response["processing_time_ms"],
                "context_documents": response.get("context_documents", []),
                "tokens_used": response["total_tokens"]
            }
            
            st.session_state.chat_history.append(assistant_msg)
            
            # Show success message
            st.success(f"Response generated in {response['processing_time_ms']:.0f}ms using {response['total_tokens']} tokens")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Query failed: {str(e)}")


def query_history():
    """Display query history and analytics"""
    st.header("Query History & Analytics")
    
    try:
        with st.spinner("Loading query history..."):
            history_response = st.session_state.api_client.get_query_history(limit=20)
        
        queries = history_response["queries"]
        
        if not queries:
            st.info("No queries found.")
            return
        
        # Analytics summary
        st.markdown("### Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        total_queries = len(queries)
        avg_processing_time = sum(q.get("processing_time_ms", 0) for q in queries) / total_queries if total_queries > 0 else 0
        total_tokens = sum(q.get("total_tokens", 0) for q in queries)
        
        with col1:
            st.metric("Total Queries", total_queries)
        
        with col2:
            st.metric("Avg Processing Time", f"{avg_processing_time:.0f}ms")
        
        with col3:
            st.metric("Total Tokens Used", f"{total_tokens:,}")
        
        with col4:
            successful_queries = sum(1 for q in queries if q.get("status") == "completed")
            success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        st.markdown("---")
        
        # Query list
        st.markdown("### Recent Queries")
        
        for query in queries:
            with st.expander(f"{query['query_text'][:100]}... ({query['created_at'][:19]})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Status:** {query['status']}")
                    st.write(f"**Processing Time:** {query.get('processing_time_ms', 0):.0f}ms")
                    st.write(f"**Chunks Retrieved:** {query.get('retrieved_chunks_count', 0)}")
                
                with col2:
                    st.write(f"**LLM Provider:** {query.get('llm_provider', 'N/A')}")
                    st.write(f"**Total Tokens:** {query.get('total_tokens', 0):,}")
                    if query.get('user_rating'):
                        st.write(f"**Rating:** {'⭐' * query['user_rating']}")
                
                if query.get("response"):
                    st.markdown("**Response:**")
                    st.write(query["response"]["response_text"][:500] + "..." if len(query["response"]["response_text"]) > 500 else query["response"]["response_text"])
    
    except Exception as e:
        st.error(f"Failed to load query history: {str(e)}")


def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.tenant_info = None
    st.session_state.chat_history = []
    st.session_state.api_client = APIClient(API_BASE_URL)
    st.rerun()


def main():
    """Main application function"""
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_form()
        return
    
    # Sidebar navigation
    page = sidebar()
    
    # Logout button in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content based on navigation
    if page == "Chat":
        chat_interface()
    elif page == "Documents":
        document_management()
    elif page == "History":
        query_history()


if __name__ == "__main__":
    main()