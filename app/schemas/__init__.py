"""
Pydantic schemas for API request/response models
"""
from .auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    TenantCreate, TenantResponse, TenantUpdate
)
from .document import (
    DocumentResponse, DocumentUpload, DocumentList,
    DocumentProcessRequest, DocumentProcessResponse
)
from .query import (
    QueryRequest, QueryResponse, QueryHistory,
    RAGRequest, RAGResponse
)

__all__ = [
    # Auth schemas
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    "TenantCreate", "TenantResponse", "TenantUpdate",
    
    # Document schemas
    "DocumentResponse", "DocumentUpload", "DocumentList",
    "DocumentProcessRequest", "DocumentProcessResponse",
    
    # Query schemas
    "QueryRequest", "QueryResponse", "QueryHistory",
    "RAGRequest", "RAGResponse",
]