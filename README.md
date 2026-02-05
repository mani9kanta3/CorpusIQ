# DocuMind - Enterprise Document Intelligence Platform

> AI-powered document intelligence platform that transforms enterprise documents into a searchable, queryable knowledge base using RAG (Retrieval-Augmented Generation).

## Problem Statement

Enterprises accumulate millions of documents - contracts, policies, financial reports, technical manuals. These documents are scattered across systems, and employees waste hours searching for information. Critical knowledge remains trapped in PDFs that no one reads.

**DocuMind solves this by:**
- Ingesting documents of all types (PDF, DOCX, XLSX, images)
- Creating a unified, AI-searchable knowledge base
- Enabling natural language queries with precise citations
- Extracting structured data from unstructured documents

## Key Features

- **Multi-Format Processing**: PDF, Word, Excel, images with OCR
- **Intelligent Chunking**: Preserves document hierarchy and context
- **Hybrid Search**: Combines semantic (vector) + lexical (BM25) retrieval
- **Cross-Document Queries**: Compare and analyze across multiple files
- **Entity Extraction**: Dates, monetary values, names, contract clauses
- **Precise Citations**: Every answer includes document, page, and paragraph references
- **Enterprise Security**: Authentication, document-level permissions, audit logging

## Architecture

```
Frontend (Next.js) - Chat Interface, Document Viewer
                |
                v
FastAPI Backend - Auth, Search Service, Document Processing (Celery)
                |
    +-----------+-----------+
    |           |           |
    v           v           v
PostgreSQL   Vector Store   LLM API
(Metadata)   (Qdrant)       (OpenAI/Claude)
```

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/documind.git
cd documind
cp .env.example .env

# Start services
make docker-up
make install
make db-upgrade
make run
```

## Technology Stack

| Category | Technologies |
|----------|-------------|
| Backend | Python, FastAPI, Celery, SQLAlchemy |
| Database | PostgreSQL, Redis |
| Vector Store | Qdrant / Pinecone |
| Document Processing | PyMuPDF, python-docx, Tesseract OCR |
| Search | Vector + BM25 + Reranking |
| LLM | OpenAI GPT-4 / Claude |
| Frontend | Next.js, React, TailwindCSS |

## Project Progress

- [x] Project structure setup
- [ ] Module 1: Document Ingestion
- [ ] Module 2: OCR Integration
- [ ] Module 3: Table Extraction
- [ ] Module 4: Intelligent Chunking
- [ ] Module 5: Embeddings & Vector Store
- [ ] Module 6: Hybrid Search
- [ ] Module 7: LLM Integration
- [ ] Module 8: Entity Extraction
- [ ] Module 9: FastAPI Backend
- [ ] Module 10: Frontend
- [ ] Module 11: Deployment

## License

MIT License
