"""
PDF Parser using PyMuPDF (fitz)
===============================

Why PyMuPDF?
------------
1. SPEED: Fastest PDF library in Python (written in C underneath)
2. FEATURES: Extracts text, images, metadata, annotations
3. RELIABILITY: Handles complex PDFs that break other libraries
4. MEMORY: Efficient with large files

The library is imported as 'fitz' for historical reasons - 
it was originally based on the MuPDF library by Artifex,
and "Fitz" is the name of MuPDF's graphics engine.

Installation: pip install PyMuPDF
Import as: import fitz (NOT import PyMuPDF)

OCR Integration:
----------------
This parser now integrates with the OCR module to handle scanned PDFs.
When a page has no extractable text, OCR is automatically applied.
"""

import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from typing import Optional

from .base import BaseParser, DocumentMetadata, ParsedDocument
from ..ocr import OCRDetector, OCREngine


class PDFParser(BaseParser):
    """
    Parser for PDF documents.
    
    Handles:
    - Native PDFs (created digitally - Word to PDF, etc.)
    - Scanned PDFs (automatically detected and OCR'd)
    - Mixed PDFs (some pages native, some scanned)
    
    Usage:
        parser = PDFParser()
        result = parser.parse(Path("document.pdf"))
        print(result.content)  # Full text (native + OCR'd)
        print(result.pages[0])  # First page text
        print(result.metadata.page_count)  # Number of pages
        
        # Without OCR (faster, but misses scanned pages)
        result = parser.parse(Path("document.pdf"), use_ocr=False)
    """
    
    SUPPORTED_EXTENSIONS = [".pdf"]
    
    def __init__(self):
        """Initialize PDF parser with OCR components."""
        self.ocr_detector = OCRDetector()
        self.ocr_engine = OCREngine()
    
    def parse(
        self, 
        file_path: Path,
        use_ocr: bool = True
    ) -> ParsedDocument:
        """
        Parse a PDF and extract all text content.
        
        Args:
            file_path: Path to the PDF file
            use_ocr: Whether to use OCR for scanned pages (default: True)
            
        Returns:
            ParsedDocument with extracted text and metadata
        """
        self.validate_file(file_path)
        
        try:
            with fitz.open(file_path) as doc:
                pages_text = []
                ocr_was_used = False
                
                # Check which pages need OCR
                if use_ocr:
                    ocr_status = self.ocr_detector.check_document(file_path)
                    pages_needing_ocr = set(ocr_status.pages_needing_ocr)
                else:
                    pages_needing_ocr = set()
                
                for page_num, page in enumerate(doc):
                    # Try native text extraction first
                    text = page.get_text("text").strip()
                    
                    # If page needs OCR and OCR is enabled
                    if page_num in pages_needing_ocr and use_ocr:
                        ocr_text = self._ocr_page(file_path, page_num)
                        if ocr_text:
                            text = ocr_text
                            ocr_was_used = True
                    
                    pages_text.append(text)
                
                full_content = "\n\n".join(pages_text)
                metadata = self._extract_metadata_from_doc(doc, file_path)
                
            return ParsedDocument(
                content=full_content,
                metadata=metadata,
                pages=pages_text
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF '{file_path}': {str(e)}")
    
    def _ocr_page(self, file_path: Path, page_num: int) -> Optional[str]:
        """
        Run OCR on a specific page.
        
        Args:
            file_path: Path to the PDF
            page_num: Page number to OCR
            
        Returns:
            Extracted text or None if OCR fails
        """
        try:
            result = self.ocr_engine.ocr_pdf(
                file_path, 
                pages=[page_num],
                preprocess=True
            )
            
            if result.pages:
                return result.pages[0].text
            return None
            
        except Exception as e:
            # OCR failed - log and continue with empty text
            print(f"Warning: OCR failed for page {page_num}: {e}")
            return None
    
    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract only metadata without full text extraction.
        
        Args:
            file_path: Path to the PDF
            
        Returns:
            DocumentMetadata object
        """
        self.validate_file(file_path)
        
        try:
            with fitz.open(file_path) as doc:
                return self._extract_metadata_from_doc(doc, file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to extract metadata from '{file_path}': {str(e)}")
    
    def _extract_metadata_from_doc(
        self, 
        doc: fitz.Document, 
        file_path: Path
    ) -> DocumentMetadata:
        """
        Extract metadata from an already-opened PDF document.
        
        Args:
            doc: An open fitz.Document object
            file_path: Path to the file (for filename and size)
            
        Returns:
            DocumentMetadata object
        """
        pdf_metadata = doc.metadata
        
        created_at = self._parse_pdf_date(pdf_metadata.get("creationDate"))
        modified_at = self._parse_pdf_date(pdf_metadata.get("modDate"))
        
        return DocumentMetadata(
            filename=file_path.name,
            file_type=self._get_file_extension(file_path),
            file_size_bytes=self._get_file_size(file_path),
            page_count=len(doc),
            created_at=created_at,
            modified_at=modified_at,
            author=pdf_metadata.get("author"),
            title=pdf_metadata.get("title")
        )
    
    def _parse_pdf_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """
        Parse PDF date format to Python datetime.
        
        Args:
            date_string: PDF format date string or None
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_string:
            return None
        
        try:
            if date_string.startswith("D:"):
                date_string = date_string[2:]
            
            date_part = date_string[:14]
            return datetime.strptime(date_part, "%Y%m%d%H%M%S")
        except (ValueError, IndexError):
            return None