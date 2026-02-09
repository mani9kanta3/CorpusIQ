"""
OCR Detector
============

Determines whether a PDF page or document needs OCR processing.

Why detect first?
-----------------
OCR is slow and resource-intensive. Running OCR on a native PDF
(which already has extractable text) wastes time and might even
produce worse results than the original text.

Detection strategy:
1. Try to extract text from the page
2. Calculate text density (characters per page area)
3. If density is below threshold → needs OCR
4. If density is above threshold → native text, skip OCR
"""

import fitz  # PyMuPDF
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class PageOCRStatus:
    """
    OCR status for a single page.
    
    Attributes:
        page_number: Zero-indexed page number
        needs_ocr: True if OCR is recommended for this page
        text_length: Number of characters extracted natively
        confidence: How confident we are in the assessment (0-1)
        reason: Human-readable explanation
    """
    page_number: int
    needs_ocr: bool
    text_length: int
    confidence: float
    reason: str


@dataclass
class DocumentOCRStatus:
    """
    OCR status for an entire document.
    
    Attributes:
        file_path: Path to the document
        total_pages: Total number of pages
        pages_needing_ocr: List of page numbers that need OCR
        pages_with_text: List of page numbers with native text
        recommendation: Overall recommendation for the document
    """
    file_path: Path
    total_pages: int
    pages_needing_ocr: list[int]
    pages_with_text: list[int]
    recommendation: str


class OCRDetector:
    """
    Detects whether PDF pages need OCR processing.
    
    The detector uses heuristics to determine if a page contains
    extractable text or if it's a scanned image.
    
    Thresholds:
    -----------
    - MIN_CHARS_PER_PAGE: Minimum characters to consider a page "has text"
      A typical page has 2000-3000 characters. If we extract less than 50,
      it's likely a scanned page or image-heavy page.
    
    - MIN_TEXT_RATIO: Minimum ratio of text to expected text
      If a page should have ~2000 chars but only has 100, ratio = 0.05
      Low ratio suggests the page might be partially scanned.
    
    Usage:
        detector = OCRDetector()
        
        # Check single page
        status = detector.check_page(Path("doc.pdf"), page_num=0)
        if status.needs_ocr:
            # Run OCR on this page
        
        # Check entire document
        doc_status = detector.check_document(Path("doc.pdf"))
        for page_num in doc_status.pages_needing_ocr:
            # Run OCR on these pages
    """
    
    # Minimum characters to consider a page "has text"
    # Typical page: 2000-3000 chars
    # Less than 50 chars → probably scanned or mostly images
    MIN_CHARS_PER_PAGE = 50
    
    # If page has some text but much less than expected, might be partial scan
    EXPECTED_CHARS_PER_PAGE = 2000
    
    def check_page(
        self, 
        file_path: Path, 
        page_num: int,
        doc: Optional[fitz.Document] = None
    ) -> PageOCRStatus:
        """
        Check if a specific page needs OCR.
        
        Args:
            file_path: Path to the PDF file
            page_num: Zero-indexed page number
            doc: Optional already-opened document (for efficiency when
                 checking multiple pages)
        
        Returns:
            PageOCRStatus with assessment details
        """
        # Open document if not provided
        should_close = False
        if doc is None:
            doc = fitz.open(file_path)
            should_close = True
        
        try:
            # Validate page number
            if page_num < 0 or page_num >= len(doc):
                raise ValueError(
                    f"Page {page_num} out of range. Document has {len(doc)} pages."
                )
            
            # Get the page
            page = doc[page_num]
            
            # Extract text
            text = page.get_text("text").strip()
            text_length = len(text)
            
            # Decision logic
            if text_length < self.MIN_CHARS_PER_PAGE:
                # Very little text - likely scanned
                return PageOCRStatus(
                    page_number=page_num,
                    needs_ocr=True,
                    text_length=text_length,
                    confidence=0.9,
                    reason=f"Only {text_length} characters extracted (threshold: {self.MIN_CHARS_PER_PAGE})"
                )
            
            # Check if page has images that might contain text
            image_list = page.get_images()
            
            if len(image_list) > 0 and text_length < self.EXPECTED_CHARS_PER_PAGE * 0.3:
                # Has images and relatively little text
                # Might be a mix of scanned and native content
                return PageOCRStatus(
                    page_number=page_num,
                    needs_ocr=True,
                    text_length=text_length,
                    confidence=0.6,
                    reason=f"Page has {len(image_list)} images and only {text_length} chars - may contain scanned content"
                )
            
            # Sufficient text extracted
            return PageOCRStatus(
                page_number=page_num,
                needs_ocr=False,
                text_length=text_length,
                confidence=0.9,
                reason=f"Native text extracted: {text_length} characters"
            )
            
        finally:
            if should_close:
                doc.close()
    
    def check_document(self, file_path: Path) -> DocumentOCRStatus:
        """
        Check all pages in a document for OCR needs.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            DocumentOCRStatus with overall assessment
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        pages_needing_ocr = []
        pages_with_text = []
        
        with fitz.open(file_path) as doc:
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                status = self.check_page(file_path, page_num, doc)
                
                if status.needs_ocr:
                    pages_needing_ocr.append(page_num)
                else:
                    pages_with_text.append(page_num)
        
        # Generate recommendation
        if len(pages_needing_ocr) == 0:
            recommendation = "No OCR needed - all pages have native text"
        elif len(pages_needing_ocr) == total_pages:
            recommendation = "Full OCR recommended - document appears to be scanned"
        else:
            recommendation = (
                f"Partial OCR recommended - {len(pages_needing_ocr)} of {total_pages} "
                f"pages need OCR (pages: {pages_needing_ocr})"
            )
        
        return DocumentOCRStatus(
            file_path=file_path,
            total_pages=total_pages,
            pages_needing_ocr=pages_needing_ocr,
            pages_with_text=pages_with_text,
            recommendation=recommendation
        )