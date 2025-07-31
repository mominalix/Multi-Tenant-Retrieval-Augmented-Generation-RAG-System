"""
Document-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class DocumentUpload(BaseModel):
    """Schema for document upload metadata"""
    title: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: UUID
    tenant_id: UUID
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: str
    total_chunks: int
    processed_chunks: int
    title: Optional[str]
    summary: Optional[str]
    language: str
    word_count: int
    collection_name: Optional[str]
    embedding_model: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Schema for paginated document list"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


class DocumentProcessRequest(BaseModel):
    """Schema for document processing request"""
    document_id: UUID
    force_reprocess: bool = False


class DocumentProcessResponse(BaseModel):
    """Schema for document processing response"""
    document_id: UUID
    status: str
    message: str
    chunks_created: Optional[int] = None


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response"""
    id: UUID
    document_id: UUID
    chunk_index: int
    text_content: str
    chunk_size: int
    start_char: Optional[int]
    end_char: Optional[int]
    page_number: Optional[int]
    vector_id: Optional[str]
    embedding_model: Optional[str]
    embedding_dimension: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""
    query: str
    limit: int = Field(default=10, ge=1, le=50)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    document_ids: Optional[List[UUID]] = None
    tags: Optional[List[str]] = None


class DocumentSearchResult(BaseModel):
    """Schema for document search result"""
    chunk_id: UUID
    document_id: UUID
    score: float
    text: str
    source: str
    page_number: Optional[int]
    chunk_index: int
    metadata: Dict[str, Any]


class DocumentSearchResponse(BaseModel):
    """Schema for document search response"""
    query: str
    results: List[DocumentSearchResult]
    total_found: int
    search_time_ms: float