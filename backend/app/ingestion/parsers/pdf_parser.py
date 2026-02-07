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
"""

import fitz  # PyMuPDF - install with: pip install PyMuPDF
from pathlib import Path
from datetime import datetime
from typing import Optional

from .base import BaseParser, DocumentMetadata, ParsedDocument


class PDFParser(BaseParser):
    """
    Parser for PDF documents.
    
    Handles:
    - Native PDFs (created digitally - Word to PDF, etc.)
    - Image-based PDFs (scanned documents) - extracts what it can,
      but OCR module will handle these better
    
    Usage:
        parser = PDFParser()
        result = parser.parse(Path("document.pdf"))
        print(result.content)  # Full text
        print(result.pages[0])  # First page text
        print(result.metadata.page_count)  # Number of pages
    """
    
    # This parser handles .pdf files
    SUPPORTED_EXTENSIONS = [".pdf"]
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a PDF and extract all text content.
        
        How it works:
        1. Validate the file exists and is a PDF
        2. Open the PDF with PyMuPDF
        3. Loop through each page
        4. Extract text from each page
        5. Combine into full content
        6. Extract metadata
        7. Return ParsedDocument
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ParsedDocument with extracted text and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If not a PDF file
            RuntimeError: If PDF parsing fails
        """
        # Step 1: Validate file
        # This calls the method from BaseParser
        self.validate_file(file_path)
        
        # Step 2-6: Extract content
        try:
            # fitz.open() opens the PDF
            # Using 'with' ensures the file is properly closed even if errors occur
            with fitz.open(file_path) as doc:
                pages_text = []
                
                # doc is iterable - each iteration gives us a page
                # enumerate gives us both index (page_num) and the page object
                for page_num, page in enumerate(doc):
                    # get_text() extracts text from the page
                    # Different options available:
                    #   "text" - plain text (default)
                    #   "html" - HTML formatted
                    #   "dict" - detailed structure
                    #   "blocks" - text blocks with positions
                    text = page.get_text("text")
                    
                    # Clean up the text
                    # strip() removes leading/trailing whitespace
                    text = text.strip()
                    
                    pages_text.append(text)
                
                # Combine all pages into one string
                # "\n\n" adds blank line between pages for readability
                full_content = "\n\n".join(pages_text)
                
                # Extract metadata while document is still open
                metadata = self._extract_metadata_from_doc(doc, file_path)
            
            # Step 7: Return the result
            return ParsedDocument(
                content=full_content,
                metadata=metadata,
                pages=pages_text
            )
            
        except Exception as e:
            # Wrap any PyMuPDF errors in a clear message
            raise RuntimeError(f"Failed to parse PDF '{file_path}': {str(e)}")
    
    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract only metadata without full text extraction.
        
        Faster than parse() when you just need file info.
        
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
        
        Why a separate method?
        ----------------------
        Both parse() and extract_metadata() need to extract metadata.
        Instead of duplicating code, we put the logic here.
        DRY principle: Don't Repeat Yourself.
        
        Args:
            doc: An open fitz.Document object
            file_path: Path to the file (for filename and size)
            
        Returns:
            DocumentMetadata object
        """
        # doc.metadata is a dictionary with PDF metadata
        # Common keys: 'title', 'author', 'subject', 'creator', 'creationDate', etc.
        pdf_metadata = doc.metadata
        
        # Parse dates from PDF format
        # PDF dates look like: "D:20231215120000+00'00'"
        # We need to convert to Python datetime
        created_at = self._parse_pdf_date(pdf_metadata.get("creationDate"))
        modified_at = self._parse_pdf_date(pdf_metadata.get("modDate"))
        
        return DocumentMetadata(
            filename=file_path.name,  # "document.pdf"
            file_type=self._get_file_extension(file_path),  # "pdf"
            file_size_bytes=self._get_file_size(file_path),
            page_count=len(doc),  # len(doc) gives number of pages
            created_at=created_at,
            modified_at=modified_at,
            author=pdf_metadata.get("author"),  # .get() returns None if key missing
            title=pdf_metadata.get("title")
        )
    
    def _parse_pdf_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """
        Parse PDF date format to Python datetime.
        
        PDF date format: "D:YYYYMMDDHHmmSS+HH'mm'" or variations
        Example: "D:20231215120000+00'00'" = December 15, 2023, 12:00:00
        
        Args:
            date_string: PDF format date string or None
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_string:
            return None
        
        try:
            # Remove the "D:" prefix if present
            if date_string.startswith("D:"):
                date_string = date_string[2:]
            
            # Take first 14 characters: YYYYMMDDHHmmSS
            # Ignore timezone for simplicity
            date_part = date_string[:14]
            
            # Parse using strptime (string parse time)
            # %Y = 4-digit year, %m = month, %d = day
            # %H = hour, %M = minute, %S = second
            return datetime.strptime(date_part, "%Y%m%d%H%M%S")
        except (ValueError, IndexError):
            # If parsing fails, return None instead of crashing
            # Some PDFs have malformed dates
            return None