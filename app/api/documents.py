"""
Document management API routes
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
import json

from app.schemas.document import (
    DocumentResponse, DocumentUpload, DocumentList,
    DocumentProcessRequest, DocumentProcessResponse,
    DocumentChunkResponse, DocumentSearchRequest, DocumentSearchResponse
)
from app.dependencies import (
    CurrentUserDep, CurrentTenantDep, DatabaseDep,
    DocumentServiceDep, VectorServiceDep, TenantServiceDep
)
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    document_service: DocumentServiceDep,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Upload a document for the current tenant
    """
    try:
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid metadata JSON format"
                )
        
        # Upload document
        document = await document_service.upload_document(
            db=db,
            tenant_id=str(current_tenant.id),
            file=file,
            metadata=parsed_metadata
        )
        
        # Start background processing
        background_tasks.add_task(
            document_service.process_document,
            db=db,
            document_id=str(document.id),
            tenant_id=str(current_tenant.id)
        )
        
        logger.info(f"Document uploaded: {document.id} by {current_user.email}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed"
        )


@router.get("/", response_model=DocumentList)
async def list_documents(
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    document_service: DocumentServiceDep,
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None
):
    """
    List documents for the current tenant
    """
    try:
        documents = document_service.list_documents(
            db=db,
            tenant_id=str(current_tenant.id),
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        # Get total count for pagination
        total_query = db.query(Document).filter(Document.tenant_id == current_tenant.id)
        if status_filter:
            total_query = total_query.filter(Document.status == status_filter)
        total = total_query.count()
        
        return DocumentList(
            documents=documents,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    document_service: DocumentServiceDep
):
    """
    Get document by ID (tenant-scoped)
    """
    try:
        document = document_service.get_document(
            db=db,
            document_id=document_id,
            tenant_id=str(current_tenant.id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document"
        )


@router.post("/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    document_service: DocumentServiceDep,
    force_reprocess: bool = False
):
    """
    Process or reprocess a document
    """
    try:
        # Validate document exists and belongs to tenant
        document = document_service.get_document(
            db=db,
            document_id=document_id,
            tenant_id=str(current_tenant.id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if already processed
        if document.status == "processed" and not force_reprocess:
            return DocumentProcessResponse(
                document_id=document.id,
                status="already_processed",
                message="Document already processed. Use force_reprocess=true to reprocess."
            )
        
        # Start background processing
        background_tasks.add_task(
            document_service.process_document,
            db=db,
            document_id=document_id,
            tenant_id=str(current_tenant.id)
        )
        
        return DocumentProcessResponse(
            document_id=document.id,
            status="processing",
            message="Document processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    document_service: DocumentServiceDep
):
    """
    Delete document and all associated data
    """
    try:
        success = await document_service.delete_document(
            db=db,
            document_id=document_id,
            tenant_id=str(current_tenant.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        logger.info(f"Document deleted: {document_id} by {current_user.email}")
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: str,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    document_service: DocumentServiceDep,
    skip: int = 0,
    limit: int = 50
):
    """
    Get chunks for a specific document
    """
    try:
        # Validate document exists and belongs to tenant
        document = document_service.get_document(
            db=db,
            document_id=document_id,
            tenant_id=str(current_tenant.id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).offset(skip).limit(limit).all()
        
        return chunks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document chunks"
        )


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    vector_service: VectorServiceDep,
    embedding_service = None  # Will use dependency injection when we have it
):
    """
    Search documents using vector similarity
    """
    try:
        # Import embedding service here to avoid circular imports
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(search_request.query)
        
        # Build filter conditions
        filter_conditions = {}
        if search_request.document_ids:
            # Note: This would need custom implementation in vector service
            # for filtering by document IDs
            pass
        
        # Search in vector store
        search_results = await vector_service.search_documents(
            tenant_id=str(current_tenant.id),
            query_embedding=query_embedding,
            limit=search_request.limit,
            score_threshold=search_request.score_threshold,
            filter_conditions=filter_conditions
        )
        
        # Format results
        formatted_results = [
            {
                "chunk_id": result["id"],
                "document_id": result["document_id"],
                "score": result["score"],
                "text": result["text"],
                "source": result["source"],
                "page_number": result.get("page_number"),
                "chunk_index": result["chunk_index"],
                "doc_metadata": result["metadata"]
            }
            for result in search_results
        ]
        
        return DocumentSearchResponse(
            query=search_request.query,
            results=formatted_results,
            total_found=len(search_results),
            search_time_ms=0.0  # Would be calculated in real implementation
        )
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document search failed"
        )