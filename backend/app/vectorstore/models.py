"""
Vector Store Data Models
========================

Defines data structures for vector storage and retrieval.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class VectorRecord:
    """
    A record to store in the vector database.
    
    Attributes:
        id: Unique identifier for this record
        vector: The embedding vector
        payload: Metadata stored with the vector (for filtering and retrieval)
    """
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """
    A single search result from vector similarity search.
    
    Attributes:
        id: ID of the matched record
        score: Similarity score (higher = more similar, typically 0-1)
        payload: Metadata from the matched record
        vector: The vector (optional, only if requested)
    """
    id: str
    score: float
    payload: dict[str, Any]
    vector: Optional[list[float]] = None
    
    @property
    def content(self) -> Optional[str]:
        """Get content from payload if available."""
        return self.payload.get("content")
    
    @property
    def document_name(self) -> Optional[str]:
        """Get document name from payload if available."""
        return self.payload.get("document_name")
    
    @property
    def page_number(self) -> Optional[int]:
        """Get page number from payload if available."""
        return self.payload.get("page_number")
    
    def get_citation(self) -> str:
        """Generate citation string from payload."""
        parts = []
        
        if self.document_name:
            parts.append(self.document_name)
        
        if self.page_number is not None:
            parts.append(f"Page {self.page_number + 1}")
        
        section = self.payload.get("section_title")
        if section:
            parts.append(f"Section: {section}")
        
        return ", ".join(parts) if parts else "Unknown source"


@dataclass
class SearchResponse:
    """
    Complete response from a vector search.
    
    Attributes:
        results: List of SearchResult objects
        query: The original query text
        total_results: Number of results returned
        search_time_ms: Time taken for search in milliseconds
    """
    results: list[SearchResult]
    query: str
    total_results: int = 0
    search_time_ms: float = 0
    
    def __post_init__(self):
        if self.total_results == 0:
            self.total_results = len(self.results)
    
    def get_top_content(self, n: int = 5) -> list[str]:
        """Get content from top N results."""
        contents = []
        for result in self.results[:n]:
            if result.content:
                contents.append(result.content)
        return contents
    
    def get_context_for_llm(self, max_results: int = 5) -> str:
        """
        Format results as context for LLM.
        
        Returns a string with numbered results including citations.
        """
        lines = []
        
        for i, result in enumerate(self.results[:max_results]):
            citation = result.get_citation()
            content = result.content or ""
            
            lines.append(f"[{i+1}] Source: {citation}")
            lines.append(f"    Score: {result.score:.3f}")
            lines.append(f"    Content: {content}")
            lines.append("")
        
        return "\n".join(lines)