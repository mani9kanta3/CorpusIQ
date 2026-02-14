"""
Embeddings and Vector Store Test
================================

Tests the complete embedding + storage + retrieval pipeline.

Requirements:
- GOOGLE_API_KEY environment variable set
- Qdrant running on localhost:6333

How to run:
    cd backend
    $env:GOOGLE_API_KEY = "your-key-here"  # PowerShell
    python -m tests.test_embeddings_vectorstore
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.embeddings import GoogleEmbedder, EmbeddingResult
from app.vectorstore import QdrantVectorStore, VectorRecord, SearchResponse


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_google_embedder():
    """Test Google embedding generation."""
    print_header("Testing Google Embedder")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("SKIPPED: GOOGLE_API_KEY not set")
        print("Get your key at: https://aistudio.google.com/app/apikey")
        print("Then set it: $env:GOOGLE_API_KEY = \"your-key-here\"")
        return False
    
    try:
        embedder = GoogleEmbedder(api_key=api_key)
        
        # Test single embedding
        print("\n--- Single Text Embedding ---")
        result = embedder.embed_text("The quick brown fox jumps over the lazy dog.")
        
        print(f"Model: {result.model}")
        print(f"Dimensions: {result.dimensions}")
        print(f"Vector (first 5): {result.embedding[:5]}")
        
        # Test batch embedding
        print("\n--- Batch Embedding ---")
        texts = [
            "Machine learning is a subset of artificial intelligence.",
            "Deep learning uses neural networks with many layers.",
            "The weather today is sunny and warm."
        ]
        
        results = embedder.embed_batch(texts)
        
        print(f"Embedded {len(results)} texts")
        for i, r in enumerate(results):
            print(f"  Text {i+1}: {r.dimensions} dimensions")
        
        # Test semantic similarity
        print("\n--- Semantic Similarity Test ---")
        
        text1 = "The cat sat on the mat"
        text2 = "A feline rested on a rug"
        text3 = "Stock prices rose sharply today"
        
        emb1 = embedder.embed_text(text1).embedding
        emb2 = embedder.embed_text(text2).embedding
        emb3 = embedder.embed_text(text3).embedding
        
        def cosine_similarity(a, b):
            dot = sum(x*y for x, y in zip(a, b))
            norm_a = sum(x*x for x in a) ** 0.5
            norm_b = sum(x*x for x in b) ** 0.5
            return dot / (norm_a * norm_b)
        
        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)
        
        print(f'Similarity "{text1}" vs "{text2}": {sim_1_2:.4f}')
        print(f'Similarity "{text1}" vs "{text3}": {sim_1_3:.4f}')
        
        if sim_1_2 > sim_1_3:
            print("✓ Semantic similarity working correctly (similar texts have higher score)")
        else:
            print("⚠ Unexpected: dissimilar text has higher score")
        
        print("\n✓ Google Embedder test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Google Embedder test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qdrant_connection():
    """Test connection to Qdrant."""
    print_header("Testing Qdrant Connection")
    
    try:
        store = QdrantVectorStore(host="localhost", port=6333)
        collections = store.client.get_collections()
        print(f"Connected to Qdrant successfully")
        print(f"Existing collections: {[c.name for c in collections.collections]}")
        
        print("\n✓ Qdrant Connection test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Qdrant Connection test FAILED: {e}")
        print("\nMake sure Qdrant is running:")
        print("  docker start qdrant")
        return False


def test_qdrant_operations():
    """Test Qdrant CRUD operations."""
    print_header("Testing Qdrant Operations")
    
    try:
        store = QdrantVectorStore(host="localhost", port=6333)
        collection_name = "test_collection"
        
        if store.collection_exists(collection_name):
            store.delete_collection(collection_name)
            print(f"Deleted existing collection: {collection_name}")
        
        print("\n--- Create Collection ---")
        store.create_collection(collection_name, vector_size=4)
        print(f"Created collection: {collection_name}")
        
        print("\n--- Insert Vectors ---")
        records = [
            VectorRecord(
                id="doc1_chunk1",
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={"content": "First document chunk", "document_id": "doc1", "page": 1}
            ),
            VectorRecord(
                id="doc1_chunk2",
                vector=[0.15, 0.25, 0.35, 0.45],
                payload={"content": "Second document chunk", "document_id": "doc1", "page": 2}
            ),
            VectorRecord(
                id="doc2_chunk1",
                vector=[0.9, 0.8, 0.7, 0.6],
                payload={"content": "Different document", "document_id": "doc2", "page": 1}
            ),
        ]
        
        store.insert(collection_name, records)
        print(f"Inserted {len(records)} vectors")
        
        info = store.get_collection_info(collection_name)
        print(f"Collection info: {info}")
        
        print("\n--- Search ---")
        query_vector = [0.12, 0.22, 0.32, 0.42]
        
        response = store.search(collection_name, query_vector, limit=3)
        
        print(f"Search returned {response.total_results} results in {response.search_time_ms:.2f}ms")
        for r in response.results:
            print(f"  ID: {r.id}, Score: {r.score:.4f}, Content: {r.payload.get('content')}")
        
        print("\n--- Search with Filter ---")
        response_filtered = store.search(
            collection_name,
            query_vector,
            limit=3,
            filters={"document_id": "doc1"}
        )
        
        print(f"Filtered search (doc1 only): {response_filtered.total_results} results")
        for r in response_filtered.results:
            print(f"  ID: {r.id}, Score: {r.score:.4f}")
        
        print("\n--- Delete ---")
        store.delete(collection_name, ["doc2_chunk1"])
        print("Deleted doc2_chunk1")
        
        store.delete_collection(collection_name)
        print(f"\nCleaned up: deleted {collection_name}")
        
        print("\n✓ Qdrant Operations test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Qdrant Operations test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test complete embedding + storage + retrieval pipeline."""
    print_header("Testing Full Pipeline")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("SKIPPED: GOOGLE_API_KEY not set")
        return False
    
    try:
        embedder = GoogleEmbedder(api_key=api_key)
        store = QdrantVectorStore(host="localhost", port=6333)
        collection_name = "test_full_pipeline"
        
        if store.collection_exists(collection_name):
            store.delete_collection(collection_name)
        
        # First, embed one text to get the actual dimensions
        sample_embedding = embedder.embed_text("sample text")
        actual_dimensions = sample_embedding.dimensions
        
        print(f"Detected embedding dimensions: {actual_dimensions}")
        
        # Now create collection with correct dimensions
        store.create_collection(collection_name, vector_size=actual_dimensions)
        print(f"Created collection with {actual_dimensions} dimensions")
        
        documents = [
            {"id": "1", "content": "Python is a programming language known for its simplicity.", "topic": "programming"},
            {"id": "2", "content": "Machine learning algorithms can learn from data.", "topic": "ml"},
            {"id": "3", "content": "The Eiffel Tower is located in Paris, France.", "topic": "travel"},
            {"id": "4", "content": "Neural networks are inspired by the human brain.", "topic": "ml"},
            {"id": "5", "content": "JavaScript is used for web development.", "topic": "programming"},
        ]
        
        print("\n--- Embedding and Storing Documents ---")
        records = []
        for doc in documents:
            embedding = embedder.embed_text(doc["content"])
            records.append(VectorRecord(
                id=doc["id"],
                vector=embedding.embedding,
                payload={"content": doc["content"], "topic": doc["topic"]}
            ))
            print(f"  Embedded doc {doc['id']}: {doc['content'][:40]}...")
        
        store.insert(collection_name, records)
        print(f"\nStored {len(records)} documents")
        
        print("\n--- Semantic Search ---")
        queries = [
            "What programming languages are easy to learn?",
            "How do AI systems learn?",
            "Famous landmarks in Europe"
        ]
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            
            query_embedding = embedder.embed_query(query).embedding
            
            response = store.search(collection_name, query_embedding, limit=2)
            
            print(f"Top results:")
            for r in response.results:
                print(f"  Score: {r.score:.4f} | {r.payload.get('content')[:50]}...")
        
        store.delete_collection(collection_name)
        print(f"\nCleaned up collection")
        
        print("\n✓ Full Pipeline test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Full Pipeline test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" DocuMind Embeddings & Vector Store Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Qdrant Connection", test_qdrant_connection()))
    
    if results[-1][1]:
        results.append(("Qdrant Operations", test_qdrant_operations()))
        results.append(("Google Embedder", test_google_embedder()))
        
        if results[-1][1]:
            results.append(("Full Pipeline", test_full_pipeline()))
    
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED/SKIPPED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed or were skipped.")


if __name__ == "__main__":
    main()