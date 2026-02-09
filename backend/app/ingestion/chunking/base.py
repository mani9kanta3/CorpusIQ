"""
Base Chunker Interface
======================

Defines the contract that all chunking strategies must follow.

Like our parser base class, this ensures consistency across
different chunking approaches.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .models import Chunk, ChunkMetadata
from ..parsers.base import ParsedDocument


class BaseChunker(ABC):
    """
    Abstract base class for document chunkers.
    
    All chunking strategies must implement:
    - chunk_text(): Split raw text into chunks
    - chunk_document(): Split a ParsedDocument into chunks
    
    Configuration:
    - chunk_size: Target size for each chunk (in characters)
    - chunk_overlap: Overlap between consecutive chunks
    - min_chunk_size: Minimum size to keep a chunk
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunker with configuration.
        
        Args:
            chunk_size: Target chunk size in characters (default: 1000)
                       ~250 tokens for most models
            chunk_overlap: Overlap between chunks (default: 200)
                          Helps with context at boundaries
            min_chunk_size: Minimum chunk size to keep (default: 100)
                           Smaller chunks are merged or discarded
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Validate configuration
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if min_chunk_size > chunk_size:
            raise ValueError("min_chunk_size must be less than or equal to chunk_size")
    
    @abstractmethod
    def chunk_text(
        self,
        text: str,
        document_id: str,
        document_name: str,
        base_metadata: Optional[dict] = None
    ) -> list[Chunk]:
        """
        Split text into chunks.
        
        Args:
            text: The text to chunk
            document_id: Unique document identifier
            document_name: Human-readable document name
            base_metadata: Additional metadata to attach to all chunks
            
        Returns:
            List of Chunk objects
        """
        pass
    
    @abstractmethod
    def chunk_document(
        self,
        document: ParsedDocument,
        document_id: str
    ) -> list[Chunk]:
        """
        Split a ParsedDocument into chunks.
        
        This method can use page information and document structure
        for smarter chunking.
        
        Args:
            document: ParsedDocument from parser
            document_id: Unique document identifier
            
        Returns:
            List of Chunk objects with page-level metadata
        """
        pass
    
    def _create_chunk(
        self,
        content: str,
        document_id: str,
        document_name: str,
        chunk_index: int,
        total_chunks: int = 0,
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
        section_hierarchy: Optional[list[str]] = None,
        content_type: str = "text"
    ) -> Chunk:
        """
        Helper to create a Chunk with metadata.
        
        Args:
            content: Chunk text content
            document_id: Document identifier
            document_name: Document filename
            chunk_index: Position in document
            total_chunks: Total chunks (can be updated later)
            page_number: Source page number
            section_title: Section header
            section_hierarchy: Full section path
            content_type: Type of content
            
        Returns:
            Chunk object
        """
        metadata = ChunkMetadata(
            document_id=document_id,
            document_name=document_name,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            page_number=page_number,
            section_title=section_title,
            section_hierarchy=section_hierarchy or [],
            content_type=content_type
        )
        
        return Chunk(content=content, metadata=metadata)