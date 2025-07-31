"""
Qdrant vector store service for multi-tenant document storage and retrieval
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    VectorParams, Distance, CollectionInfo, 
    PointStruct, Filter, FieldCondition, MatchValue
)
from app.config import settings

logger = logging.getLogger(__name__)


class QdrantVectorService:
    """
    Qdrant vector database service with multi-tenant support
    """
    
    def __init__(self):
        # Initialize Qdrant clients
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            timeout=30.0
        )
        
        self.async_client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            timeout=30.0
        )
        
        self.default_collection = "multi_tenant_documents"
        self.embedding_dimension = settings.embedding_dimension
    
    async def init_collection(self, collection_name: str = None) -> bool:
        """
        Initialize Qdrant collection with multi-tenant support
        """
        if collection_name is None:
            collection_name = self.default_collection
        
        try:
            # Check if collection exists
            collections = await self.async_client.get_collections()
            existing_collections = [c.name for c in collections.collections]
            
            if collection_name not in existing_collections:
                # Create collection with vector configuration
                await self.async_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload index for tenant isolation
                await self.async_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="tenant_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                # Create additional indexes for efficient filtering
                await self.async_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Collection {collection_name} already exists")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize collection {collection_name}: {e}")
            return False
    
    async def add_documents(
        self,
        tenant_id: str,
        documents: List[Dict[str, Any]],
        collection_name: str = None
    ) -> bool:
        """
        Add documents to Qdrant with tenant isolation
        
        Args:
            tenant_id: Tenant identifier for isolation
            documents: List of document dictionaries with text, embeddings, and metadata
            collection_name: Target collection name
        """
        if collection_name is None:
            collection_name = self.default_collection
        
        try:
            points = []
            
            for doc in documents:
                point_id = str(uuid4())
                
                # Ensure tenant_id is in payload for isolation
                payload = doc.get("metadata", {}).copy()
                payload.update({
                    "tenant_id": tenant_id,
                    "document_id": doc.get("document_id"),
                    "chunk_id": doc.get("chunk_id"),
                    "text": doc.get("text", ""),
                    "source": doc.get("source", ""),
                    "page_number": doc.get("page_number"),
                    "chunk_index": doc.get("chunk_index", 0)
                })
                
                # Create point structure
                point = PointStruct(
                    id=point_id,
                    vector=doc["embedding"],
                    payload=payload
                )
                points.append(point)
            
            # Upsert points to Qdrant
            operation_info = await self.async_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} documents for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents for tenant {tenant_id}: {e}")
            return False
    
    async def search_documents(
        self,
        tenant_id: str,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None,
        collection_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents with tenant isolation
        
        Args:
            tenant_id: Tenant identifier for isolation
            query_embedding: Query vector embedding
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Additional filter conditions
            collection_name: Target collection name
        
        Returns:
            List of search results with metadata
        """
        if collection_name is None:
            collection_name = self.default_collection
        
        try:
            # Build filter for tenant isolation
            must_conditions = [
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value=tenant_id)
                )
            ]
            
            # Add additional filter conditions
            if filter_conditions:
                for key, value in filter_conditions.items():
                    must_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            search_filter = Filter(must=must_conditions)
            
            # Perform search with tenant isolation
            search_results = await self.async_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "document_id": result.payload.get("document_id"),
                    "chunk_id": result.payload.get("chunk_id"),
                    "source": result.payload.get("source", ""),
                    "page_number": result.payload.get("page_number"),
                    "chunk_index": result.payload.get("chunk_index", 0),
                    "metadata": {
                        k: v for k, v in result.payload.items() 
                        if k not in ["tenant_id", "text", "document_id", "chunk_id", "source"]
                    }
                })
            
            logger.info(f"Found {len(results)} documents for tenant {tenant_id}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed for tenant {tenant_id}: {e}")
            return []
    
    async def delete_document(
        self,
        tenant_id: str,
        document_id: str,
        collection_name: str = None
    ) -> bool:
        """
        Delete all chunks of a document for a specific tenant
        """
        if collection_name is None:
            collection_name = self.default_collection
        
        try:
            # Find all points for this document and tenant
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="tenant_id",
                        match=MatchValue(value=tenant_id)
                    ),
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            # Get points to delete
            scroll_result = await self.async_client.scroll(
                collection_name=collection_name,
                scroll_filter=search_filter,
                limit=1000,  # Adjust based on your needs
                with_payload=False,
                with_vectors=False
            )
            
            if scroll_result[0]:  # If points found
                point_ids = [point.id for point in scroll_result[0]]
                
                # Delete points
                await self.async_client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=point_ids
                    )
                )
                
                logger.info(f"Deleted {len(point_ids)} chunks for document {document_id} in tenant {tenant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} for tenant {tenant_id}: {e}")
            return False
    
    async def delete_tenant_data(
        self,
        tenant_id: str,
        collection_name: str = None
    ) -> bool:
        """
        Delete all data for a specific tenant (use with caution!)
        """
        if collection_name is None:
            collection_name = self.default_collection
        
        try:
            # Delete all points for this tenant
            await self.async_client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="tenant_id",
                            match=MatchValue(value=tenant_id)
                        )
                    ]
                )
            )
            
            logger.warning(f"Deleted all data for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tenant data for {tenant_id}: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get collection information and statistics
        """
        if collection_name is None:
            collection_name = self.default_collection
        
        try:
            collection_info = await self.async_client.get_collection(collection_name)
            
            return {
                "name": collection_info.config.params.vectors.size,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Qdrant service is healthy
        """
        try:
            collections = await self.async_client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False