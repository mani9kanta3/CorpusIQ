# DocuMind - Project Structure

## Overview

This document explains every folder and file in the DocuMind project.
Read this BEFORE writing any code. Understanding structure = understanding architecture.

---

## Root Directory

```
documind/
├── backend/                 # Python FastAPI backend (THIS IS WHERE 80% OF YOUR WORK LIVES)
├── frontend/                # React/Next.js frontend (Week 7-8)
├── docker/                  # Docker configurations for all services
├── scripts/                 # Utility scripts (database migrations, data seeding, etc.)
├── tests/                   # Integration tests spanning multiple modules
├── docs/                    # Project documentation, API specs, architecture diagrams
├── .env.example             # Template for environment variables (NEVER commit real .env)
├── .gitignore               # Files Git should ignore
├── docker-compose.yml       # Orchestrates all services locally
├── docker-compose.prod.yml  # Production-specific overrides
├── Makefile                 # Common commands (make run, make test, make lint)
├── README.md                # Project overview, setup instructions
└── pyproject.toml           # Python project configuration (dependencies, linting rules)
```

---

## Backend Directory (Deep Dive)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management (reads from .env)
│   ├── dependencies.py              # Dependency injection (database sessions, etc.)
│   │
│   ├── core/                        # SHARED UTILITIES - No business logic here
│   │   ├── __init__.py
│   │   ├── exceptions.py            # Custom exception classes
│   │   ├── logging.py               # Logging configuration
│   │   ├── security.py              # Password hashing, token utilities
│   │   └── utils.py                 # Generic helpers (file operations, etc.)
│   │
│   ├── models/                      # SQLAlchemy ORM models (database tables)
│   │   ├── __init__.py
│   │   ├── base.py                  # Base model class with common fields
│   │   ├── user.py                  # User model
│   │   ├── document.py              # Document model
│   │   ├── chunk.py                 # Chunk model (pieces of documents)
│   │   └── audit.py                 # Audit log model (who did what when)
│   │
│   ├── schemas/                     # Pydantic schemas (API request/response validation)
│   │   ├── __init__.py
│   │   ├── user.py                  # User-related schemas
│   │   ├── document.py              # Document-related schemas
│   │   ├── search.py                # Search request/response schemas
│   │   └── common.py                # Shared schemas (pagination, etc.)
│   │
│   ├── api/                         # API ROUTES - Thin layer, calls services
│   │   ├── __init__.py
│   │   ├── router.py                # Main router that combines all routes
│   │   ├── v1/                      # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Login, register, token refresh
│   │   │   ├── documents.py         # Upload, list, delete documents
│   │   │   ├── search.py            # Query documents
│   │   │   ├── admin.py             # Admin-only endpoints
│   │   │   └── health.py            # Health check endpoint
│   │   └── deps.py                  # Route-specific dependencies
│   │
│   ├── services/                    # BUSINESS LOGIC - The "brains"
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── document_service.py      # Document CRUD operations
│   │   ├── search_service.py        # Orchestrates search pipeline
│   │   └── admin_service.py         # Admin operations
│   │
│   ├── ingestion/                   # DOCUMENT PROCESSING PIPELINE (Module 1-3)
│   │   ├── __init__.py
│   │   ├── pipeline.py              # Main ingestion orchestrator
│   │   ├── parsers/                 # File-type specific parsers
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Abstract base parser
│   │   │   ├── pdf_parser.py        # PDF extraction (PyMuPDF)
│   │   │   ├── docx_parser.py       # Word document extraction
│   │   │   ├── xlsx_parser.py       # Excel extraction
│   │   │   ├── image_parser.py      # Image text extraction (OCR)
│   │   │   └── txt_parser.py        # Plain text handling
│   │   ├── ocr/                     # OCR processing (Module 2)
│   │   │   ├── __init__.py
│   │   │   ├── detector.py          # Detect if page needs OCR
│   │   │   ├── preprocessor.py      # Image enhancement before OCR
│   │   │   └── extractor.py         # OCR text extraction
│   │   ├── tables/                  # Table extraction (Module 3)
│   │   │   ├── __init__.py
│   │   │   ├── detector.py          # Detect tables in pages
│   │   │   └── extractor.py         # Extract table structure
│   │   └── chunking/                # Document chunking (Module 4)
│   │       ├── __init__.py
│   │       ├── strategies.py        # Different chunking approaches
│   │       └── hierarchy.py         # Preserve document structure
│   │
│   ├── embeddings/                  # EMBEDDING GENERATION (Module 5)
│   │   ├── __init__.py
│   │   ├── generator.py             # Generate embeddings from text
│   │   ├── cache.py                 # Cache embeddings to avoid recomputation
│   │   └── models.py                # Embedding model configurations
│   │
│   ├── vectorstore/                 # VECTOR DATABASE (Module 5)
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract vector store interface
│   │   ├── pinecone_store.py        # Pinecone implementation
│   │   ├── qdrant_store.py          # Qdrant implementation (self-hosted option)
│   │   └── schemas.py               # Vector store specific schemas
│   │
│   ├── search/                      # SEARCH PIPELINE (Module 6)
│   │   ├── __init__.py
│   │   ├── hybrid.py                # Combines vector + BM25 search
│   │   ├── vector_search.py         # Semantic/vector search
│   │   ├── bm25_search.py           # Keyword/lexical search
│   │   ├── reranker.py              # Rerank results for relevance
│   │   └── filters.py               # Metadata filtering logic
│   │
│   ├── llm/                         # LLM INTEGRATION (Module 7)
│   │   ├── __init__.py
│   │   ├── client.py                # LLM API client (OpenAI, Claude, etc.)
│   │   ├── prompts.py               # System prompts, prompt templates
│   │   ├── response_generator.py   # Generate answers from context
│   │   └── citation.py              # Extract and format citations
│   │
│   ├── entity_extraction/           # ENTITY EXTRACTION (Module 8)
│   │   ├── __init__.py
│   │   ├── extractor.py             # Main extraction logic
│   │   ├── ner.py                   # Named Entity Recognition
│   │   ├── contract_entities.py     # Contract-specific entities
│   │   └── patterns.py              # Regex patterns for dates, amounts, etc.
│   │
│   └── db/                          # DATABASE UTILITIES
│       ├── __init__.py
│       ├── session.py               # Database session management
│       ├── migrations/              # Alembic migrations
│       │   └── versions/            # Migration files
│       └── init_db.py               # Database initialization
│
├── workers/                         # BACKGROUND WORKERS (Celery)
│   ├── __init__.py
│   ├── celery_app.py                # Celery configuration
│   └── tasks/
│       ├── __init__.py
│       ├── ingestion_tasks.py       # Document processing tasks
│       └── embedding_tasks.py       # Embedding generation tasks
│
├── tests/                           # BACKEND TESTS
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests (test individual functions)
│   │   ├── test_parsers.py
│   │   ├── test_chunking.py
│   │   └── test_search.py
│   └── integration/                 # Integration tests (test workflows)
│       ├── test_ingestion_pipeline.py
│       └── test_search_pipeline.py
│
├── requirements.txt                 # Python dependencies (pip install -r requirements.txt)
├── requirements-dev.txt             # Development-only dependencies (pytest, black, etc.)
└── alembic.ini                      # Alembic migration configuration
```

---

## Frontend Directory (Week 7-8)

```
frontend/
├── src/
│   ├── app/                         # Next.js App Router pages
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Home page
│   │   ├── chat/                    # Chat interface
│   │   ├── documents/               # Document library
│   │   └── admin/                   # Admin dashboard
│   │
│   ├── components/                  # Reusable UI components
│   │   ├── ui/                      # Generic UI (buttons, inputs, etc.)
│   │   ├── chat/                    # Chat-specific components
│   │   ├── documents/               # Document-specific components
│   │   └── admin/                   # Admin-specific components
│   │
│   ├── hooks/                       # Custom React hooks
│   ├── lib/                         # Utility functions, API client
│   ├── stores/                      # State management (Zustand or similar)
│   └── types/                       # TypeScript type definitions
│
├── public/                          # Static assets
├── package.json                     # Node.js dependencies
├── tailwind.config.js               # Tailwind CSS configuration
├── tsconfig.json                    # TypeScript configuration
└── next.config.js                   # Next.js configuration
```

---

## Docker Directory

```
docker/
├── backend/
│   ├── Dockerfile                   # Backend container definition
│   └── entrypoint.sh                # Startup script
├── frontend/
│   └── Dockerfile                   # Frontend container definition
├── postgres/
│   └── init.sql                     # Database initialization script
├── redis/
│   └── redis.conf                   # Redis configuration
└── nginx/
    └── nginx.conf                   # Reverse proxy configuration (production)
```

---

## Key Concepts to Understand

### 1. Separation: Routes vs Services vs Models

```
API Routes (api/)     → Handle HTTP requests, validate input, return responses
                      → THIN - just calls services

Services (services/)  → Business logic, orchestration
                      → THICK - actual work happens here

Models (models/)      → Database table definitions
                      → Define structure, relationships
```

### 2. Why So Many `__init__.py` Files?

These make folders into Python packages, allowing imports like:
```python
from app.ingestion.parsers import PDFParser
```

### 3. The Ingestion Pipeline Flow

```
Upload → Type Detection → Parser → OCR (if needed) → Table Extraction 
       → Chunking → Embedding → Vector Store → Database Metadata
```

Each step is a separate module. If one breaks, you know exactly where.

### 4. The Search Pipeline Flow

```
Query → Embedding → Vector Search ─┐
                                   ├→ Fusion → Reranking → LLM → Response
Query → BM25 Search ──────────────┘
```

---

## Your First Task

After this structure is created:
1. Read through this document completely
2. Draw the architecture on paper (seriously - it helps)
3. Identify which modules map to which folders
4. Come back with questions about anything unclear

Do NOT start coding until you can explain why each folder exists.
