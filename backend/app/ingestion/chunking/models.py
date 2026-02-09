"""
Chunk Data Models
=================

Defines the structure of document chunks.

A chunk is more than just text - it carries:
- The text content itself
- Where it came from (document, page, section)
- Its relationship to other chunks (parent, siblings)
- Metadata for filtering and citation
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ChunkMetadata:
    """
    Metadata attached to each chunk.
    
    This metadata serves multiple purposes:
    1. CITATION: Tell users exactly where information came from
    2. FILTERING: Search only in specific documents/sections
    3. CONTEXT: Help LLM understand what it's reading
    
    Attributes:
        document_id: Unique identifier for source document
        document_name: Human-readable filename
        page_number: Page number (0-indexed, None for non-paged docs)
        section_title: Header/section this chunk belongs to
        section_hierarchy: Full path like ["Chapter 1", "Section 1.2", "Subsection A"]
        chunk_index: Position of this chunk in the document (0-indexed)
        total_chunks: Total chunks in the document
        content_type: Type of content (text, table, code, list)
        created_at: When the chunk was created
    """
    document_id: str
    document_name: str
    chunk_index: int
    total_chunks: int = 0
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    section_hierarchy: list[str] = field(default_factory=list)
    content_type: str = "text"  # text, table, code, list
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "section_hierarchy": self.section_hierarchy,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat()
        }
    
    def get_citation(self) -> str:
        """
        Generate a human-readable citation.
        
        Examples:
            "contract.pdf, Page 5"
            "manual.pdf, Page 12, Section: Installation"
            "policy.docx, Section: Remote Work Policy"
        """
        parts = [self.document_name]
        
        if self.page_number is not None:
            parts.append(f"Page {self.page_number + 1}")  # 1-indexed for humans
        
        if self.section_title:
            parts.append(f"Section: {self.section_title}")
        
        return ", ".join(parts)


@dataclass
class Chunk:
    """
    A chunk of document content ready for embedding.
    
    Attributes:
        content: The actual text content
        metadata: Associated metadata for citation and filtering
        embedding: Vector embedding (populated later by embedding module)
        parent_id: ID of parent chunk (for hierarchical chunking)
        chunk_id: Unique identifier for this chunk
    """
    content: str
    metadata: ChunkMetadata
    embedding: Optional[list[float]] = None
    parent_id: Optional[str] = None
    chunk_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate chunk_id if not provided."""
        if self.chunk_id is None:
            # Create ID from document + index
            self.chunk_id = f"{self.metadata.document_id}_chunk_{self.metadata.chunk_index}"
    
    @property
    def char_count(self) -> int:
        """Number of characters in content."""
        return len(self.content)
    
    @property
    def word_count(self) -> int:
        """Approximate word count."""
        return len(self.content.split())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage/serialization."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "parent_id": self.parent_id,
            "char_count": self.char_count,
            "word_count": self.word_count
        }
    
    def get_context_header(self) -> str:
        """
        Generate a context header to prepend to content.
        
        This helps LLMs understand what they're reading.
        
        Example:
            "[From: contract.pdf | Page 5 | Section: Payment Terms]"
        """
        return f"[From: {self.metadata.get_citation()}]"
    
    def get_content_with_context(self) -> str:
        """
        Get content with context header prepended.
        
        Useful when sending to LLM.
        """
        return f"{self.get_context_header()}\n\n{self.content}"