"""
Table Extractor
===============

Extracts table content from PDFs with row/column structure preserved.

The extractor:
1. Finds tables in the document
2. Extracts cell contents
3. Cleans and normalizes data
4. Returns structured table objects

Cell cleaning:
--------------
Raw extracted cells often have issues:
- Extra whitespace
- Newlines within cells
- None values for empty cells
- Merged cell artifacts

We clean these to produce consistent, usable data.
"""

import pdfplumber
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class ExtractedTable:
    """
    A table extracted from a document.
    
    Attributes:
        page_number: Page where table was found (0-indexed)
        headers: Column headers (first row, if detected as headers)
        rows: Data rows (list of lists)
        raw_data: Original extracted data before cleaning
        bbox: Bounding box coordinates
        table_index: Index of this table on the page (0-indexed)
    """
    page_number: int
    headers: list[str]
    rows: list[list[str]]
    raw_data: list[list]
    bbox: Optional[tuple[float, float, float, float]] = None
    table_index: int = 0
    
    @property
    def row_count(self) -> int:
        """Number of data rows (excluding header)."""
        return len(self.rows)
    
    @property
    def col_count(self) -> int:
        """Number of columns."""
        return len(self.headers) if self.headers else 0
    
    def to_markdown(self) -> str:
        """
        Convert table to Markdown format.
        
        Markdown tables are well-understood by LLMs and preserve structure.
        
        Returns:
            Markdown table string
        """
        if not self.headers:
            return ""
        
        lines = []
        
        # Header row
        header_line = "| " + " | ".join(self.headers) + " |"
        lines.append(header_line)
        
        # Separator row
        separator = "| " + " | ".join(["---"] * len(self.headers)) + " |"
        lines.append(separator)
        
        # Data rows
        for row in self.rows:
            # Ensure row has same number of columns as headers
            padded_row = row + [""] * (len(self.headers) - len(row))
            row_line = "| " + " | ".join(padded_row[:len(self.headers)]) + " |"
            lines.append(row_line)
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """
        Convert table to dictionary format.
        
        Useful for JSON serialization and programmatic access.
        
        Returns:
            Dictionary with headers and rows
        """
        return {
            "page_number": self.page_number,
            "table_index": self.table_index,
            "headers": self.headers,
            "rows": self.rows,
            "row_count": self.row_count,
            "col_count": self.col_count
        }
    
    def to_csv(self) -> str:
        """
        Convert table to CSV format.
        
        Returns:
            CSV string
        """
        lines = []
        
        # Header
        lines.append(",".join(f'"{h}"' for h in self.headers))
        
        # Rows
        for row in self.rows:
            # Escape quotes and wrap in quotes
            escaped = [f'"{cell.replace(chr(34), chr(34)+chr(34))}"' for cell in row]
            lines.append(",".join(escaped))
        
        return "\n".join(lines)
    
    def get_column(self, column_name: str) -> list[str]:
        """
        Get all values from a specific column.
        
        Args:
            column_name: Header name of the column
            
        Returns:
            List of values in that column
        """
        if column_name not in self.headers:
            raise ValueError(f"Column '{column_name}' not found. Available: {self.headers}")
        
        col_index = self.headers.index(column_name)
        return [row[col_index] if col_index < len(row) else "" for row in self.rows]
    
    def get_row(self, index: int) -> dict[str, str]:
        """
        Get a row as a dictionary.
        
        Args:
            index: Row index (0-indexed, excluding header)
            
        Returns:
            Dictionary mapping column names to values
        """
        if index >= len(self.rows):
            raise IndexError(f"Row {index} out of range. Table has {len(self.rows)} rows.")
        
        row = self.rows[index]
        return {
            header: row[i] if i < len(row) else ""
            for i, header in enumerate(self.headers)
        }


class TableExtractor:
    """
    Extracts tables from PDF documents.
    
    Usage:
        extractor = TableExtractor()
        
        # Extract all tables from a document
        tables = extractor.extract_tables(Path("report.pdf"))
        
        for table in tables:
            print(f"Found table on page {table.page_number}")
            print(table.to_markdown())
        
        # Extract from specific page
        tables = extractor.extract_tables_from_page(Path("report.pdf"), page_num=0)
    """
    
    def __init__(self, detect_headers: bool = True):
        """
        Initialize extractor.
        
        Args:
            detect_headers: Whether to treat first row as headers (default: True)
        """
        self.detect_headers = detect_headers
    
    def extract_tables(self, file_path: Path) -> list[ExtractedTable]:
        """
        Extract all tables from a PDF document.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of ExtractedTable objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        all_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = self._extract_from_page(page, page_num)
                all_tables.extend(page_tables)
        
        return all_tables
    
    def extract_tables_from_page(
        self, 
        file_path: Path, 
        page_num: int
    ) -> list[ExtractedTable]:
        """
        Extract tables from a specific page.
        
        Args:
            file_path: Path to the PDF file
            page_num: Zero-indexed page number
            
        Returns:
            List of ExtractedTable objects from that page
        """
        file_path = Path(file_path)
        
        with pdfplumber.open(file_path) as pdf:
            if page_num >= len(pdf.pages):
                raise ValueError(
                    f"Page {page_num} out of range. Document has {len(pdf.pages)} pages."
                )
            
            page = pdf.pages[page_num]
            return self._extract_from_page(page, page_num)
    
    def _extract_from_page(
        self, 
        page, 
        page_num: int
    ) -> list[ExtractedTable]:
        """
        Extract all tables from a pdfplumber page object.
        
        Args:
            page: pdfplumber page object
            page_num: Page number for reference
            
        Returns:
            List of ExtractedTable objects
        """
        tables = []
        
        # find_tables() returns table objects
        found_tables = page.find_tables()
        
        for table_idx, table in enumerate(found_tables):
            # extract() returns list of lists (rows of cells)
            raw_data = table.extract()
            
            if not raw_data:
                continue
            
            # Clean the data
            cleaned_data = self._clean_table_data(raw_data)
            
            if not cleaned_data:
                continue
            
            # Separate headers and rows
            if self.detect_headers and len(cleaned_data) > 1:
                headers = cleaned_data[0]
                rows = cleaned_data[1:]
            else:
                # Generate column names if no headers
                col_count = len(cleaned_data[0]) if cleaned_data else 0
                headers = [f"Column_{i+1}" for i in range(col_count)]
                rows = cleaned_data
            
            extracted = ExtractedTable(
                page_number=page_num,
                headers=headers,
                rows=rows,
                raw_data=raw_data,
                bbox=table.bbox,
                table_index=table_idx
            )
            
            tables.append(extracted)
        
        return tables
    
    def _clean_table_data(self, raw_data: list[list]) -> list[list[str]]:
        """
        Clean extracted table data.
        
        Cleaning steps:
        1. Convert None to empty string
        2. Strip whitespace
        3. Normalize internal whitespace (newlines, multiple spaces)
        4. Remove completely empty rows
        
        Args:
            raw_data: Raw extracted data from pdfplumber
            
        Returns:
            Cleaned data as list of lists of strings
        """
        cleaned = []
        
        for row in raw_data:
            cleaned_row = []
            
            for cell in row:
                # Handle None
                if cell is None:
                    cleaned_row.append("")
                    continue
                
                # Convert to string
                cell_str = str(cell)
                
                # Normalize whitespace
                # Replace newlines and multiple spaces with single space
                cell_str = re.sub(r'\s+', ' ', cell_str)
                
                # Strip leading/trailing whitespace
                cell_str = cell_str.strip()
                
                cleaned_row.append(cell_str)
            
            # Only include row if it has at least one non-empty cell
            if any(cell for cell in cleaned_row):
                cleaned.append(cleaned_row)
        
        return cleaned