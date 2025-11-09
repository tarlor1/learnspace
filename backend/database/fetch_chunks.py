"""
Test script to fetch chunks from Neo4j for a specific document
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.upload import GraphRAGIndexer


def test_fetch_chunks(document_id: str, topic: str = "programming language concepts"):
    """
    Test fetching relevant chunks from Neo4j for a document

    Args:
        document_id: UUID of the document in both PostgreSQL and Neo4j
        topic: Topic/query to search for
    """
    print(f"\n🔍 Testing Chunk Retrieval")
    print(f"   Document ID: {document_id}")
    print(f"   Topic: {topic}\n")

    # Initialize indexer
    indexer = GraphRAGIndexer(extract_concepts=False)

    # Query for relevant chunks
    print(f"🤖 Querying Neo4j for relevant chunks...")
    relevant_chunks = indexer.query_document(
        document_id=document_id, query_text=topic, top_k=5
    )

    if not relevant_chunks:
        print(f"❌ No chunks found for document {document_id}")
        return

    print(f"\n✅ Found {len(relevant_chunks)} relevant chunks:\n")

    for i, chunk in enumerate(relevant_chunks, 1):
        print(f"{'='*80}")
        print(f"Chunk #{i}")
        print(f"Index: {chunk['chunk_index']}")
        print(f"Similarity Score: {chunk['score']:.4f}")
        print(f"\nContent Preview:")
        print(f"{chunk['text'][:300]}...")
        print(f"{'='*80}\n")

    # Return chunks for further use
    return relevant_chunks


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fetch_chunks.py <document_id> [topic]")
        print("\nExample:")
        print("  python fetch_chunks.py e479e5a2-5165-4769-920d-57376245d081")
        print(
            '  python fetch_chunks.py e479e5a2-5165-4769-920d-57376245d081 "parsing techniques"'
        )
        sys.exit(1)

    doc_id = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else "programming language concepts"

    test_fetch_chunks(doc_id, topic)
