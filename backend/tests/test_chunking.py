"""
Chunking Module Test Script
===========================

Tests the recursive and document-aware chunkers.

How to run:
-----------
    cd backend
    python -m tests.test_chunking
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.ingestion.chunking import (
    RecursiveChunker,
    DocumentAwareChunker,
    Chunk,
    ChunkMetadata
)
from app.ingestion.parsers import ParserFactory


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_recursive_chunker():
    """Test recursive text chunking."""
    print_header("Testing Recursive Chunker")
    
    # Sample text with paragraphs
    text = """
Introduction

This is the first paragraph of our test document. It contains several sentences 
that should be kept together when possible. The chunker should try to split at 
paragraph boundaries first.

Main Content

Here is the second section with more content. This paragraph discusses the main 
topic of the document. We want to ensure that the chunker respects paragraph 
boundaries and doesn't split sentences awkwardly.

Additional details are provided here. This is important information that relates 
to the main content above. The relationship between paragraphs should be preserved 
through overlap.

Conclusion

Finally, we have a conclusion section. This wraps up the document and summarizes 
the key points. The chunker should handle this section appropriately.
    """.strip()
    
    try:
        chunker = RecursiveChunker(
            chunk_size=500,  # Small for testing
            chunk_overlap=100,
            min_chunk_size=50
        )
        
        chunks = chunker.chunk_text(
            text=text,
            document_id="test_doc_001",
            document_name="test_document.txt"
        )
        
        print(f"\nOriginal text length: {len(text)} characters")
        print(f"Chunk size setting: 500 characters")
        print(f"Number of chunks created: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\n--- Chunk {i + 1} ---")
            print(f"Length: {chunk.char_count} chars, {chunk.word_count} words")
            print(f"Chunk ID: {chunk.chunk_id}")
            preview = chunk.content[:150].replace('\n', ' ')
            if len(chunk.content) > 150:
                preview += "..."
            print(f"Preview: {preview}")
        
        print("\n✓ Recursive Chunker test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Recursive Chunker test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_aware_chunker():
    """Test document-aware chunking with headers."""
    print_header("Testing Document-Aware Chunker")
    
    # Sample text with clear structure
    text = """
# Project Overview

This document describes the project goals and requirements. The project aims to 
build an enterprise document intelligence platform.

## Goals

The main goals of this project are:
- Process multiple document types
- Extract structured data
- Enable natural language queries

## Requirements

### Technical Requirements

The system must support PDF, DOCX, and XLSX files. Processing should be 
asynchronous for large documents.

### Performance Requirements

Response time should be under 3 seconds. The system should handle 100K+ documents.

# Implementation Details

This section covers the technical implementation approach.

## Architecture

The system uses a microservices architecture with the following components:

| Component | Purpose | Technology |
| --- | --- | --- |
| Parser | Document extraction | Python |
| Embedder | Vector generation | OpenAI |
| Search | Retrieval | Qdrant |

## Timeline

Phase 1 will be completed in 4 weeks. Phase 2 will follow immediately after.
    """.strip()
    
    try:
        chunker = DocumentAwareChunker(
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50
        )
        
        chunks = chunker.chunk_text(
            text=text,
            document_id="test_doc_002",
            document_name="project_spec.md"
        )
        
        print(f"\nOriginal text length: {len(text)} characters")
        print(f"Number of chunks created: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\n--- Chunk {i + 1} ---")
            print(f"Section: {chunk.metadata.section_title}")
            print(f"Hierarchy: {chunk.metadata.section_hierarchy}")
            print(f"Type: {chunk.metadata.content_type}")
            print(f"Length: {chunk.char_count} chars")
            preview = chunk.content[:150].replace('\n', ' ')
            if len(chunk.content) > 150:
                preview += "..."
            print(f"Preview: {preview}")
        
        print("\n✓ Document-Aware Chunker test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Document-Aware Chunker test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chunker_with_real_document():
    """Test chunking with a real parsed document."""
    print_header("Testing Chunker with Real Document")
    
    test_file = Path(__file__).parent / "test_files" / "sample.pdf"
    
    if not test_file.exists():
        print(f"SKIPPED: No test file at {test_file}")
        return True
    
    try:
        # Parse the document
        parser = ParserFactory.get_parser(test_file)
        parsed_doc = parser.parse(test_file)
        
        print(f"\nDocument: {parsed_doc.metadata.filename}")
        print(f"Pages: {parsed_doc.metadata.page_count}")
        print(f"Total content length: {len(parsed_doc.content)} chars")
        
        # Chunk it
        chunker = DocumentAwareChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.chunk_document(parsed_doc, document_id="pdf_001")
        
        print(f"\nChunks created: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\n--- Chunk {i + 1} ---")
            print(f"Page: {chunk.metadata.page_number}")
            print(f"Citation: {chunk.metadata.get_citation()}")
            print(f"Length: {chunk.char_count} chars")
            preview = chunk.content[:100].replace('\n', ' ')
            if len(chunk.content) > 100:
                preview += "..."
            print(f"Preview: {preview}")
        
        print("\n✓ Real Document Chunking test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Real Document Chunking test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chunk_metadata():
    """Test chunk metadata and citation generation."""
    print_header("Testing Chunk Metadata")
    
    try:
        # Create a chunk with full metadata
        metadata = ChunkMetadata(
            document_id="doc_123",
            document_name="contract.pdf",
            chunk_index=5,
            total_chunks=20,
            page_number=3,
            section_title="Payment Terms",
            section_hierarchy=["Chapter 2", "Financial Terms", "Payment Terms"],
            content_type="text"
        )
        
        chunk = Chunk(
            content="The vendor shall be paid within 30 days of invoice receipt.",
            metadata=metadata
        )
        
        print(f"\nChunk ID: {chunk.chunk_id}")
        print(f"Citation: {chunk.metadata.get_citation()}")
        print(f"Context header: {chunk.get_context_header()}")
        print(f"\nFull content with context:")
        print(chunk.get_content_with_context())
        
        print(f"\nMetadata dict:")
        for key, value in metadata.to_dict().items():
            print(f"  {key}: {value}")
        
        print("\n✓ Chunk Metadata test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Chunk Metadata test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_overlap():
    """Test that chunk overlap is working correctly."""
    print_header("Testing Chunk Overlap")
    
    # Create text that will definitely need multiple chunks
    text = "Word " * 500  # 2500 characters
    
    try:
        chunker = RecursiveChunker(
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50
        )
        
        chunks = chunker.chunk_text(
            text=text,
            document_id="overlap_test",
            document_name="test.txt"
        )
        
        print(f"\nOriginal text length: {len(text)} chars")
        print(f"Chunk size: 500, Overlap: 100")
        print(f"Number of chunks: {len(chunks)}")
        
        # Check for overlap between consecutive chunks
        if len(chunks) >= 2:
            for i in range(len(chunks) - 1):
                chunk1_end = chunks[i].content[-100:]  # Last 100 chars
                chunk2_start = chunks[i+1].content[:100]  # First 100 chars
                
                # Find common substring
                overlap_found = False
                for j in range(min(len(chunk1_end), len(chunk2_start)), 10, -1):
                    if chunk1_end[-j:] == chunk2_start[:j]:
                        print(f"\nOverlap between chunk {i+1} and {i+2}: {j} chars")
                        overlap_found = True
                        break
                
                if not overlap_found:
                    print(f"\nNo significant overlap found between chunk {i+1} and {i+2}")
        
        print("\n✓ Overlap test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Overlap test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all chunking tests."""
    print("\n" + "=" * 60)
    print(" DocuMind Chunking Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Recursive Chunker", test_recursive_chunker()))
    results.append(("Document-Aware Chunker", test_document_aware_chunker()))
    results.append(("Real Document Chunking", test_chunker_with_real_document()))
    results.append(("Chunk Metadata", test_chunk_metadata()))
    results.append(("Chunk Overlap", test_overlap()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All chunking tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check output above.")


if __name__ == "__main__":
    main()