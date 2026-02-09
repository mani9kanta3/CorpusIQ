"""
OpenAI Embedding Generator
==========================

Uses OpenAI's embedding API to generate vectors.

Models available:
- text-embedding-3-small: 1536 dimensions, good quality, cheap
- text-embedding-3-large: 3072 dimensions, better quality, more expensive
- text-embedding-ada-002: 1536 dimensions, legacy model

Pricing (as of 2024):
- text-embedding-3-small: $0.02 per 1M tokens
- text-embedding-3-large: $0.13 per 1M tokens
"""

import os
from typing import Optional
from openai import OpenAI

from .base import BaseEmbedder, EmbeddingResult


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI embedding generator.
    
    Usage:
        embedder = OpenAIEmbedder(api_key="sk-...")
        
        # Single text
        result = embedder.embed_text("Hello world")
        print(result.embedding)  # [0.123, -0.456, ...]
        
        # Batch
        results = embedder.embed_batch(["Text 1", "Text 2", "Text 3"])
    
    Environment:
        Set OPENAI_API_KEY environment variable, or pass api_key parameter.
    """
    
    # Model configurations
    MODELS = {
        "text-embedding-3-small": {"dimensions": 1536},
        "text-embedding-3-large": {"dimensions": 3072},
        "text-embedding-ada-002": {"dimensions": 1536},  # Legacy
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ):
        """
        Initialize OpenAI embedder.
        
        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var
            model: Model to use (default: text-embedding-3-small)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        if model not in self.MODELS:
            raise ValueError(
                f"Unknown model: {model}. Available: {list(self.MODELS.keys())}"
            )
        
        self._model = model
        self._dimensions = self.MODELS[model]["dimensions"]
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
    
    @property
    def model_name(self) -> str:
        """Name of the embedding model."""
        return self._model
    
    def get_dimensions(self) -> int:
        """Get embedding dimensionality."""
        return self._dimensions
    
    def embed_text(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with embedding vector
        """
        # Clean the text
        text = text.replace("\n", " ").strip()
        
        if not text:
            raise ValueError("Cannot embed empty text")
        
        # Call OpenAI API
        response = self.client.embeddings.create(
            model=self._model,
            input=text
        )
        
        embedding = response.data[0].embedding
        tokens_used = response.usage.total_tokens
        
        return EmbeddingResult(
            embedding=embedding,
            text=text,
            model=self._model,
            tokens_used=tokens_used
        )
    
    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        
        More efficient than calling embed_text() multiple times.
        OpenAI API supports batching natively.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of EmbeddingResult objects
        """
        if not texts:
            return []
        
        # Clean texts
        cleaned_texts = [t.replace("\n", " ").strip() for t in texts]
        
        # Remove empty texts but track their positions
        non_empty_indices = [i for i, t in enumerate(cleaned_texts) if t]
        non_empty_texts = [cleaned_texts[i] for i in non_empty_indices]
        
        if not non_empty_texts:
            raise ValueError("All texts are empty")
        
        # Call OpenAI API with batch
        response = self.client.embeddings.create(
            model=self._model,
            input=non_empty_texts
        )
        
        # Build results
        results = [None] * len(texts)
        tokens_per_text = response.usage.total_tokens // len(non_empty_texts)
        
        for i, embedding_data in enumerate(response.data):
            original_index = non_empty_indices[i]
            results[original_index] = EmbeddingResult(
                embedding=embedding_data.embedding,
                text=cleaned_texts[original_index],
                model=self._model,
                tokens_used=tokens_per_text
            )
        
        # Handle any empty texts that were skipped
        for i, result in enumerate(results):
            if result is None:
                # Return zero vector for empty texts
                results[i] = EmbeddingResult(
                    embedding=[0.0] * self._dimensions,
                    text="",
                    model=self._model,
                    tokens_used=0
                )
        
        return results
    
    def embed_chunks(self, chunks: list) -> list:
        """
        Embed a list of Chunk objects and attach embeddings to them.
        
        This is a convenience method for working with our Chunk model.
        
        Args:
            chunks: List of Chunk objects from chunking module
            
        Returns:
            Same chunks with embeddings attached
        """
        # Extract texts
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        results = self.embed_batch(texts)
        
        # Attach to chunks
        for chunk, result in zip(chunks, results):
            chunk.embedding = result.embedding
        
        return chunks