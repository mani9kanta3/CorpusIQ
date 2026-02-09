"""
Table Extraction Package
========================

Extracts tables from PDFs and other documents while preserving structure.

Components:
- detector: Finds tables within document pages
- extractor: Extracts table content with row/column structure
- formatter: Converts tables to LLM-friendly formats (Markdown, JSON)

Why table extraction matters:
-----------------------------
Tables contain structured data that's critical for accurate RAG responses.
Without proper extraction, the relationship between cells is lost.

Usage:
    from app.ingestion.tables import TableExtractor
    
    extractor = TableExtractor()
    tables = extractor.extract_tables(Path("report.pdf"))
    
    for table in tables:
        print(table.to_markdown())
"""

from .detector import TableDetector
from .extractor import TableExtractor, ExtractedTable
from .formatter import TableFormatter

__all__ = [
    "TableDetector",
    "TableExtractor",
    "ExtractedTable",
    "TableFormatter",
]