"""
Table Extraction Test Script
============================

Tests table detection, extraction, and formatting.

How to run:
-----------
    cd backend
    python -m tests.test_tables

Requirements:
-------------
- pdfplumber installed
- Test PDF with tables at backend/tests/test_files/sample_tables.pdf
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.ingestion.tables import TableDetector, TableExtractor, TableFormatter


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_table_detector():
    """Test table detection in PDF."""
    print_header("Testing Table Detector")
    
    test_file = Path(__file__).parent / "test_files" / "sample_tables.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        print("Create a PDF with tables and save as sample_tables.pdf")
        return True
    
    try:
        detector = TableDetector()
        
        # Quick check
        has_tables = detector.has_tables(test_file)
        print(f"\nDocument has tables: {has_tables}")
        
        # Detailed detection
        info = detector.detect_tables(test_file)
        
        print(f"\nDocument: {info.file_path.name}")
        print(f"Total pages: {info.total_pages}")
        print(f"Pages with tables: {info.pages_with_tables}")
        print(f"Total tables found: {info.total_tables}")
        
        print("\nTable locations:")
        for loc in info.table_locations:
            print(f"  Page {loc.page_number}: {loc.row_count} rows × {loc.col_count} cols")
        
        print("\n✓ Table Detector test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Table Detector test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_table_extractor():
    """Test table content extraction."""
    print_header("Testing Table Extractor")
    
    test_file = Path(__file__).parent / "test_files" / "sample_tables.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        return True
    
    try:
        extractor = TableExtractor()
        tables = extractor.extract_tables(test_file)
        
        print(f"\nExtracted {len(tables)} table(s)")
        
        for i, table in enumerate(tables):
            print(f"\n--- Table {i + 1} ---")
            print(f"Page: {table.page_number}")
            print(f"Headers: {table.headers}")
            print(f"Rows: {table.row_count}")
            print(f"Columns: {table.col_count}")
            
            # Show first 3 rows
            print("\nData preview:")
            for row in table.rows[:3]:
                print(f"  {row}")
            if table.row_count > 3:
                print(f"  ... ({table.row_count - 3} more rows)")
        
        print("\n✓ Table Extractor test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Table Extractor test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_table_formatter():
    """Test table formatting for LLM consumption."""
    print_header("Testing Table Formatter")
    
    test_file = Path(__file__).parent / "test_files" / "sample_tables.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        return True
    
    try:
        extractor = TableExtractor()
        formatter = TableFormatter()
        
        tables = extractor.extract_tables(test_file)
        
        if not tables:
            print("No tables found to format")
            return True
        
        # Test single table formatting
        table = tables[0]
        
        print("\n--- Markdown Format ---")
        print(table.to_markdown())
        
        print("\n--- LLM Context Format ---")
        llm_format = formatter.to_llm_context(table, include_summary=True)
        print(llm_format)
        
        print("\n--- CSV Format ---")
        print(table.to_csv())
        
        print("\n--- Row Dictionaries ---")
        row_dicts = formatter.to_row_dicts(table)
        for row_dict in row_dicts[:2]:  # First 2 rows
            print(f"  {row_dict}")
        
        # Test multiple tables
        if len(tables) > 1:
            print("\n--- Multiple Tables Combined ---")
            combined = formatter.format_multiple_tables(tables)
            # Show first 500 chars
            preview = combined[:500]
            if len(combined) > 500:
                preview += "..."
            print(preview)
        
        print("\n✓ Table Formatter test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Table Formatter test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_table_column_access():
    """Test accessing specific columns and rows."""
    print_header("Testing Table Data Access")
    
    test_file = Path(__file__).parent / "test_files" / "sample_tables.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        return True
    
    try:
        extractor = TableExtractor()
        tables = extractor.extract_tables(test_file)
        
        if not tables:
            print("No tables found")
            return True
        
        table = tables[0]
        
        print(f"\nTable headers: {table.headers}")
        
        # Try to access first column
        if table.headers:
            first_col = table.headers[0]
            print(f"\nValues in '{first_col}' column:")
            values = table.get_column(first_col)
            for val in values[:5]:
                print(f"  - {val}")
        
        # Access first row as dict
        if table.row_count > 0:
            print(f"\nFirst row as dictionary:")
            row_dict = table.get_row(0)
            for key, value in row_dict.items():
                print(f"  {key}: {value}")
        
        print("\n✓ Table Data Access test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Table Data Access test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all table tests."""
    print("\n" + "=" * 60)
    print(" DocuMind Table Extraction Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Table Detector", test_table_detector()))
    results.append(("Table Extractor", test_table_extractor()))
    results.append(("Table Formatter", test_table_formatter()))
    results.append(("Table Data Access", test_table_column_access()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n All table tests passed!")
    else:
        print("\n Some tests failed. Check output above.")


if __name__ == "__main__":
    main()