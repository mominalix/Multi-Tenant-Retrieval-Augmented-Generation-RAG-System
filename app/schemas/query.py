"""
Query and RAG-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class QueryRequest(BaseModel):
    """Schema for basic query request"""
    query_text: str = Field(..., min_length=1, max_length=1000)
    query_type: str = Field(default="search")
    session_id: Optional[str] = None


class RAGRequest(BaseModel):
    """Schema for RAG query request"""
    query: str = Field(..., min_length=1, max_length=1000)
    
    # Retrieval parameters
    max_chunks: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    document_ids: Optional[List[UUID]] = None
    tags: Optional[List[str]] = None
    
    # LLM parameters
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    system_prompt: Optional[str] = None
    
    # Session parameters
    session_id: Optional[str] = None
    conversation_turn: int = Field(default=1, ge=1)
    
    # Response parameters
    stream: bool = Field(default=False)
    include_sources: bool = Field(default=True)


class ContextDocument(BaseModel):
    """Schema for context document in RAG response"""
    chunk_id: str  # Changed from UUID to str for JSON serialization
    document_id: str  # Changed from UUID to str for JSON serialization
    score: float
    text: str
    source: str
    page_number: Optional[int]
    chunk_index: int
    doc_metadata: Dict[str, Any]


class RAGResponse(BaseModel):
    """Schema for RAG response"""
    query_id: UUID
    query: str
    response: str
    
    # Context information
    context_documents: List[ContextDocument]
    context_used: str
    
    # Processing information
    processing_time_ms: float
    llm_provider: str
    llm_model: str
    
    # Usage information
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    
    # Quality metrics
    confidence_score: Optional[float] = None
    source_attribution: List[str]
    contains_citations: bool
    
    # Session information
    session_id: Optional[str]
    conversation_turn: int
    
    # Metadata
    created_at: datetime


class QueryResponse(BaseModel):
    """Schema for basic query response"""
    id: UUID
    tenant_id: UUID
    user_id: UUID
    query_text: str
    query_type: str
    processing_time_ms: Optional[float]
    status: str
    retrieved_chunks_count: int
    retrieved_documents: List[UUID]
    similarity_threshold: float
    llm_provider: Optional[str]
    llm_model: Optional[str]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    user_rating: Optional[int]
    feedback: Optional[str]
    session_id: Optional[str]
    conversation_turn: int
    query_metadata: Dict[str, Any]
    created_at: datetime
    
    # Include response if available
    response: Optional["QueryResponseData"] = None
    
    class Config:
        from_attributes = True


class QueryResponseData(BaseModel):
    """Schema for query response data"""
    id: UUID
    query_id: UUID
    response_text: str
    response_format: str
    context_used: Optional[str]
    context_chunks: List[UUID]
    confidence_score: Optional[float]
    source_attribution: List[str]
    contains_citations: bool
    fact_checked: bool
    is_cached: bool
    cache_hit: bool
    generated_at: datetime
    
    class Config:
        from_attributes = True


class QueryHistory(BaseModel):
    """Schema for query history"""
    queries: List[QueryResponse]
    total: int
    page: int
    size: int
    pages: int


class QueryFeedback(BaseModel):
    """Schema for query feedback"""
    query_id: UUID
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class QueryAnalytics(BaseModel):
    """Schema for query analytics"""
    tenant_id: UUID
    total_queries: int
    queries_today: int
    avg_processing_time_ms: float
    avg_tokens_per_query: float
    total_cost: float
    top_query_types: List[Dict[str, Any]]
    avg_rating: Optional[float]
    period_start: datetime
    period_end: datetime


# Update QueryResponse to avoid circular import
QueryResponse.model_rebuild()