"""
Table Formatter
===============

Converts extracted tables into formats optimized for LLM consumption.

Why formatting matters:
-----------------------
LLMs understand some formats better than others:

1. Markdown tables: Good balance of readability and structure
2. JSON: Precise, but verbose and uses many tokens
3. Plain text with separators: Simple, but can lose structure
4. HTML: Verbose, wastes tokens

We primarily use Markdown because:
- LLMs are trained on lots of Markdown
- Compact representation
- Preserves row/column relationships
- Human-readable for debugging

For complex tables or when precise data access is needed, JSON is better.
"""

from typing import Optional
from .extractor import ExtractedTable


class TableFormatter:
    """
    Formats tables for different use cases.
    
    Usage:
        formatter = TableFormatter()
        
        # For LLM context
        markdown = formatter.to_llm_context(table, include_summary=True)
        
        # For structured output
        json_data = formatter.to_json(table)
        
        # Multiple tables
        combined = formatter.format_multiple_tables(tables)
    """
    
    def to_llm_context(
        self,
        table: ExtractedTable,
        include_summary: bool = True,
        max_rows: Optional[int] = None
    ) -> str:
        """
        Format table for inclusion in LLM context/prompt.
        
        Creates a format that helps LLMs understand and reference the table.
        
        Args:
            table: ExtractedTable object
            include_summary: Add a brief description of the table
            max_rows: Limit rows (for large tables). None = all rows
            
        Returns:
            Formatted string ready for LLM context
        """
        parts = []
        
        # Summary helps LLM understand what the table contains
        if include_summary:
            summary = self._generate_summary(table)
            parts.append(summary)
        
        # The actual table in Markdown
        if max_rows and len(table.rows) > max_rows:
            # Truncate large tables
            truncated_table = ExtractedTable(
                page_number=table.page_number,
                headers=table.headers,
                rows=table.rows[:max_rows],
                raw_data=table.raw_data,
                bbox=table.bbox,
                table_index=table.table_index
            )
            parts.append(truncated_table.to_markdown())
            parts.append(f"... ({len(table.rows) - max_rows} more rows)")
        else:
            parts.append(table.to_markdown())
        
        return "\n".join(parts)
    
    def _generate_summary(self, table: ExtractedTable) -> str:
        """
        Generate a brief summary of the table.
        
        This helps LLMs understand context without reading every cell.
        
        Args:
            table: ExtractedTable object
            
        Returns:
            Summary string
        """
        col_list = ", ".join(table.headers[:5])  # First 5 columns
        if len(table.headers) > 5:
            col_list += f", ... ({len(table.headers) - 5} more columns)"
        
        return (
            f"[Table from page {table.page_number + 1}: "
            f"{table.row_count} rows × {table.col_count} columns. "
            f"Columns: {col_list}]"
        )
    
    def to_json(self, table: ExtractedTable) -> dict:
        """
        Convert table to JSON-serializable dictionary.
        
        Better for programmatic access and APIs.
        
        Args:
            table: ExtractedTable object
            
        Returns:
            Dictionary with table data
        """
        return table.to_dict()
    
    def to_row_dicts(self, table: ExtractedTable) -> list[dict]:
        """
        Convert table to list of row dictionaries.
        
        Each row becomes a dict with column names as keys.
        Useful for data processing and APIs.
        
        Example output:
            [
                {"Name": "Alice", "Age": "30", "City": "New York"},
                {"Name": "Bob", "Age": "25", "City": "London"}
            ]
        
        Args:
            table: ExtractedTable object
            
        Returns:
            List of dictionaries
        """
        return [table.get_row(i) for i in range(table.row_count)]
    
    def format_multiple_tables(
        self,
        tables: list[ExtractedTable],
        separator: str = "\n\n---\n\n"
    ) -> str:
        """
        Format multiple tables into a single string.
        
        Useful when a document has several tables that need to be
        included in LLM context together.
        
        Args:
            tables: List of ExtractedTable objects
            separator: String to put between tables
            
        Returns:
            Combined formatted string
        """
        if not tables:
            return ""
        
        formatted_tables = []
        
        for i, table in enumerate(tables):
            header = f"### Table {i + 1} (Page {table.page_number + 1})"
            content = self.to_llm_context(table, include_summary=True)
            formatted_tables.append(f"{header}\n\n{content}")
        
        return separator.join(formatted_tables)
    
    def to_plain_text(
        self,
        table: ExtractedTable,
        cell_separator: str = " | ",
        row_separator: str = "\n"
    ) -> str:
        """
        Convert table to plain text format.
        
        Simpler than Markdown, useful for basic text processing.
        
        Args:
            table: ExtractedTable object
            cell_separator: String between cells
            row_separator: String between rows
            
        Returns:
            Plain text representation
        """
        lines = []
        
        # Header
        lines.append(cell_separator.join(table.headers))
        
        # Rows
        for row in table.rows:
            # Pad row to match header length
            padded = row + [""] * (len(table.headers) - len(row))
            lines.append(cell_separator.join(padded[:len(table.headers)]))
        
        return row_separator.join(lines)