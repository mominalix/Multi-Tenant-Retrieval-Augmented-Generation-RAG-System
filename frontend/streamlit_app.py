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
API_BASE_URL = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="Multi-Tenant RAG System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main > div {
    padding-top: 2rem;
}
.stAlert {
    margin-top: 1rem;
}
.upload-section {
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    text-align: center;
}
.query-response {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
.context-doc {
    background-color: #e8f4f8;
    padding: 15px;
    border-radius: 8px;
    margin: 5px 0;
    border-left: 4px solid #0066cc;
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
    """Display login form"""
    st.title("🧠 Multi-Tenant RAG System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            tenant_identifier = st.text_input(
                "Tenant ID or Subdomain (optional)", 
                placeholder="my-company or tenant-uuid"
            )
            
            submit = st.form_submit_button("Login", use_container_width=True)
            
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


def sidebar():
    """Display sidebar with user info and navigation"""
    with st.sidebar:
        if st.session_state.authenticated:
            # User info
            st.markdown("### 👤 User Info")
            st.write(f"**Email:** {st.session_state.user_info['email']}")
            st.write(f"**Role:** {st.session_state.user_info['role']}")
            
            # Tenant info
            st.markdown("### 🏢 Tenant Info")
            tenant = st.session_state.tenant_info
            st.write(f"**Name:** {tenant['name']}")
            st.write(f"**LLM Provider:** {tenant['llm_provider']}")
            st.write(f"**LLM Model:** {tenant['llm_model']}")
            
            st.markdown("---")
            
            # Navigation
            st.markdown("### 📁 Navigation")
            return st.radio(
                "Select Page",
                ["💬 Chat", "📄 Documents", "📊 History"],
                label_visibility="collapsed"
            )
        
        return None


def document_management():
    """Document management interface"""
    st.header("📄 Document Management")
    
    # Upload section
    st.markdown("### Upload New Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'docx'],
        help="Supported formats: PDF, TXT, DOCX"
    )
    
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
    st.header("💬 RAG Chat Interface")
    
    # Query configuration
    with st.expander("⚙️ Query Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_chunks = st.slider("Max Context Chunks", 1, 10, 5)
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        
        with col2:
            score_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.7, 0.1)
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
                with st.expander(f"📚 Sources ({len(msg['context_documents'])} documents)"):
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
                "context_documents": response["context_documents"],
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
    st.header("📊 Query History & Analytics")
    
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
            with st.expander(f"🔍 {query['query_text'][:100]}... ({query['created_at'][:19]})"):
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
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Main content based on navigation
    if page == "💬 Chat":
        chat_interface()
    elif page == "📄 Documents":
        document_management()
    elif page == "📊 History":
        query_history()


if __name__ == "__main__":
    main()