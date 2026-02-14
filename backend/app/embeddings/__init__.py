"""
Embeddings Package
==================

Converts text into vector embeddings for semantic search.

Available Embedders:
- OpenAIEmbedder: Uses OpenAI API (paid)
- GoogleEmbedder: Uses Google Gemini API (free tier available)

Usage:
    from app.embeddings import GoogleEmbedder
    
    embedder = GoogleEmbedder()
    result = embedder.embed_text("Hello world")
    print(f"Dimensions: {result.dimensions}")
"""

from .base import BaseEmbedder, EmbeddingResult
from .openai_embedder import OpenAIEmbedder
from .google_embedder import GoogleEmbedder

__all__ = [
    "BaseEmbedder",
    "EmbeddingResult",
    "OpenAIEmbedder",
    "GoogleEmbedder",
]