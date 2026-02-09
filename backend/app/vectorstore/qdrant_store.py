"""
Qdrant Vector Store Implementation
==================================

Qdrant is an open-source vector database.

Features:
- High performance similarity search
- Rich filtering capabilities
- Payload storage (metadata with vectors)
- REST and gRPC APIs
- Horizontal scaling

Documentation: https://qdrant.tech/documentation/
"""

import time
import uuid
import hashlib
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from .base import BaseVectorStore
from .models import VectorRecord, SearchResult, SearchResponse


class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant vector store implementation.
    
    Usage:
        # Connect to local Qdrant
        store = QdrantVectorStore(host="localhost", port=6333)
        
        # Create collection
        store.create_collection("documents", vector_size=1536)
        
        # Insert vectors
        records = [
            VectorRecord(id="1", vector=[0.1, 0.2, ...], payload={"text": "..."})
        ]
        store.insert("documents", records)
        
        # Search
        results = store.search("documents", query_vector=[0.1, 0.2, ...])
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        url: Optional[str] = None
    ):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host (default: localhost)
            port: Qdrant server port (default: 6333)
            api_key: API key for Qdrant Cloud (optional)
            url: Full URL (alternative to host/port, for cloud)
        """
        if url:
            # Qdrant Cloud
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            # Local Qdrant
            self.client = QdrantClient(host=host, port=port)
        
        self.host = host
        self.port = port
        
        # Cache for ID mapping (original_id -> qdrant_uuid)
        self._id_map: dict[str, str] = {}
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> bool:
        """
        Create a new collection.
        
        Args:
            collection_name: Name for the collection
            vector_size: Embedding dimensions (1536 for OpenAI small)
            distance_metric: cosine, euclidean, or dot
            
        Returns:
            True if created successfully
        """
        # Map distance metric to Qdrant's enum
        distance_map = {
            "cosine": models.Distance.COSINE,
            "euclidean": models.Distance.EUCLID,
            "dot": models.Distance.DOT
        }
        
        distance = distance_map.get(distance_metric.lower(), models.Distance.COSINE)
        
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            return True
        except UnexpectedResponse as e:
            # Collection might already exist
            if "already exists" in str(e):
                return True
            raise
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False
    
    def insert(
        self,
        collection_name: str,
        records: list[VectorRecord]
    ) -> bool:
        """
        Insert vectors into collection.
        
        Args:
            collection_name: Target collection
            records: VectorRecord objects to insert
            
        Returns:
            True if successful
        """
        if not records:
            return True
        
        points = []
        for record in records:
            # Convert ID to UUID format
            qdrant_id = self._to_qdrant_id(record.id)
            
            # Store original ID in payload for retrieval
            payload = record.payload.copy()
            payload["_original_id"] = record.id
            
            points.append(
                models.PointStruct(
                    id=qdrant_id,
                    vector=record.vector,
                    payload=payload
                )
            )
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return True
    
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
            query_vector: Query embedding
            limit: Max results
            filters: Metadata filters (e.g., {"document_id": "doc_123"})
            
        Returns:
            SearchResponse with results
        """
        start_time = time.time()
        
        # Build filter if provided
        query_filter = None
        if filters:
            query_filter = self._build_filter(filters)
        
        # Execute search
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Convert to our model
        search_results = []
        for r in results:
            # Get original ID from payload if available
            original_id = r.payload.get("_original_id", str(r.id)) if r.payload else str(r.id)
            
            # Remove internal field from payload
            payload = {k: v for k, v in (r.payload or {}).items() if not k.startswith("_")}
            
            search_results.append(
                SearchResult(
                    id=original_id,
                    score=r.score,
                    payload=payload
                )
            )
        
        return SearchResponse(
            results=search_results,
            query="",  # We don't have the text query here
            search_time_ms=search_time
        )
    
    def delete(
        self,
        collection_name: str,
        ids: list[str]
    ) -> bool:
        """Delete vectors by ID."""
        if not ids:
            return True
        
        qdrant_ids = [self._to_qdrant_id(id) for id in ids]
        
        self.client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=qdrant_ids)
        )
        
        return True
    
    def delete_by_filter(
        self,
        collection_name: str,
        filters: dict
    ) -> bool:
        """
        Delete vectors matching a filter.
        
        Useful for deleting all chunks from a specific document.
        
        Args:
            collection_name: Target collection
            filters: Metadata filters (e.g., {"document_id": "doc_123"})
            
        Returns:
            True if successful
        """
        query_filter = self._build_filter(filters)
        
        self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(filter=query_filter)
        )
        
        return True
    
    def get_collection_info(self, collection_name: str) -> dict:
        """Get collection statistics."""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value if info.status else "unknown",
                "vector_size": info.config.params.vectors.size if info.config else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _to_qdrant_id(self, original_id: str) -> str:
        """
        Convert any string ID to a valid UUID for Qdrant.
        
        Qdrant requires IDs to be either:
        - Unsigned integers
        - UUIDs (128-bit)
        
        We use UUID5 with a namespace to create deterministic UUIDs
        from any string. This means the same original_id always
        produces the same UUID.
        
        Args:
            original_id: Any string ID
            
        Returns:
            UUID string
        """
        # Use UUID5 for deterministic UUID generation
        # Same input always produces same output
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # Standard namespace
        return str(uuid.uuid5(namespace, original_id))
    
    def _build_filter(self, filters: dict) -> models.Filter:
        """
        Build Qdrant filter from dict.
        
        Supports:
        - Exact match: {"field": "value"}
        - Multiple values: {"field": ["val1", "val2"]}
        
        Args:
            filters: Dict of field -> value(s)
            
        Returns:
            Qdrant Filter object
        """
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                # Match any of the values
                conditions.append(
                    models.FieldCondition(
                        key=field,
                        match=models.MatchAny(any=value)
                    )
                )
            else:
                # Exact match
                conditions.append(
                    models.FieldCondition(
                        key=field,
                        match=models.MatchValue(value=value)
                    )
                )
        
        return models.Filter(must=conditions)