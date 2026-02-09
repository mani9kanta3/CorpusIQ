"""
Base Vector Store Interface
===========================

Defines the contract for vector database implementations.

This allows swapping between:
- Qdrant (our default)
- Pinecone (cloud alternative)
- Weaviate (another option)
- ChromaDB (simple local option)

Without changing application code.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import VectorRecord, SearchResult, SearchResponse


class BaseVectorStore(ABC):
    """
    Abstract base class for vector stores.
    
    All implementations must provide:
    - create_collection(): Set up a new collection/index
    - insert(): Add vectors
    - search(): Find similar vectors
    - delete(): Remove vectors
    """
    
    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> bool:
        """
        Create a new collection for storing vectors.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimensionality of vectors (e.g., 1536 for OpenAI)
            distance_metric: How to measure similarity (cosine, euclidean, dot)
            
        Returns:
            True if created successfully
        """
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection and all its data."""
        pass
    
    @abstractmethod
    def insert(
        self,
        collection_name: str,
        records: list[VectorRecord]
    ) -> bool:
        """
        Insert vectors into a collection.
        
        Args:
            collection_name: Target collection
            records: List of VectorRecord objects to insert
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> SearchResponse:
        """
        Search for similar vectors.
        
        Args:
            collection_name: Collection to search
            query_vector: The query embedding
            limit: Maximum results to return
            filters: Optional metadata filters
            
        Returns:
            SearchResponse with results
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        collection_name: str,
        ids: list[str]
    ) -> bool:
        """
        Delete vectors by ID.
        
        Args:
            collection_name: Target collection
            ids: List of record IDs to delete
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        """
        Get information about a collection.
        
        Returns dict with:
        - vectors_count: Number of vectors
        - status: Collection status
        """
        pass