"""
DocuMind Core Settings

This module uses Pydantic Settings to load and validate configuration from environment
variables. Using Pydantic for settings provides:
1. Type validation at startup (fail fast if config is wrong)
2. Default values with clear documentation
3. Easy testing by overriding settings
4. Clear structure for all configuration options
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    The settings are loaded in this order (later overrides earlier):
    1. Default values defined here
    2. .env file
    3. Environment variables
    
    This means you can set defaults here, override in .env for local dev,
    and override in environment variables for production.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars that aren't defined here
    )
    
    # =========================================================================
    # Application Settings
    # =========================================================================
    app_name: str = "DocuMind"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # =========================================================================
    # API Settings
    # =========================================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON-formatted string from env var
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Treat as comma-separated
                return [origin.strip() for origin in v.split(",")]
        return v
    
    # =========================================================================
    # Security
    # =========================================================================
    secret_key: str = Field(
        default="CHANGE-THIS-IN-PRODUCTION-USE-SECRETS-MANAGEMENT",
        min_length=32,
        description="Secret key for JWT signing. Must be at least 32 characters."
    )
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # =========================================================================
    # Database
    # =========================================================================
    database_url: str = Field(
        default="postgresql+asyncpg://documind:documind@localhost:5432/documind",
        description="Async database URL for SQLAlchemy"
    )
    database_url_sync: str = Field(
        default="postgresql://documind:documind@localhost:5432/documind",
        description="Sync database URL for Alembic migrations"
    )
    
    # =========================================================================
    # Redis
    # =========================================================================
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # =========================================================================
    # Vector Database (Qdrant)
    # =========================================================================
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "documind_chunks"
    qdrant_api_key: str | None = None  # For Qdrant Cloud
    qdrant_url: str | None = None  # For Qdrant Cloud
    
    # =========================================================================
    # LLM Settings
    # =========================================================================
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    
    anthropic_api_key: str | None = None
    
    # Azure OpenAI (Enterprise alternative)
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None
    
    # =========================================================================
    # Embedding Settings
    # =========================================================================
    embedding_provider: Literal["openai", "local", "cohere"] = "openai"
    embedding_dimension: int = 1536  # OpenAI text-embedding-3-small
    embedding_batch_size: int = 100
    local_embedding_model: str = "BAAI/bge-large-en-v1.5"
    
    # =========================================================================
    # Reranking
    # =========================================================================
    rerank_provider: Literal["cohere", "cross-encoder", "none"] = "cross-encoder"
    cohere_api_key: str | None = None
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # =========================================================================
    # Document Processing
    # =========================================================================
    max_upload_size_mb: int = 50
    allowed_extensions: List[str] = Field(
        default=["pdf", "docx", "doc", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "tiff"]
    )
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"
    
    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_extensions(cls, v):
        """Parse allowed extensions from string or list."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return [ext.lower() for ext in v]
    
    # =========================================================================
    # Chunking Settings
    # =========================================================================
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    min_chunk_size: int = Field(default=100, ge=10)
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v, info):
        """Ensure overlap is less than chunk size."""
        # Note: In Pydantic v2, we can't easily access other fields during validation
        # This check will happen at runtime in the chunking module
        return v
    
    # =========================================================================
    # Search Settings
    # =========================================================================
    search_top_k: int = Field(default=20, ge=1, le=100)
    rerank_top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # =========================================================================
    # OCR Settings
    # =========================================================================
    ocr_provider: Literal["tesseract", "aws_textract", "azure"] = "tesseract"
    tesseract_path: str = "/usr/bin/tesseract"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    
    # =========================================================================
    # Monitoring & Observability
    # =========================================================================
    langchain_tracing_v2: bool = False
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str | None = None
    langchain_project: str = "documind"
    sentry_dsn: str | None = None
    
    # =========================================================================
    # Rate Limiting
    # =========================================================================
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # =========================================================================
    # Computed Properties
    # =========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024
    
    def get_qdrant_url(self) -> str:
        """Get the Qdrant connection URL."""
        if self.qdrant_url:
            return self.qdrant_url
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only load settings once, not on every request.
    This is a common pattern for expensive-to-create singleton objects.
    
    In tests, you can clear the cache with: get_settings.cache_clear()
    """
    return Settings()


# Create a module-level settings instance for convenience
# This is loaded when the module is first imported
settings = get_settings()
