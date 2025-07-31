"""
Embedding service for text vectorization using various models
"""
import logging
from typing import List, Union, Dict, Any
from sentence_transformers import SentenceTransformer
import openai
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using various embedding models
    """
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        
        # Initialize local embedding model
        self._local_model = None
        self._load_local_model()
        
        # Configure OpenAI if API key is available
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    def _load_local_model(self):
        """
        Load local SentenceTransformer model
        """
        try:
            self._local_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded local embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load local embedding model: {e}")
    
    async def embed_text(
        self, 
        text: Union[str, List[str]], 
        model_provider: str = "local"
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text using specified provider
        
        Args:
            text: Single text string or list of texts
            model_provider: Provider to use ("local", "openai")
        
        Returns:
            Embedding vector(s)
        """
        if isinstance(text, str):
            text = [text]
            single_text = True
        else:
            single_text = False
        
        try:
            if model_provider == "openai" and settings.openai_api_key:
                embeddings = await self._embed_with_openai(text)
            else:
                embeddings = await self._embed_with_local_model(text)
            
            return embeddings[0] if single_text and embeddings else embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [] if single_text else [[]]
    
    async def _embed_with_local_model(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using local SentenceTransformer model
        """
        if not self._local_model:
            raise ValueError("Local embedding model not loaded")
        
        embeddings = self._local_model.encode(
            texts,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
        
        return embeddings.tolist()
    
    async def _embed_with_openai(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API
        """
        try:
            response = await openai.Embedding.acreate(
                input=texts,
                model="text-embedding-ada-002"
            )
            
            embeddings = [item['embedding'] for item in response['data']]
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            # Fallback to local model
            return await self._embed_with_local_model(texts)
    
    def get_embedding_dimension(self, model_provider: str = "local") -> int:
        """
        Get embedding dimension for the specified provider
        """
        if model_provider == "openai":
            return 1536  # text-embedding-ada-002 dimension
        else:
            return self.dimension
    
    def chunk_text_for_embedding(
        self, 
        text: str, 
        max_chunk_size: int = 512,
        overlap_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks suitable for embedding
        
        Args:
            text: Input text to chunk
            max_chunk_size: Maximum characters per chunk
            overlap_size: Overlap between chunks
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if len(text) <= max_chunk_size:
            return [{
                "text": text,
                "chunk_index": 0,
                "start_char": 0,
                "end_char": len(text),
                "chunk_size": len(text)
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + max_chunk_size, len(text))
            
            # Try to break at word boundary
            if end < len(text):
                # Look for last space within reasonable distance
                for i in range(end, max(start + max_chunk_size - 100, start), -1):
                    if text[i] == ' ':
                        end = i
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunks.append({
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                    "chunk_size": len(chunk_text)
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + max_chunk_size - overlap_size, end)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    async def embed_document_chunks(
        self,
        chunks: List[Dict[str, Any]],
        model_provider: str = "local"
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks
        
        Args:
            chunks: List of chunk dictionaries
            model_provider: Provider to use for embeddings
        
        Returns:
            Chunks with added embedding vectors
        """
        if not chunks:
            return []
        
        # Extract text from chunks
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = await self.embed_text(texts, model_provider)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
            chunk["embedding_model"] = self.model_name
            chunk["embedding_dimension"] = len(embeddings[i])
        
        return chunks
    
    def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        import numpy as np
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)