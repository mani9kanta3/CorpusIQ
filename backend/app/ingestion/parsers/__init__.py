"""
Document Parsers Package
========================

This package contains parsers for different document formats.

Usage:
    from app.ingestion.parsers import ParserFactory, ParsedDocument
    
    parser = ParserFactory.get_parser(Path("document.pdf"))
    result = parser.parse(Path("document.pdf"))
    
    print(result.content)
    print(result.metadata.page_count)

Available parsers:
    - PDFParser: .pdf files
    - DOCXParser: .docx files (Word)
    - XLSXParser: .xlsx files (Excel)
    - TextParser: .txt, .md, .csv files

To add a new parser:
    1. Create parser class inheriting from BaseParser
    2. Implement parse() and extract_metadata() methods
    3. Add to PARSER_REGISTRY in factory.py
"""

from .base import BaseParser, DocumentMetadata, ParsedDocument
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .xlsx_parser import XLSXParser
from .txt_parser import TextParser
from .factory import ParserFactory

# What gets exported when someone does: from app.ingestion.parsers import *
__all__ = [
    # Base classes
    "BaseParser",
    "DocumentMetadata", 
    "ParsedDocument",
    
    # Parsers
    "PDFParser",
    "DOCXParser",
    "XLSXParser",
    "TextParser",
    
    # Factory
    "ParserFactory",
]