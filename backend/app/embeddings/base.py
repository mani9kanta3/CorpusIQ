"""
Base Embedding Interface
========================

Defines the contract for embedding generators.

Why an interface?
-----------------
You might want to swap embedding providers:
- OpenAI for production (quality)
- Local model for development (free)
- Cohere for specific use cases

With a common interface, the rest of your code doesn't change.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """
    Result of embedding generation.
    
    Attributes:
        embedding: The vector (list of floats)
        text: Original text that was embedded
        model: Model used for embedding
        tokens_used: Number of tokens processed
    """
    embedding: list[float]
    text: str
    model: str
    tokens_used: int = 0
    
    @property
    def dimensions(self) -> int:
        """Number of dimensions in the embedding."""
        return len(self.embedding)


class BaseEmbedder(ABC):
    """
    Abstract base class for embedding generators.
    
    All embedding implementations must provide:
    - embed_text(): Embed a single text string
    - embed_batch(): Embed multiple texts efficiently
    - get_dimensions(): Return the embedding dimensionality
    """
    
    @abstractmethod
    def embed_text(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with embedding vector
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        
        Batch processing is more efficient than individual calls
        for most APIs (fewer round trips, often cheaper).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of EmbeddingResult objects (same order as input)
        """
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """
        Get the dimensionality of embeddings.
        
        Different models produce different sizes:
        - OpenAI text-embedding-3-small: 1536
        - OpenAI text-embedding-3-large: 3072
        - Cohere: 1024
        
        Returns:
            Number of dimensions
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the embedding model."""
        pass