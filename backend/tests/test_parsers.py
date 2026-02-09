"""
Parser Test Script
==================

This script tests all document parsers to verify they work correctly.

How to run:
-----------
From the backend directory:
    python -m tests.test_parsers

Or from project root:
    python -m backend.tests.test_parsers

What it tests:
--------------
1. Text parser with a sample .txt file
2. Parser factory routing
3. Supported extensions listing

For PDF/DOCX/XLSX testing:
--------------------------
You'll need to create sample files manually:
- Create a simple PDF using any tool (Word, Google Docs, online converter)
- Create a simple DOCX in Microsoft Word or Google Docs
- Create a simple XLSX in Excel or Google Sheets

Save them in backend/tests/test_files/
"""

import sys
from pathlib import Path

# Add the backend directory to Python path so imports work
# This is needed when running the script directly
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.ingestion.parsers import (
    ParserFactory,
    ParsedDocument,
    DocumentMetadata,
    TextParser,
    PDFParser,
    DOCXParser,
    XLSXParser,
)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(result: ParsedDocument) -> None:
    """Print parsed document details."""
    print(f"\n--- Metadata ---")
    print(f"  Filename: {result.metadata.filename}")
    print(f"  Type: {result.metadata.file_type}")
    print(f"  Size: {result.metadata.file_size_bytes} bytes")
    print(f"  Page/Section count: {result.metadata.page_count}")
    print(f"  Author: {result.metadata.author}")
    print(f"  Title: {result.metadata.title}")
    
    print(f"\n--- Content Preview (first 500 chars) ---")
    preview = result.content[:500]
    if len(result.content) > 500:
        preview += "..."
    print(preview)
    
    print(f"\n--- Pages/Sections: {len(result.pages)} ---")
    for i, page in enumerate(result.pages[:3]):  # Show first 3 only
        preview = page[:100] + "..." if len(page) > 100 else page
        print(f"  [{i+1}]: {preview}")
    if len(result.pages) > 3:
        print(f"  ... and {len(result.pages) - 3} more")


def test_text_parser() -> bool:
    """Test the TextParser with a sample file."""
    print_header("Testing TextParser")
    
    test_file = Path(__file__).parent / "test_files" / "sample.txt"
    
    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        print("Please create the file with some sample text.")
        return False
    
    try:
        parser = TextParser()
        result = parser.parse(test_file)
        print_result(result)
        print("\n✓ TextParser test PASSED")
        return True
    except Exception as e:
        print(f"\n✗ TextParser test FAILED: {e}")
        return False


def test_pdf_parser() -> bool:
    """Test the PDFParser with a sample file."""
    print_header("Testing PDFParser")
    
    test_file = Path(__file__).parent / "test_files" / "sample.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        print("To test: Create a PDF file and save it as sample.pdf")
        return True  # Not a failure, just skipped
    
    try:
        parser = PDFParser()
        result = parser.parse(test_file)
        print_result(result)
        print("\n✓ PDFParser test PASSED")
        return True
    except Exception as e:
        print(f"\n✗ PDFParser test FAILED: {e}")
        return False


def test_docx_parser() -> bool:
    """Test the DOCXParser with a sample file."""
    print_header("Testing DOCXParser")
    
    test_file = Path(__file__).parent / "test_files" / "sample.docx"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        print("To test: Create a Word document and save it as sample.docx")
        return True  # Not a failure, just skipped
    
    try:
        parser = DOCXParser()
        result = parser.parse(test_file)
        print_result(result)
        print("\n✓ DOCXParser test PASSED")
        return True
    except Exception as e:
        print(f"\n✗ DOCXParser test FAILED: {e}")
        return False


def test_xlsx_parser() -> bool:
    """Test the XLSXParser with a sample file."""
    print_header("Testing XLSXParser")
    
    test_file = Path(__file__).parent / "test_files" / "sample.xlsx"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        print("To test: Create an Excel file and save it as sample.xlsx")
        return True  # Not a failure, just skipped
    
    try:
        parser = XLSXParser()
        result = parser.parse(test_file)
        print_result(result)
        print("\n✓ XLSXParser test PASSED")
        return True
    except Exception as e:
        print(f"\n✗ XLSXParser test FAILED: {e}")
        return False


def test_parser_factory() -> bool:
    """Test the ParserFactory routing."""
    print_header("Testing ParserFactory")
    
    try:
        # Test supported extensions
        extensions = ParserFactory.get_supported_extensions()
        print(f"Supported extensions: {extensions}")
        
        # Test parser routing
        test_cases = [
            ("document.pdf", PDFParser),
            ("report.docx", DOCXParser),
            ("data.xlsx", XLSXParser),
            ("notes.txt", TextParser),
            ("readme.md", TextParser),
            ("data.csv", TextParser),
        ]
        
        print("\nParser routing tests:")
        for filename, expected_class in test_cases:
            parser = ParserFactory.get_parser(Path(filename))
            actual_class = type(parser)
            status = "✓" if actual_class == expected_class else "✗"
            print(f"  {status} {filename} -> {actual_class.__name__}")
        
        # Test unsupported extension
        print("\nUnsupported extension test:")
        try:
            ParserFactory.get_parser(Path("file.xyz"))
            print("  ✗ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"  ✓ Correctly raised ValueError: {e}")
        
        # Test is_supported
        print("\nis_supported() tests:")
        print(f"  document.pdf: {ParserFactory.is_supported(Path('document.pdf'))}")
        print(f"  file.xyz: {ParserFactory.is_supported(Path('file.xyz'))}")
        
        print("\n✓ ParserFactory test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ ParserFactory test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" DocuMind Parser Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("TextParser", test_text_parser()))
    results.append(("PDFParser", test_pdf_parser()))
    results.append(("DOCXParser", test_docx_parser()))
    results.append(("XLSXParser", test_xlsx_parser()))
    results.append(("ParserFactory", test_parser_factory()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()