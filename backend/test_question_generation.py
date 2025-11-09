"""
Test script to demonstrate the complete question generation pipeline:
1. Fetch relevant chunks from Neo4j
2. Generate a question using NeuralSeek
"""

import sys
import asyncio
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.upload import GraphRAGIndexer
from utils import generate_question_from_context


async def test_question_generation_pipeline(
    document_id: str, topic: str = "programming language concepts"
):
    """
    Test the complete pipeline: fetch chunks and generate a question.

    Args:
        document_id: UUID of the document in Neo4j
        topic: Topic/query to search for
    """
    print("\n" + "=" * 80)
    print("🧪 TESTING QUESTION GENERATION PIPELINE")
    print("=" * 80)
    print(f"📄 Document ID: {document_id}")
    print(f"📚 Topic: {topic}\n")

    # --- Step 1: Fetch Relevant Chunks ---
    print("🔍 STEP 1: Fetching relevant chunks from Neo4j...")
    print("-" * 80)

    indexer = GraphRAGIndexer(extract_concepts=False)
    relevant_chunks = indexer.query_document(
        document_id=document_id, query_text=topic, top_k=5
    )

    if not relevant_chunks:
        print(f"❌ No chunks found for document {document_id}")
        return

    print(f"✅ Found {len(relevant_chunks)} relevant chunks:\n")
    for i, chunk in enumerate(relevant_chunks, 1):
        print(
            f"  Chunk #{i} (Index: {chunk['chunk_index']}, Score: {chunk['score']:.4f})"
        )
        print(f"  Preview: {chunk['text'][:150]}...\n")

    # --- Step 2: Prepare Context for NeuralSeek ---
    print("\n📝 STEP 2: Preparing context for NeuralSeek...")
    print("-" * 80)

    context_text = "\n\n---\n\n".join([chunk["text"] for chunk in relevant_chunks])
    print(f"✅ Context prepared ({len(context_text)} characters)\n")

    # --- Step 3: Generate Question with NeuralSeek ---
    print("🤖 STEP 3: Generating question using NeuralSeek...")
    print("-" * 80)

    try:
        generated_question = await generate_question_from_context(context=context_text)

        if generated_question.get("error"):
            print(f"❌ Error from NeuralSeek: {generated_question.get('error')}")
            print(f"   Raw response: {generated_question.get('raw_response', 'N/A')}")
            return

        # --- Step 4: Display the Generated Question ---
        print("\n" + "=" * 80)
        print("✨ GENERATED QUESTION")
        print("=" * 80)
        print(json.dumps(generated_question, indent=2))
        print("=" * 80)

    except Exception as e:
        print(f"❌ An error occurred during question generation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_question_generation.py <document_id> [topic]")
        print("\nExample:")
        print(
            '  python test_question_generation.py e479e5a2-5165-4769-920d-57376245d081 "parsing techniques"'
        )
        sys.exit(1)

    doc_id = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else "programming language concepts"

    # Run the async test function
    asyncio.run(test_question_generation_pipeline(doc_id, topic))
