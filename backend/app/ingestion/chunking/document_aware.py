"""
Document-Aware Chunker
======================

Chunks documents while respecting their structure.

Unlike recursive chunking which just looks at text, this chunker:
1. Detects headers/sections
2. Keeps headers with their content
3. Preserves section hierarchy in metadata
4. Handles tables as single chunks
5. Keeps lists together when possible

This produces better chunks for structured documents like:
- Contracts (sections, clauses)
- Manuals (chapters, procedures)
- Reports (executive summary, findings, recommendations)
- Policies (sections, subsections)
"""

import re
from typing import Optional

from .base import BaseChunker
from .recursive import RecursiveChunker
from .models import Chunk, ChunkMetadata
from ..parsers.base import ParsedDocument


class DocumentAwareChunker(BaseChunker):
    """
    Structure-aware document chunker.
    
    Detects document structure and creates chunks that respect
    section boundaries while maintaining context.
    
    Usage:
        chunker = DocumentAwareChunker(chunk_size=1000)
        chunks = chunker.chunk_document(parsed_doc, document_id="doc_123")
        
        # Each chunk knows its section
        for chunk in chunks:
            print(f"Section: {chunk.metadata.section_title}")
            print(f"Hierarchy: {chunk.metadata.section_hierarchy}")
    """
    
    # Patterns for detecting headers
    # These cover common document formats
    HEADER_PATTERNS = [
        # Markdown-style headers
        r'^(#{1,6})\s+(.+)$',
        
        # Numbered sections: "1.", "1.1", "1.1.1", "Section 1:"
        r'^(\d+(?:\.\d+)*\.?)\s+(.+)$',
        r'^(?:Section|Chapter|Part|Article)\s+(\d+(?:\.\d+)*):?\s*(.*)$',
        
        # UPPERCASE HEADERS
        r'^([A-Z][A-Z\s]{2,})$',
        
        # Headers ending with colon
        r'^([A-Z][A-Za-z\s]+):$',
    ]
    
    # Patterns for detecting tables (already formatted)
    TABLE_PATTERNS = [
        r'^\|.+\|$',  # Markdown table row
        r'^[\w\s]+\s*\|\s*[\w\s]+',  # Pipe-separated values
        r'^=== Sheet:',  # Our Excel sheet marker
    ]
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        preserve_tables: bool = True,
        preserve_lists: bool = True
    ):
        """
        Initialize document-aware chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size to keep
            preserve_tables: Keep tables as single chunks
            preserve_lists: Keep lists together when possible
        """
        super().__init__(chunk_size, chunk_overlap, min_chunk_size)
        self.preserve_tables = preserve_tables
        self.preserve_lists = preserve_lists
        
        # Fallback chunker for when sections are too large
        self.recursive_chunker = RecursiveChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size
        )
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        document_name: str,
        base_metadata: Optional[dict] = None
    ) -> list[Chunk]:
        """
        Split text into structure-aware chunks.
        
        Args:
            text: Text to split
            document_id: Document identifier
            document_name: Document filename
            base_metadata: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []
        
        # Parse document structure
        sections = self._parse_sections(text)
        
        # Convert sections to chunks
        chunks = []
        chunk_index = 0
        
        for section in sections:
            section_chunks = self._section_to_chunks(
                section=section,
                document_id=document_id,
                document_name=document_name,
                start_index=chunk_index
            )
            
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)
        
        # Update total counts
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def chunk_document(
        self,
        document: ParsedDocument,
        document_id: str
    ) -> list[Chunk]:
        """
        Split a ParsedDocument into structure-aware chunks.
        
        Args:
            document: ParsedDocument from parser
            document_id: Document identifier
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_index = 0
        current_hierarchy = []
        
        for page_num, page_text in enumerate(document.pages):
            if not page_text.strip():
                continue
            
            # Parse sections on this page
            sections = self._parse_sections(page_text)
            
            for section in sections:
                # Update hierarchy based on section level
                if section["title"]:
                    level = section.get("level", 0)
                    # Trim hierarchy to current level and add new title
                    current_hierarchy = current_hierarchy[:level]
                    current_hierarchy.append(section["title"])
                
                section_chunks = self._section_to_chunks(
                    section=section,
                    document_id=document_id,
                    document_name=document.metadata.filename,
                    start_index=chunk_index,
                    page_number=page_num,
                    hierarchy=current_hierarchy.copy()
                )
                
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
        
        # Update total counts
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _parse_sections(self, text: str) -> list[dict]:
        """
        Parse text into sections based on headers.
        
        Returns list of dicts:
        {
            "title": "Section Title" or None,
            "level": 0-5 (header level),
            "content": "Section content...",
            "content_type": "text" | "table" | "list"
        }
        """
        sections = []
        current_section = {
            "title": None,
            "level": 0,
            "content": "",
            "content_type": "text"
        }
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a header
            header_match = self._detect_header(line)
            
            if header_match:
                # Save current section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": header_match["title"],
                    "level": header_match["level"],
                    "content": "",
                    "content_type": "text"
                }
                i += 1
                continue
            
            # Check if this is a table
            if self.preserve_tables and self._is_table_line(line):
                # Save current section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Collect entire table
                table_lines = []
                while i < len(lines) and self._is_table_line(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                
                # Create table section
                sections.append({
                    "title": None,
                    "level": current_section["level"],
                    "content": '\n'.join(table_lines),
                    "content_type": "table"
                })
                
                # Start new section for content after table
                current_section = {
                    "title": None,
                    "level": current_section["level"],
                    "content": "",
                    "content_type": "text"
                }
                continue
            
            # Check if this is a list item
            if self.preserve_lists and self._is_list_item(line):
                # Collect entire list
                list_lines = [line]
                i += 1
                while i < len(lines) and (self._is_list_item(lines[i]) or lines[i].startswith('  ')):
                    list_lines.append(lines[i])
                    i += 1
                
                # Add list to current section content
                current_section["content"] += '\n'.join(list_lines) + '\n'
                continue
            
            # Regular content line
            current_section["content"] += line + '\n'
            i += 1
        
        # Don't forget last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def _detect_header(self, line: str) -> Optional[dict]:
        """
        Detect if a line is a header.
        
        Returns:
            {"title": "Header Text", "level": 0-5} or None
        """
        line = line.strip()
        
        if not line:
            return None
        
        # Markdown headers: # Header, ## Header, etc.
        md_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if md_match:
            level = len(md_match.group(1)) - 1  # 0-indexed
            return {"title": md_match.group(2).strip(), "level": level}
        
        # Numbered sections: 1. Title, 1.1 Title, etc.
        num_match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.+)$', line)
        if num_match:
            # Count dots to determine level
            level = num_match.group(1).count('.')
            return {"title": f"{num_match.group(1)} {num_match.group(2)}".strip(), "level": level}
        
        # Chapter/Section/Part headers
        sec_match = re.match(r'^(?:Section|Chapter|Part|Article)\s+(\d+(?:\.\d+)*):?\s*(.*)$', line, re.IGNORECASE)
        if sec_match:
            title = f"Section {sec_match.group(1)}"
            if sec_match.group(2):
                title += f": {sec_match.group(2)}"
            return {"title": title, "level": 0}
        
        # ALL CAPS headers (at least 3 chars, mostly letters)
        if len(line) >= 3 and line.isupper() and sum(c.isalpha() for c in line) / len(line) > 0.7:
            return {"title": line, "level": 0}
        
        return None
    
    def _is_table_line(self, line: str) -> bool:
        """Check if a line is part of a table."""
        line = line.strip()
        
        if not line:
            return False
        
        # Markdown table
        if line.startswith('|') and line.endswith('|'):
            return True
        
        # Markdown separator row
        if re.match(r'^[\|\s\-:]+$', line):
            return True
        
        # Our Excel format
        if line.startswith('=== Sheet:'):
            return True
        
        # Pipe-separated with multiple columns
        if '|' in line and line.count('|') >= 2:
            return True
        
        return False
    
    def _is_list_item(self, line: str) -> bool:
        """Check if a line is a list item."""
        line = line.strip()
        
        if not line:
            return False
        
        # Bullet lists: -, *, •
        if re.match(r'^[\-\*\•]\s+', line):
            return True
        
        # Numbered lists: 1., 1), a., a)
        if re.match(r'^(\d+[\.\)]|[a-zA-Z][\.\)])\s+', line):
            return True
        
        return False
    
    def _section_to_chunks(
        self,
        section: dict,
        document_id: str,
        document_name: str,
        start_index: int,
        page_number: Optional[int] = None,
        hierarchy: Optional[list[str]] = None
    ) -> list[Chunk]:
        """
        Convert a section to one or more chunks.
        
        If section is small enough, it becomes one chunk.
        If too large, it's split using recursive chunker.
        """
        content = section["content"].strip()
        title = section["title"]
        content_type = section["content_type"]
        
        if not content:
            return []
        
        # Add header to content for context
        if title:
            content_with_header = f"{title}\n\n{content}"
        else:
            content_with_header = content
        
        # If content fits in one chunk, keep it together
        if len(content_with_header) <= self.chunk_size:
            chunk = self._create_chunk(
                content=content_with_header,
                document_id=document_id,
                document_name=document_name,
                chunk_index=start_index,
                page_number=page_number,
                section_title=title,
                section_hierarchy=hierarchy,
                content_type=content_type
            )
            return [chunk]
        
        # Content too large - need to split
        # For tables, keep as single chunk even if large (LLM needs full table)
        if content_type == "table":
            chunk = self._create_chunk(
                content=content_with_header,
                document_id=document_id,
                document_name=document_name,
                chunk_index=start_index,
                page_number=page_number,
                section_title=title,
                section_hierarchy=hierarchy,
                content_type="table"
            )
            return [chunk]
        
        # Use recursive chunker for large text sections
        text_chunks = self.recursive_chunker._split_text(
            content_with_header,
            self.recursive_chunker.separators
        )
        
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = self._create_chunk(
                content=chunk_text,
                document_id=document_id,
                document_name=document_name,
                chunk_index=start_index + i,
                page_number=page_number,
                section_title=title,
                section_hierarchy=hierarchy,
                content_type=content_type
            )
            chunks.append(chunk)
        
        return chunks