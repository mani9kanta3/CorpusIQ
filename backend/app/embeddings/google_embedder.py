"""
Google Gemini Embedding Generator
=================================

Uses Google's Gemini API for embeddings.
Free tier available for development.

Model: gemini-embedding-001 (3072 dimensions)
"""

import os
from typing import Optional
from google import genai

from .base import BaseEmbedder, EmbeddingResult


class GoogleEmbedder(BaseEmbedder):
    """
    Google Gemini embedding generator.
    
    Usage:
        embedder = GoogleEmbedder(api_key="your-key")
        result = embedder.embed_text("Hello world")
        print(result.embedding)
    """
    
    MODEL_NAME = "gemini-embedding-001"
    DIMENSIONS = 3072  # Actual dimensions from the model
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google embedder.
        
        Args:
            api_key: Google AI API key
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self._dimensions = self.DIMENSIONS
    
    @property
    def model_name(self) -> str:
        return self.MODEL_NAME
    
    def get_dimensions(self) -> int:
        return self._dimensions
    
    def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text."""
        text = text.replace("\n", " ").strip()
        
        if not text:
            raise ValueError("Cannot embed empty text")
        
        response = self.client.models.embed_content(
            model=self.MODEL_NAME,
            contents=text
        )
        
        embedding = list(response.embeddings[0].values)
        self._dimensions = len(embedding)
        
        return EmbeddingResult(
            embedding=embedding,
            text=text,
            model=self.MODEL_NAME,
            tokens_used=0
        )
    
    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        results = []
        for text in texts:
            text = text.replace("\n", " ").strip()
            if text:
                results.append(self.embed_text(text))
            else:
                results.append(EmbeddingResult(
                    embedding=[0.0] * self._dimensions,
                    text="",
                    model=self.MODEL_NAME,
                    tokens_used=0
                ))
        
        return results
    
    def embed_query(self, text: str) -> EmbeddingResult:
        """Generate embedding for a search query."""
        return self.embed_text(text)
    
    def embed_chunks(self, chunks: list) -> list:
        """Embed Chunk objects and attach embeddings."""
        texts = [chunk.content for chunk in chunks]
        results = self.embed_batch(texts)
        
        for chunk, result in zip(chunks, results):
            chunk.embedding = result.embedding
        
        return chunks