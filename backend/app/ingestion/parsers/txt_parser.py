"""
Plain Text Parser

The simplest parser. Text files have no structure - just raw text.

Handles:
- .txt files
- .md files (Markdown - we treat as plain text for now)
- .csv files (basic handling - we'll improve in table extraction module)

Why include .md and .csv?
-------------------------
- Markdown (.md): It's just text with formatting symbols. For our RAG system,
  we care about the words, not the formatting. "# Header" is still the word "Header".
  
- CSV (.csv): While CSVs are structured, for basic ingestion we can read them
  as text. The table extraction module will handle them properly later.

No external libraries needed - Python's built-in file handling is enough.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import os

from .base import BaseParser, DocumentMetadata, ParsedDocument


class TextParser(BaseParser):
    """
    Parser for plain text files.
    
    Since text files have no pages, we split by paragraphs (double newlines)
    to create our "pages" list for citation purposes.
    
    Encoding handling:
    ------------------
    Text files can be encoded in different formats:
    - UTF-8 (most common, supports all languages)
    - Latin-1 (older Western European)
    - ASCII (basic English only)
    
    We try UTF-8 first, then fall back to Latin-1 which accepts any byte.
    
    Usage:
        parser = TextParser()
        result = parser.parse(Path("notes.txt"))
    """
    
    SUPPORTED_EXTENSIONS = [".txt", ".md", ".csv"]
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            ParsedDocument with content split into paragraphs
        """
        self.validate_file(file_path)
        
        try:
            # Read file content with encoding handling
            content = self._read_file_content(file_path)
            
            # Split into paragraphs for our "pages" list
            paragraphs = self._split_into_paragraphs(content)
            
            # Extract metadata
            metadata = self._extract_file_metadata(file_path, content)
            
            return ParsedDocument(
                content=content,
                metadata=metadata,
                pages=paragraphs
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to parse text file '{file_path}': {str(e)}")
    
    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from text file.
        
        Text files don't have embedded metadata like PDF/DOCX.
        We can only get file system info (size, dates).
        
        Args:
            file_path: Path to the text file
            
        Returns:
            DocumentMetadata object
        """
        self.validate_file(file_path)
        
        try:
            # We need to read the file to count paragraphs
            content = self._read_file_content(file_path)
            return self._extract_file_metadata(file_path, content)
        except Exception as e:
            raise RuntimeError(f"Failed to extract metadata from '{file_path}': {str(e)}")
    
    def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content with encoding detection.
        
        Why try multiple encodings?
        ---------------------------
        If someone created a file on an old Windows system, it might be
        encoded in Latin-1. If we try to read it as UTF-8, we get errors.
        
        Strategy:
        1. Try UTF-8 (most common, correct for most files)
        2. Fall back to Latin-1 (accepts any byte sequence)
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string
        """
        # Try UTF-8 first
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Fall back to Latin-1
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
    
    def _split_into_paragraphs(self, content: str) -> list[str]:
        """
        Split content into paragraphs.
        
        A paragraph is defined as text separated by blank lines.
        
        Example:
            "First paragraph.\n\nSecond paragraph.\n\nThird."
            
            Becomes: ["First paragraph.", "Second paragraph.", "Third."]
        
        Args:
            content: Full text content
            
        Returns:
            List of non-empty paragraphs
        """
        # Split on double newlines (blank lines)
        # This handles both Unix (\n) and Windows (\r\n) line endings
        raw_paragraphs = content.split("\n\n")
        
        # Clean up and filter empty paragraphs
        paragraphs = []
        for para in raw_paragraphs:
            # Strip whitespace and normalize internal newlines
            cleaned = para.strip()
            if cleaned:
                paragraphs.append(cleaned)
        
        # If no paragraphs found (no double newlines), treat whole content as one
        if not paragraphs and content.strip():
            paragraphs = [content.strip()]
        
        return paragraphs
    
    def _extract_file_metadata(
        self, 
        file_path: Path, 
        content: str
    ) -> DocumentMetadata:
        """
        Extract metadata from file system.
        
        Text files don't have embedded metadata, so we use:
        - File system timestamps (created, modified)
        - Paragraph count as "page count"
        - Filename
        
        Args:
            file_path: Path to the file
            content: File content (needed for paragraph count)
            
        Returns:
            DocumentMetadata object
        """
        # Get file stats
        file_stats = file_path.stat()
        
        # Paragraph count for our "page count"
        paragraphs = self._split_into_paragraphs(content)
        
        # Get timestamps
        # st_mtime = modification time (Unix timestamp)
        # st_ctime = creation time on Windows, metadata change time on Unix
        modified_at = datetime.fromtimestamp(file_stats.st_mtime)
        created_at = datetime.fromtimestamp(file_stats.st_ctime)
        
        return DocumentMetadata(
            filename=file_path.name,
            file_type=self._get_file_extension(file_path),
            file_size_bytes=self._get_file_size(file_path),
            page_count=len(paragraphs),
            created_at=created_at,
            modified_at=modified_at,
            author=None,  # Text files don't have author info
            title=None    # Text files don't have title info
        )