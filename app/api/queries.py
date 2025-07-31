"""
Query and RAG API routes
"""
import logging
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import uuid4

from app.schemas.query import (
    QueryRequest, QueryResponse, QueryHistory, QueryFeedback,
    RAGRequest, RAGResponse, ContextDocument, QueryAnalytics
)
from app.dependencies import (
    CurrentUserDep, CurrentTenantDep, DatabaseDep,
    VectorServiceDep, LLMServiceDep, EmbeddingServiceDep
)
from app.models.query import Query, QueryResponse as QueryResponseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queries", tags=["Queries & RAG"])


@router.post("/rag", response_model=RAGResponse)
async def generate_rag_response(
    rag_request: RAGRequest,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    vector_service: VectorServiceDep,
    llm_service: LLMServiceDep,
    embedding_service: EmbeddingServiceDep
):
    """
    Generate RAG response with retrieved context
    """
    start_time = time.time()
    
    try:
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(rag_request.query)
        
        # Build filter conditions for document retrieval
        filter_conditions = {}
        if rag_request.document_ids:
            # Convert UUIDs to strings for filtering
            filter_conditions["document_id"] = [str(doc_id) for doc_id in rag_request.document_ids]
        
        # Retrieve relevant documents from vector store
        search_results = await vector_service.search_documents(
            tenant_id=str(current_tenant.id),
            query_embedding=query_embedding,
            limit=rag_request.max_chunks,
            score_threshold=rag_request.score_threshold,
            filter_conditions=filter_conditions
        )
        
        # Format context documents
        context_documents = []
        context_text_parts = []
        
        for result in search_results:
            context_doc = ContextDocument(
                chunk_id=result["id"],
                document_id=result["document_id"],
                score=result["score"],
                text=result["text"],
                source=result["source"],
                page_number=result.get("page_number"),
                chunk_index=result["chunk_index"],
                metadata=result["metadata"]
            )
            context_documents.append(context_doc)
            context_text_parts.append(result["text"])
        
        # Prepare context for LLM
        context_used = "\n\n".join(context_text_parts)
        
        # Use tenant's LLM configuration if not specified
        llm_provider = rag_request.llm_provider or current_tenant.llm_provider
        llm_model = rag_request.llm_model or current_tenant.llm_model
        
        # Generate LLM response
        llm_response = await llm_service.generate_rag_response(
            query=rag_request.query,
            context_documents=[doc.dict() for doc in context_documents],
            provider=llm_provider,
            model=llm_model,
            system_prompt=rag_request.system_prompt,
            temperature=rag_request.temperature,
            max_tokens=rag_request.max_tokens,
            stream=False  # Non-streaming for this endpoint
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Create query record
        query_record = Query(
            tenant_id=current_tenant.id,
            user_id=current_user.id,
            query_text=rag_request.query,
            query_type="rag",
            processing_time_ms=processing_time,
            status="completed",
            retrieved_chunks_count=len(context_documents),
            retrieved_documents=[doc.document_id for doc in context_documents],
            similarity_threshold=rag_request.score_threshold,
            llm_provider=llm_provider,
            llm_model=llm_model,
            input_tokens=llm_response.usage.get("prompt_tokens", 0),
            output_tokens=llm_response.usage.get("completion_tokens", 0),
            total_tokens=llm_response.usage.get("total_tokens", 0),
            estimated_cost=0.0,  # Would calculate based on provider pricing
            session_id=rag_request.session_id,
            conversation_turn=rag_request.conversation_turn,
            metadata={"rag_request": rag_request.dict()}
        )
        
        db.add(query_record)
        db.commit()
        db.refresh(query_record)
        
        # Create response record
        response_record = QueryResponseModel(
            query_id=query_record.id,
            response_text=llm_response.content,
            response_format="text",
            context_used=context_used,
            context_chunks=[str(doc.chunk_id) for doc in context_documents],
            confidence_score=None,  # Could be calculated based on retrieval scores
            source_attribution=[doc.source for doc in context_documents],
            contains_citations=False,  # Could be analyzed
            fact_checked=False
        )
        
        db.add(response_record)
        db.commit()
        
        # Build response
        rag_response = RAGResponse(
            query_id=query_record.id,
            query=rag_request.query,
            response=llm_response.content,
            context_documents=context_documents,
            context_used=context_used,
            processing_time_ms=processing_time,
            llm_provider=llm_provider,
            llm_model=llm_model,
            input_tokens=llm_response.usage.get("prompt_tokens", 0),
            output_tokens=llm_response.usage.get("completion_tokens", 0),
            total_tokens=llm_response.usage.get("total_tokens", 0),
            estimated_cost=0.0,
            confidence_score=None,
            source_attribution=list(set(doc.source for doc in context_documents)),
            contains_citations=False,
            session_id=rag_request.session_id,
            conversation_turn=rag_request.conversation_turn,
            created_at=query_record.created_at
        )
        
        logger.info(f"RAG query completed for user {current_user.email}: {query_record.id}")
        return rag_response
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        
        # Record failed query
        try:
            failed_query = Query(
                tenant_id=current_tenant.id,
                user_id=current_user.id,
                query_text=rag_request.query,
                query_type="rag",
                processing_time_ms=(time.time() - start_time) * 1000,
                status="failed",
                metadata={"error": str(e), "rag_request": rag_request.dict()}
            )
            db.add(failed_query)
            db.commit()
        except:
            pass  # Don't fail twice
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG query failed"
        )


@router.post("/rag/stream")
async def generate_rag_response_stream(
    rag_request: RAGRequest,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    vector_service: VectorServiceDep,
    llm_service: LLMServiceDep,
    embedding_service: EmbeddingServiceDep
):
    """
    Generate streaming RAG response
    """
    try:
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(rag_request.query)
        
        # Retrieve relevant documents
        search_results = await vector_service.search_documents(
            tenant_id=str(current_tenant.id),
            query_embedding=query_embedding,
            limit=rag_request.max_chunks,
            score_threshold=rag_request.score_threshold
        )
        
        # Format context documents
        context_documents = [
            {
                "chunk_id": result["id"],
                "document_id": result["document_id"],
                "score": result["score"],
                "text": result["text"],
                "source": result["source"],
                "page_number": result.get("page_number"),
                "chunk_index": result["chunk_index"],
                "metadata": result["metadata"]
            }
            for result in search_results
        ]
        
        # Use tenant's LLM configuration if not specified
        llm_provider = rag_request.llm_provider or current_tenant.llm_provider
        llm_model = rag_request.llm_model or current_tenant.llm_model
        
        # Generate streaming response
        response_stream = await llm_service.generate_rag_response(
            query=rag_request.query,
            context_documents=context_documents,
            provider=llm_provider,
            model=llm_model,
            system_prompt=rag_request.system_prompt,
            temperature=rag_request.temperature,
            max_tokens=rag_request.max_tokens,
            stream=True
        )
        
        async def stream_generator():
            try:
                async for chunk in response_stream:
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: [ERROR: {str(e)}]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming RAG query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Streaming RAG query failed"
        )


@router.get("/history", response_model=QueryHistory)
async def get_query_history(
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    skip: int = 0,
    limit: int = 20,
    session_id: Optional[str] = None
):
    """
    Get query history for current user/tenant
    """
    try:
        query = db.query(Query).filter(
            Query.tenant_id == current_tenant.id,
            Query.user_id == current_user.id
        )
        
        if session_id:
            query = query.filter(Query.session_id == session_id)
        
        query = query.order_by(Query.created_at.desc())
        
        total = query.count()
        queries = query.offset(skip).limit(limit).all()
        
        return QueryHistory(
            queries=queries,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get query history"
        )


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: str,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep
):
    """
    Get specific query by ID
    """
    try:
        query = db.query(Query).filter(
            Query.id == query_id,
            Query.tenant_id == current_tenant.id,
            Query.user_id == current_user.id
        ).first()
        
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )
        
        return query
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get query"
        )


@router.post("/{query_id}/feedback")
async def submit_query_feedback(
    query_id: str,
    feedback: QueryFeedback,
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep
):
    """
    Submit feedback for a query
    """
    try:
        query = db.query(Query).filter(
            Query.id == query_id,
            Query.tenant_id == current_tenant.id,
            Query.user_id == current_user.id
        ).first()
        
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )
        
        # Update query with feedback
        query.user_rating = feedback.rating
        query.feedback = feedback.feedback
        
        db.commit()
        
        logger.info(f"Feedback submitted for query {query_id} by {current_user.email}")
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get("/analytics/summary", response_model=QueryAnalytics)
async def get_query_analytics(
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    days: int = 30
):
    """
    Get query analytics for the tenant
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Base query for the period
        base_query = db.query(Query).filter(
            Query.tenant_id == current_tenant.id,
            Query.created_at >= start_date,
            Query.created_at <= end_date
        )
        
        # Total queries in period
        total_queries = base_query.count()
        
        # Queries today
        queries_today = db.query(Query).filter(
            Query.tenant_id == current_tenant.id,
            Query.created_at >= today_start
        ).count()
        
        # Average processing time
        avg_processing_time = base_query.filter(
            Query.processing_time_ms.isnot(None)
        ).with_entities(func.avg(Query.processing_time_ms)).scalar() or 0.0
        
        # Average tokens per query
        avg_tokens = base_query.filter(
            Query.total_tokens > 0
        ).with_entities(func.avg(Query.total_tokens)).scalar() or 0.0
        
        # Total cost
        total_cost = base_query.with_entities(
            func.sum(Query.estimated_cost)
        ).scalar() or 0.0
        
        # Top query types
        query_types = db.query(
            Query.query_type,
            func.count(Query.id).label('count')
        ).filter(
            Query.tenant_id == current_tenant.id,
            Query.created_at >= start_date
        ).group_by(Query.query_type).all()
        
        top_query_types = [
            {"type": qtype, "count": count} 
            for qtype, count in query_types
        ]
        
        # Average rating
        avg_rating = base_query.filter(
            Query.user_rating.isnot(None)
        ).with_entities(func.avg(Query.user_rating)).scalar()
        
        return QueryAnalytics(
            tenant_id=current_tenant.id,
            total_queries=total_queries,
            queries_today=queries_today,
            avg_processing_time_ms=float(avg_processing_time),
            avg_tokens_per_query=float(avg_tokens),
            total_cost=float(total_cost),
            top_query_types=top_query_types,
            avg_rating=float(avg_rating) if avg_rating else None,
            period_start=start_date,
            period_end=end_date
        )
        
    except Exception as e:
        logger.error(f"Failed to get query analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get query analytics"
        )