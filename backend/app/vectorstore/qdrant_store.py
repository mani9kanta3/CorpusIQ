"""
Qdrant Vector Store Implementation
==================================

Qdrant is an open-source vector database.
"""

import time
import uuid
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from .base import BaseVectorStore
from .models import VectorRecord, SearchResult, SearchResponse


class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant vector store implementation.
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
        """
        if url:
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            self.client = QdrantClient(host=host, port=port)
        
        self.host = host
        self.port = port
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> bool:
        """Create a new collection."""
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
        """Insert vectors into collection."""
        if not records:
            return True
        
        points = []
        for record in records:
            qdrant_id = self._to_qdrant_id(record.id)
            
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
        """Search for similar vectors."""
        start_time = time.time()
        
        query_filter = None
        if filters:
            query_filter = self._build_filter(filters)
        
        # Use query_points instead of search (newer API)
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        
        search_time = (time.time() - start_time) * 1000
        
        search_results = []
        for r in results.points:
            original_id = r.payload.get("_original_id", str(r.id)) if r.payload else str(r.id)
            payload = {k: v for k, v in (r.payload or {}).items() if not k.startswith("_")}
            
            search_results.append(
                SearchResult(
                    id=original_id,
                    score=r.score if r.score is not None else 0.0,
                    payload=payload
                )
            )
        
        return SearchResponse(
            results=search_results,
            query="",
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
        """Delete vectors matching a filter."""
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
                "points_count": info.points_count,
                "status": str(info.status) if info.status else "unknown",
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _to_qdrant_id(self, original_id: str) -> str:
        """Convert any string ID to a valid UUID for Qdrant."""
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        return str(uuid.uuid5(namespace, original_id))
    
    def _build_filter(self, filters: dict) -> models.Filter:
        """Build Qdrant filter from dict."""
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                conditions.append(
                    models.FieldCondition(
                        key=field,
                        match=models.MatchAny(any=value)
                    )
                )
            else:
                conditions.append(
                    models.FieldCondition(
                        key=field,
                        match=models.MatchValue(value=value)
                    )
                )
        
        return models.Filter(must=conditions)