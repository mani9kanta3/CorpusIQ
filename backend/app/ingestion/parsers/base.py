"""
Base Parser Interface for Document Processing
=============================================

This module defines the contract that ALL document parsers must follow.

Why do we need this?
--------------------
Imagine you're building a food delivery app. You have restaurants that serve
different cuisines - Italian, Chinese, Indian. Each restaurant is different,
but they ALL must:
- Accept orders
- Prepare food
- Package it
- Hand it to the delivery person

The "interface" defines WHAT they must do, not HOW they do it.

Similarly, our parsers (PDF, DOCX, XLSX) are all different, but they ALL must:
- Parse the document
- Extract metadata
- Return a consistent format

This is called "programming to an interface" - a fundamental design principle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class DocumentMetadata:
    """
    Stores metadata about a document.
    
    Why @dataclass?
    ---------------
    A dataclass automatically generates:
    - __init__() method (constructor)
    - __repr__() method (for printing)
    - __eq__() method (for comparison)
    
    Without @dataclass, we'd have to write:
    
        class DocumentMetadata:
            def __init__(self, filename, file_type, file_size_bytes, ...):
                self.filename = filename
                self.file_type = file_type
                self.file_size_bytes = file_size_bytes
                # ... and so on for every field
    
    @dataclass does this automatically. Less code, fewer bugs.
    
    Attributes:
        filename: Original name of the uploaded file (e.g., "contract.pdf")
        file_type: Type of file (e.g., "pdf", "docx", "xlsx")
        file_size_bytes: Size in bytes (used for upload limits, storage planning)
        page_count: Number of pages (None for formats without pages, like .txt)
        created_at: When the document was originally created (from file metadata)
        modified_at: When the document was last modified
        author: Document author (if available in metadata)
        title: Document title (if available in metadata)
    """
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: Optional[int] = None       # Optional because .txt files don't have pages
    created_at: Optional[datetime] = None  # Optional because not all files have this
    modified_at: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None


@dataclass 
class ParsedDocument:
    """
    The result of parsing a document.
    
    This is what every parser returns after processing a file.
    
    Why separate 'content' and 'pages'?
    -----------------------------------
    - 'content': The full text of the document as one string.
                 Used for: generating embeddings, full-text search
    
    - 'pages': A list where each item is the text from one page.
               Used for: citations! When we tell the user "this answer came 
               from page 5", we need to know what text was on page 5.
    
    Example:
        If a PDF has 3 pages:
        - content = "Page 1 text... Page 2 text... Page 3 text..."
        - pages = ["Page 1 text...", "Page 2 text...", "Page 3 text..."]
    
    Attributes:
        content: Full extracted text as a single string
        metadata: DocumentMetadata object with file information
        pages: List of strings, one per page (empty list for non-paged formats)
    """
    content: str
    metadata: DocumentMetadata
    pages: list[str]


class BaseParser(ABC):
    """
    Abstract Base Class for all document parsers.
    
    What is ABC (Abstract Base Class)?
    ----------------------------------
    ABC is Python's way of creating an "interface" or "contract".
    
    When a class inherits from ABC and has @abstractmethod decorators,
    Python ENFORCES that any subclass MUST implement those methods.
    
    Example:
        class PDFParser(BaseParser):
            pass  # Forgot to implement parse() and extract_metadata()
        
        parser = PDFParser()  # ERROR! Python won't allow this.
    
    This catches bugs early. If you forget to implement a required method,
    Python tells you immediately instead of failing at runtime.
    
    Why not just use a regular class?
    ---------------------------------
    With a regular class, you could forget to implement a method and Python
    wouldn't complain until that method is actually called - maybe in production,
    maybe weeks later. ABC catches this at class definition time.
    
    SUPPORTED_EXTENSIONS:
        Each parser subclass will define what file types it handles.
        PDFParser will set: SUPPORTED_EXTENSIONS = ['.pdf']
        DocxParser will set: SUPPORTED_EXTENSIONS = ['.docx']
    """
    
    SUPPORTED_EXTENSIONS: list[str] = []
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a document and extract all content.
        
        This is the main method. It reads the entire document and extracts:
        - All text content
        - All metadata
        - Page-by-page breakdown
        
        Args:
            file_path: Path object pointing to the file
                       (Path is better than str - it has useful methods like
                        .exists(), .suffix, .name, etc.)
        
        Returns:
            ParsedDocument with all extracted information
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file type isn't supported by this parser
            Exception: If parsing fails for any reason
        
        Note:
            The 'pass' here doesn't mean "do nothing". Combined with
            @abstractmethod, it means "subclasses MUST override this".
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract ONLY metadata, without parsing full content.
        
        Why have this separate from parse()?
        ------------------------------------
        Sometimes you just need quick info about a file:
        - How many pages?
        - How big is it?
        - When was it created?
        
        Full parsing can be slow for large documents. This method gives you
        the quick stuff without the heavy lifting.
        
        Use case: Showing a document list in the UI. You want to display
        "contract.pdf - 50 pages - 2.5MB" without reading all 50 pages.
        
        Args:
            file_path: Path to the document
        
        Returns:
            DocumentMetadata object
        """
        pass
    
    def validate_file(self, file_path: Path) -> None:
        """
        Check if file exists and is a supported type.
        
        This is a concrete method (not abstract) - it has actual implementation.
        Subclasses inherit this as-is, no need to override.
        
        Why validate?
        -------------
        1. Security: Don't try to open files that don't exist
        2. Clarity: Give clear error messages instead of cryptic failures
        3. Fail fast: Catch problems before wasting time on processing
        
        Args:
            file_path: Path to validate
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file extension not in SUPPORTED_EXTENSIONS
        """
        # Check 1: Does the file exist?
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check 2: Is it a supported file type?
        # file_path.suffix gives us the extension: ".pdf", ".docx", etc.
        # .lower() handles cases like ".PDF" or ".Pdf"
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {file_extension}. "
                f"Supported types: {self.SUPPORTED_EXTENSIONS}"
            )
    
    def _get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Why the underscore prefix?
        --------------------------
        In Python, a single underscore prefix (_method) is a convention meaning
        "this is internal/private - use it within the class, but external code
        shouldn't rely on it."
        
        It's not enforced by Python (you CAN still call it from outside),
        but it signals intent to other developers.
        
        Args:
            file_path: Path to the file
        
        Returns:
            File size in bytes as an integer
        """
        # .stat() returns file statistics
        # .st_size is the size in bytes
        return file_path.stat().st_size
    
    def _get_file_extension(self, file_path: Path) -> str:
        """
        Get the file extension without the dot.
        
        Example: 
            Path("document.pdf").suffix returns ".pdf"
            This method returns "pdf" (without the dot)
        
        Args:
            file_path: Path to the file
        
        Returns:
            Extension string without the dot (e.g., "pdf", "docx")
        """
        # [1:] slices off the first character (the dot)
        # ".pdf"[1:] = "pdf"
        return file_path.suffix.lower()[1:]