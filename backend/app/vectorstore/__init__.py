"""
Vector Store Package
====================

Handles storage and retrieval of vector embeddings.

Usage:
    from app.vectorstore import QdrantVectorStore, VectorRecord
    
    # Initialize
    store = QdrantVectorStore(host="localhost", port=6333)
    
    # Create collection
    store.create_collection("my_docs", vector_size=1536)
    
    # Insert
    record = VectorRecord(id="1", vector=[...], payload={"text": "..."})
    store.insert("my_docs", [record])
    
    # Search
    response = store.search("my_docs", query_vector=[...])
    for result in response.results:
        print(f"{result.score}: {result.payload}")
"""

from .models import VectorRecord, SearchResult, SearchResponse
from .base import BaseVectorStore
from .qdrant_store import QdrantVectorStore

__all__ = [
    # Models
    "VectorRecord",
    "SearchResult", 
    "SearchResponse",
    
    # Stores
    "BaseVectorStore",
    "QdrantVectorStore",
]