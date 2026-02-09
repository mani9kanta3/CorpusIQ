"""
Recursive Text Splitter
=======================

Splits text by trying progressively smaller separators.

Strategy:
1. Try to split by double newlines (paragraphs)
2. If chunks too big, split by single newlines
3. If still too big, split by sentences (. ! ?)
4. If still too big, split by words
5. Last resort: split by characters

This preserves semantic units as much as possible.

Inspired by LangChain's RecursiveCharacterTextSplitter.
"""

import re
from typing import Optional

from .base import BaseChunker
from .models import Chunk
from ..parsers.base import ParsedDocument


class RecursiveChunker(BaseChunker):
    """
    Recursively splits text using hierarchical separators.
    
    Usage:
        chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
        
        # From raw text
        chunks = chunker.chunk_text(
            text="Your document text...",
            document_id="doc_123",
            document_name="report.pdf"
        )
        
        # From ParsedDocument
        chunks = chunker.chunk_document(parsed_doc, document_id="doc_123")
    """
    
    # Separators in order of preference (most to least desirable split points)
    DEFAULT_SEPARATORS = [
        "\n\n",      # Paragraph breaks (best)
        "\n",        # Line breaks
        ". ",        # Sentence ends
        "? ",        # Question ends
        "! ",        # Exclamation ends
        "; ",        # Semicolon
        ", ",        # Comma
        " ",         # Words
        ""           # Characters (last resort)
    ]
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        separators: Optional[list[str]] = None
    ):
        """
        Initialize recursive chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size to keep
            separators: Custom separator hierarchy (optional)
        """
        super().__init__(chunk_size, chunk_overlap, min_chunk_size)
        self.separators = separators or self.DEFAULT_SEPARATORS
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        document_name: str,
        base_metadata: Optional[dict] = None
    ) -> list[Chunk]:
        """
        Split text into chunks using recursive strategy.
        
        Args:
            text: Text to split
            document_id: Document identifier
            document_name: Document filename
            base_metadata: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []
        
        # Split the text
        text_chunks = self._split_text(text, self.separators)
        
        # Create Chunk objects
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = self._create_chunk(
                content=chunk_text,
                document_id=document_id,
                document_name=document_name,
                chunk_index=i,
                total_chunks=len(text_chunks)
            )
            chunks.append(chunk)
        
        # Update total_chunks in metadata (now that we know the count)
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def chunk_document(
        self,
        document: ParsedDocument,
        document_id: str
    ) -> list[Chunk]:
        """
        Split a ParsedDocument into chunks.
        
        Uses page information for better metadata.
        
        Args:
            document: ParsedDocument from parser
            document_id: Document identifier
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_index = 0
        
        # Process each page separately to maintain page references
        for page_num, page_text in enumerate(document.pages):
            if not page_text.strip():
                continue
            
            # Split this page's text
            page_chunks = self._split_text(page_text, self.separators)
            
            for chunk_text in page_chunks:
                chunk = self._create_chunk(
                    content=chunk_text,
                    document_id=document_id,
                    document_name=document.metadata.filename,
                    chunk_index=chunk_index,
                    page_number=page_num
                )
                chunks.append(chunk)
                chunk_index += 1
        
        # Update total counts
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _split_text(
        self,
        text: str,
        separators: list[str]
    ) -> list[str]:
        """
        Recursively split text using separator hierarchy.
        
        Args:
            text: Text to split
            separators: List of separators to try
            
        Returns:
            List of text chunks
        """
        final_chunks = []
        
        # Get the current separator
        separator = separators[0] if separators else ""
        remaining_separators = separators[1:] if len(separators) > 1 else []
        
        # Split by current separator
        if separator:
            splits = text.split(separator)
        else:
            # Character-level split (last resort)
            splits = list(text)
        
        # Process each split
        current_chunk = ""
        
        for split in splits:
            # Add separator back (except for last separator which is "")
            piece = split + separator if separator else split
            
            # If adding this piece would exceed chunk_size
            if len(current_chunk) + len(piece) > self.chunk_size:
                # Save current chunk if it's big enough
                if len(current_chunk) >= self.min_chunk_size:
                    final_chunks.append(current_chunk.strip())
                elif current_chunk and remaining_separators:
                    # Try to split current chunk with finer separator
                    sub_chunks = self._split_text(current_chunk, remaining_separators)
                    final_chunks.extend(sub_chunks)
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Take the last chunk_overlap characters as overlap
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + piece
                else:
                    current_chunk = piece
            else:
                current_chunk += piece
        
        # Don't forget the last chunk
        if current_chunk.strip():
            if len(current_chunk) >= self.min_chunk_size:
                final_chunks.append(current_chunk.strip())
            elif remaining_separators:
                # Try finer splitting
                sub_chunks = self._split_text(current_chunk, remaining_separators)
                final_chunks.extend(sub_chunks)
            else:
                # Keep it even if small (last resort)
                final_chunks.append(current_chunk.strip())
        
        return final_chunks