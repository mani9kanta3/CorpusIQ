"""
Parser Factory
==============

Central router that selects the correct parser based on file type.

Why use a Factory pattern?
--------------------------
1. ENCAPSULATION: Parser selection logic lives in ONE place
2. EXTENSIBILITY: Add new parsers without changing other code
3. SIMPLICITY: Callers just ask for "a parser" - they don't care which one

How to add a new parser:
------------------------
1. Create the parser class (e.g., HTMLParser)
2. Import it in this file
3. Add it to PARSER_REGISTRY
4. Done! The factory automatically handles it.

Usage:
    from app.ingestion.parsers.factory import ParserFactory
    
    # Get parser for a file
    parser = ParserFactory.get_parser(Path("document.pdf"))
    result = parser.parse(Path("document.pdf"))
    
    # Check if file type is supported
    if ParserFactory.is_supported(Path("file.xyz")):
        parser = ParserFactory.get_parser(Path("file.xyz"))
"""

from pathlib import Path
from typing import Optional

from .base import BaseParser
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .xlsx_parser import XLSXParser
from .txt_parser import TextParser


# =============================================================================
# PARSER REGISTRY
# =============================================================================
# This is where all parsers are registered.
# To add a new parser: just add it to this list.

PARSER_REGISTRY: list[type[BaseParser]] = [
    PDFParser,
    DOCXParser,
    XLSXParser,
    TextParser,
]


class ParserFactory:
    """
    Factory class for creating document parsers.
    
    This class uses static methods because:
    - It doesn't need to store any state
    - It's just a collection of utility functions
    - You don't need to create an instance: ParserFactory.get_parser(...)
    
    Class methods vs Instance methods:
    ----------------------------------
    Instance method: needs an object first
        factory = ParserFactory()
        parser = factory.get_parser(path)
    
    Static method: no object needed
        parser = ParserFactory.get_parser(path)
    
    For a factory with no state, static methods are cleaner.
    """
    
    @staticmethod
    def get_parser(file_path: Path) -> BaseParser:
        """
        Get the appropriate parser for a file.
        
        How it works:
        1. Extract file extension (.pdf, .docx, etc.)
        2. Look through all registered parsers
        3. Find one that supports this extension
        4. Return an instance of that parser
        
        Args:
            file_path: Path to the file (can be string or Path object)
            
        Returns:
            Instance of the appropriate parser
            
        Raises:
            ValueError: If no parser supports this file type
            
        Example:
            parser = ParserFactory.get_parser(Path("report.pdf"))
            # Returns: PDFParser instance
        """
        # Ensure we have a Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Get extension in lowercase
        extension = file_path.suffix.lower()
        
        # Search through registered parsers
        for parser_class in PARSER_REGISTRY:
            if extension in parser_class.SUPPORTED_EXTENSIONS:
                # Found a match! Create and return an instance
                return parser_class()
        
        # No parser found for this extension
        supported = ParserFactory.get_supported_extensions()
        raise ValueError(
            f"No parser available for '{extension}' files. "
            f"Supported formats: {supported}"
        )
    
    @staticmethod
    def is_supported(file_path: Path) -> bool:
        """
        Check if a file type is supported.
        
        Useful for validation before attempting to parse.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if a parser exists for this file type
            
        Example:
            if ParserFactory.is_supported(uploaded_file):
                parser = ParserFactory.get_parser(uploaded_file)
            else:
                raise HTTPException(400, "Unsupported file type")
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        extension = file_path.suffix.lower()
        
        for parser_class in PARSER_REGISTRY:
            if extension in parser_class.SUPPORTED_EXTENSIONS:
                return True
        
        return False
    
    @staticmethod
    def get_supported_extensions() -> list[str]:
        """
        Get list of all supported file extensions.
        
        Useful for:
        - Displaying to users: "Supported formats: .pdf, .docx, .xlsx, .txt"
        - File upload validation
        - API documentation
        
        Returns:
            List of extensions like ['.pdf', '.docx', '.xlsx', '.txt', '.md', '.csv']
        """
        extensions = []
        for parser_class in PARSER_REGISTRY:
            extensions.extend(parser_class.SUPPORTED_EXTENSIONS)
        return extensions
    
    @staticmethod
    def get_parser_for_extension(extension: str) -> Optional[BaseParser]:
        """
        Get parser by extension string directly.
        
        Sometimes you have just the extension, not a full path.
        
        Args:
            extension: File extension with or without dot ('.pdf' or 'pdf')
            
        Returns:
            Parser instance or None if not supported
            
        Example:
            parser = ParserFactory.get_parser_for_extension('.pdf')
            parser = ParserFactory.get_parser_for_extension('pdf')  # Also works
        """
        # Normalize: ensure it starts with a dot
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        extension = extension.lower()
        
        for parser_class in PARSER_REGISTRY:
            if extension in parser_class.SUPPORTED_EXTENSIONS:
                return parser_class()
        
        return None