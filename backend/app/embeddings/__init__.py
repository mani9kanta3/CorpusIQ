"""
Embeddings Package
==================

Converts text into vector embeddings for semantic search.

Usage:
    from app.embeddings import OpenAIEmbedder
    
    embedder = OpenAIEmbedder()
    result = embedder.embed_text("Hello world")
    print(f"Dimensions: {result.dimensions}")
    print(f"Vector: {result.embedding[:5]}...")  # First 5 values
"""

from .base import BaseEmbedder, EmbeddingResult
from .openai_embedder import OpenAIEmbedder

__all__ = [
    "BaseEmbedder",
    "EmbeddingResult",
    "OpenAIEmbedder",
]