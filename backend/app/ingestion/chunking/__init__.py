"""
Document Chunking Package
=========================

Splits documents into chunks suitable for embedding and retrieval.

Components:
- models: Chunk and ChunkMetadata data classes
- base: BaseChunker interface
- recursive: RecursiveChunker for basic text splitting
- document_aware: DocumentAwareChunker for structure-preserving splits

Usage:
    from app.ingestion.chunking import DocumentAwareChunker, Chunk
    
    chunker = DocumentAwareChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_document(parsed_doc, document_id="doc_123")
    
    for chunk in chunks:
        print(f"[{chunk.metadata.section_title}]")
        print(chunk.content[:100])
"""

from .models import Chunk, ChunkMetadata
from .base import BaseChunker
from .recursive import RecursiveChunker
from .document_aware import DocumentAwareChunker

__all__ = [
    # Models
    "Chunk",
    "ChunkMetadata",
    
    # Chunkers
    "BaseChunker",
    "RecursiveChunker",
    "DocumentAwareChunker",
]