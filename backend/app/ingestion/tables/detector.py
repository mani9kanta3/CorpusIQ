"""
Table Detector
==============

Detects the presence and location of tables in PDF documents.

Detection strategies:
---------------------
1. Line-based: Look for horizontal/vertical lines forming grid
2. Whitespace-based: Look for aligned columns of text with gaps
3. Hybrid: Combine both approaches

pdfplumber uses line-based detection primarily, which works well
for tables with visible borders. For borderless tables, it uses
text alignment analysis.
"""

import pdfplumber
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class TableLocation:
    """
    Location of a detected table.
    
    Attributes:
        page_number: Zero-indexed page number
        bbox: Bounding box (x0, y0, x1, y1) in PDF coordinates
        row_count: Estimated number of rows
        col_count: Estimated number of columns
    """
    page_number: int
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    row_count: int
    col_count: int


@dataclass 
class DocumentTableInfo:
    """
    Summary of tables found in a document.
    
    Attributes:
        file_path: Path to the document
        total_pages: Total pages in document
        pages_with_tables: List of page numbers containing tables
        table_locations: Detailed location info for each table
        total_tables: Total number of tables found
    """
    file_path: Path
    total_pages: int
    pages_with_tables: list[int]
    table_locations: list[TableLocation]
    total_tables: int


class TableDetector:
    """
    Detects tables in PDF documents.
    
    Usage:
        detector = TableDetector()
        
        # Quick check - does this document have tables?
        has_tables = detector.has_tables(Path("report.pdf"))
        
        # Detailed info
        info = detector.detect_tables(Path("report.pdf"))
        print(f"Found {info.total_tables} tables")
        for loc in info.table_locations:
            print(f"  Page {loc.page_number}: {loc.row_count}x{loc.col_count}")
    """
    
    def has_tables(self, file_path: Path) -> bool:
        """
        Quick check if document contains any tables.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if at least one table is found
        """
        file_path = Path(file_path)
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.find_tables()
                if tables:
                    return True
        
        return False
    
    def detect_tables(self, file_path: Path) -> DocumentTableInfo:
        """
        Detect all tables in a document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            DocumentTableInfo with details about all tables
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        table_locations = []
        pages_with_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                # find_tables() returns table objects with bounding boxes
                tables = page.find_tables()
                
                if tables:
                    pages_with_tables.append(page_num)
                    
                    for table in tables:
                        # Get table dimensions by extracting it
                        extracted = table.extract()
                        
                        if extracted:
                            row_count = len(extracted)
                            col_count = len(extracted[0]) if extracted else 0
                        else:
                            row_count = 0
                            col_count = 0
                        
                        table_locations.append(TableLocation(
                            page_number=page_num,
                            bbox=table.bbox,
                            row_count=row_count,
                            col_count=col_count
                        ))
        
        return DocumentTableInfo(
            file_path=file_path,
            total_pages=total_pages,
            pages_with_tables=pages_with_tables,
            table_locations=table_locations,
            total_tables=len(table_locations)
        )
    
    def detect_tables_on_page(
        self, 
        file_path: Path, 
        page_number: int
    ) -> list[TableLocation]:
        """
        Detect tables on a specific page.
        
        Args:
            file_path: Path to PDF file
            page_number: Zero-indexed page number
            
        Returns:
            List of TableLocation objects for tables on that page
        """
        file_path = Path(file_path)
        
        table_locations = []
        
        with pdfplumber.open(file_path) as pdf:
            if page_number >= len(pdf.pages):
                raise ValueError(
                    f"Page {page_number} out of range. "
                    f"Document has {len(pdf.pages)} pages."
                )
            
            page = pdf.pages[page_number]
            tables = page.find_tables()
            
            for table in tables:
                extracted = table.extract()
                
                if extracted:
                    row_count = len(extracted)
                    col_count = len(extracted[0]) if extracted else 0
                else:
                    row_count = 0
                    col_count = 0
                
                table_locations.append(TableLocation(
                    page_number=page_number,
                    bbox=table.bbox,
                    row_count=row_count,
                    col_count=col_count
                ))
        
        return table_locations