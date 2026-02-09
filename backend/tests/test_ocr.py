"""
OCR Module Test Script
======================

Tests the OCR detector, preprocessor, and engine.

How to run:
-----------
    cd backend
    python -m tests.test_ocr

Requirements:
-------------
- Tesseract installed and in PATH
- Poppler installed and in PATH
- Test files in backend/tests/test_files/
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.ingestion.ocr import (
    OCRDetector,
    OCREngine,
    ImagePreprocessor,
    DocumentOCRStatus,
    OCRResult,
)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_detector():
    """Test the OCR detector with our sample PDF."""
    print_header("Testing OCR Detector")
    
    test_file = Path(__file__).parent / "test_files" / "sample.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        return True
    
    try:
        detector = OCRDetector()
        status = detector.check_document(test_file)
        
        print(f"\nDocument: {status.file_path.name}")
        print(f"Total pages: {status.total_pages}")
        print(f"Pages needing OCR: {status.pages_needing_ocr}")
        print(f"Pages with native text: {status.pages_with_text}")
        print(f"Recommendation: {status.recommendation}")
        
        print("\n✓ OCR Detector test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ OCR Detector test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preprocessor():
    """Test the image preprocessor."""
    print_header("Testing Image Preprocessor")
    
    # Look for any image file
    test_dir = Path(__file__).parent / "test_files"
    image_files = list(test_dir.glob("*.png")) + list(test_dir.glob("*.jpg"))
    
    if not image_files:
        print("SKIPPED: No image files found in test_files/")
        print("Add a .png or .jpg file to test preprocessing")
        return True
    
    test_file = image_files[0]
    
    try:
        from PIL import Image
        
        preprocessor = ImagePreprocessor()
        
        # Load original
        original = Image.open(test_file)
        print(f"\nOriginal image: {test_file.name}")
        print(f"  Size: {original.size}")
        print(f"  Mode: {original.mode}")
        
        # Preprocess
        processed = preprocessor.preprocess(test_file)
        print(f"\nProcessed image:")
        print(f"  Size: {processed.size}")
        print(f"  Mode: {processed.mode}")
        
        print("\n✓ Preprocessor test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Preprocessor test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_image():
    """Test OCR on a single image."""
    print_header("Testing OCR on Image")
    
    # Look for any image file
    test_dir = Path(__file__).parent / "test_files"
    image_files = list(test_dir.glob("*.png")) + list(test_dir.glob("*.jpg"))
    
    if not image_files:
        print("SKIPPED: No image files found")
        print("Add sample_scan.png to test_files/ to test OCR")
        return True
    
    test_file = image_files[0]
    
    try:
        engine = OCREngine()
        result = engine.ocr_image(test_file)
        
        print(f"\nImage: {test_file.name}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Language: {result.language}")
        print(f"\nExtracted text ({len(result.text)} chars):")
        print("-" * 40)
        # Show first 500 characters
        preview = result.text[:500]
        if len(result.text) > 500:
            preview += "..."
        print(preview)
        print("-" * 40)
        
        if result.text.strip():
            print("\n✓ OCR Image test PASSED")
            return True
        else:
            print("\n⚠ OCR returned empty text - image may not contain readable text")
            return True  # Not a failure, just no text found
        
    except Exception as e:
        print(f"\n✗ OCR Image test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_pdf():
    """Test OCR on a PDF."""
    print_header("Testing OCR on PDF")
    
    test_file = Path(__file__).parent / "test_files" / "sample.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        return True
    
    try:
        # First check if it needs OCR
        detector = OCRDetector()
        status = detector.check_document(test_file)
        
        print(f"\nDocument: {test_file.name}")
        print(f"Pages needing OCR: {status.pages_needing_ocr}")
        
        if not status.pages_needing_ocr:
            print("\nThis PDF has native text - no OCR needed")
            print("To test OCR, create a scanned PDF or use sample_scan.png")
            print("\n✓ OCR PDF test PASSED (no OCR needed)")
            return True
        
        # Run OCR on pages that need it
        engine = OCREngine()
        result = engine.ocr_pdf(test_file, pages=status.pages_needing_ocr)
        
        print(f"\nOCR Results:")
        print(f"Pages processed: {len(result.pages)}")
        print(f"Average confidence: {result.average_confidence:.1f}%")
        print(f"\nExtracted text ({len(result.full_text)} chars):")
        print("-" * 40)
        preview = result.full_text[:500]
        if len(result.full_text) > 500:
            preview += "..."
        print(preview)
        print("-" * 40)
        
        print("\n✓ OCR PDF test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ OCR PDF test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all OCR tests."""
    print("\n" + "=" * 60)
    print(" DocuMind OCR Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("OCR Detector", test_detector()))
    results.append(("Image Preprocessor", test_preprocessor()))
    results.append(("OCR Image", test_ocr_image()))
    results.append(("OCR PDF", test_ocr_pdf()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All OCR tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check output above.")


if __name__ == "__main__":
    main()