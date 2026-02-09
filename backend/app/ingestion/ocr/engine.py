"""
OCR Engine
==========

Performs actual OCR using Tesseract.

This is the core OCR module that:
1. Takes images (from files, PDFs, or PIL objects)
2. Runs Tesseract OCR
3. Returns extracted text

Tesseract tips:
---------------
- Works best with 300 DPI images
- Prefers black text on white background
- Supports 100+ languages (need to install language packs)
- Can output plain text, hOCR (HTML), or TSV with coordinates

We use pytesseract as the Python wrapper for Tesseract.
"""

import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .preprocessor import ImagePreprocessor
from .detector import OCRDetector, DocumentOCRStatus


@dataclass
class OCRResult:
    """
    Result of OCR processing.
    
    Attributes:
        text: Extracted text content
        confidence: Average confidence score (0-100)
        language: Language used for OCR
        page_number: Page number (for multi-page documents)
    """
    text: str
    confidence: float
    language: str
    page_number: Optional[int] = None


@dataclass
class DocumentOCRResult:
    """
    OCR result for an entire document.
    
    Attributes:
        file_path: Path to the source document
        pages: List of OCRResult for each page
        full_text: Combined text from all pages
        average_confidence: Average confidence across all pages
    """
    file_path: Path
    pages: list[OCRResult]
    full_text: str
    average_confidence: float


class OCREngine:
    """
    Main OCR engine using Tesseract.
    
    Usage:
        engine = OCREngine()
        
        # OCR a single image
        result = engine.ocr_image(Path("scan.png"))
        print(result.text)
        
        # OCR a PDF (scanned)
        result = engine.ocr_pdf(Path("scanned_doc.pdf"))
        print(result.full_text)
        
        # OCR with preprocessing disabled
        result = engine.ocr_image(Path("clean_scan.png"), preprocess=False)
    
    Configuration:
        engine = OCREngine(language="deu")  # German
        engine = OCREngine(language="eng+fra")  # English + French
    """
    
    def __init__(
        self, 
        language: str = "eng",
        tesseract_path: Optional[str] = None
    ):
        """
        Initialize OCR engine.
        
        Args:
            language: Tesseract language code(s). Examples:
                      "eng" - English
                      "deu" - German
                      "fra" - French
                      "eng+fra" - English and French
            tesseract_path: Path to tesseract executable (optional)
                           If not provided, uses system PATH
        """
        self.language = language
        self.preprocessor = ImagePreprocessor()
        self.detector = OCRDetector()
        
        # Set tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def ocr_image(
        self, 
        image_path: Path, 
        preprocess: bool = True
    ) -> OCRResult:
        """
        Perform OCR on a single image file.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess image (recommended)
            
        Returns:
            OCRResult with extracted text and confidence
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        image = Image.open(image_path)
        
        return self.ocr_pil_image(image, preprocess=preprocess)
    
    def ocr_pil_image(
        self, 
        image: Image.Image, 
        preprocess: bool = True,
        page_number: Optional[int] = None
    ) -> OCRResult:
        """
        Perform OCR on a PIL Image object.
        
        Args:
            image: PIL Image object
            preprocess: Whether to preprocess image
            page_number: Optional page number for multi-page docs
            
        Returns:
            OCRResult with extracted text and confidence
        """
        # Preprocess if requested
        if preprocess:
            image = self.preprocessor.preprocess_image(image)
        
        # Run Tesseract
        # We get both text and detailed data for confidence score
        text = pytesseract.image_to_string(image, lang=self.language)
        
        # Get confidence score
        # image_to_data returns detailed info including confidence per word
        try:
            data = pytesseract.image_to_data(
                image, 
                lang=self.language, 
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence (excluding -1 which means no confidence)
            confidences = [
                int(conf) for conf in data["conf"] 
                if int(conf) > 0
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
        except Exception:
            # If detailed data fails, just use the text with unknown confidence
            avg_confidence = 0
        
        return OCRResult(
            text=text.strip(),
            confidence=avg_confidence,
            language=self.language,
            page_number=page_number
        )
    
    def ocr_pdf(
        self, 
        pdf_path: Path,
        pages: Optional[list[int]] = None,
        preprocess: bool = True,
        dpi: int = 300
    ) -> DocumentOCRResult:
        """
        Perform OCR on a PDF document.
        
        Converts PDF pages to images, then runs OCR on each.
        
        Args:
            pdf_path: Path to the PDF file
            pages: Specific pages to OCR (0-indexed). None = all pages
            preprocess: Whether to preprocess images
            dpi: Resolution for PDF to image conversion
                 Higher = better quality but slower
            
        Returns:
            DocumentOCRResult with text from all pages
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Convert PDF to images
        # This uses poppler under the hood
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            raise RuntimeError(
                f"Failed to convert PDF to images. "
                f"Make sure poppler is installed. Error: {e}"
            )
        
        # Determine which pages to process
        if pages is None:
            pages_to_process = list(range(len(images)))
        else:
            pages_to_process = pages
        
        # OCR each page
        page_results = []
        for page_num in pages_to_process:
            if page_num >= len(images):
                continue
            
            image = images[page_num]
            result = self.ocr_pil_image(
                image, 
                preprocess=preprocess,
                page_number=page_num
            )
            page_results.append(result)
        
        # Combine results
        full_text = "\n\n".join(result.text for result in page_results)
        
        # Calculate average confidence
        if page_results:
            avg_confidence = sum(r.confidence for r in page_results) / len(page_results)
        else:
            avg_confidence = 0
        
        return DocumentOCRResult(
            file_path=pdf_path,
            pages=page_results,
            full_text=full_text,
            average_confidence=avg_confidence
        )
    
    def ocr_pdf_smart(
        self,
        pdf_path: Path,
        preprocess: bool = True,
        dpi: int = 300
    ) -> DocumentOCRResult:
        """
        Smart OCR that only processes pages that need it.
        
        Uses the detector to identify which pages are scanned vs native text.
        Only runs OCR on scanned pages, saving time on mixed documents.
        
        Args:
            pdf_path: Path to the PDF file
            preprocess: Whether to preprocess images
            dpi: Resolution for conversion
            
        Returns:
            DocumentOCRResult with text from all pages
        """
        pdf_path = Path(pdf_path)
        
        # Detect which pages need OCR
        status = self.detector.check_document(pdf_path)
        
        if not status.pages_needing_ocr:
            # No pages need OCR - return empty result
            return DocumentOCRResult(
                file_path=pdf_path,
                pages=[],
                full_text="",
                average_confidence=100  # Native text is "perfect"
            )
        
        # Only OCR the pages that need it
        return self.ocr_pdf(
            pdf_path,
            pages=status.pages_needing_ocr,
            preprocess=preprocess,
            dpi=dpi
        )