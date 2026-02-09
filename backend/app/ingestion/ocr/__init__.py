"""
OCR (Optical Character Recognition) Package
============================================

This package handles text extraction from scanned documents and images.

Components:
- detector: Determines if a document/page needs OCR
- preprocessor: Improves image quality for better OCR results  
- engine: Performs the actual OCR using Tesseract

Usage:
    from app.ingestion.ocr import OCREngine, OCRDetector
    
    # Check if document needs OCR
    detector = OCRDetector()
    status = detector.check_document(Path("document.pdf"))
    
    # Run OCR
    engine = OCREngine()
    result = engine.ocr_pdf(Path("scanned.pdf"))
    print(result.full_text)
"""

from .detector import OCRDetector, PageOCRStatus, DocumentOCRStatus
from .preprocessor import ImagePreprocessor
from .engine import OCREngine, OCRResult, DocumentOCRResult

__all__ = [
    # Detector
    "OCRDetector",
    "PageOCRStatus",
    "DocumentOCRStatus",
    
    # Preprocessor
    "ImagePreprocessor",
    
    # Engine
    "OCREngine",
    "OCRResult",
    "DocumentOCRResult",
]