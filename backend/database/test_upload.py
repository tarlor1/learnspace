"""
Test script for PDF upload with GraphRAG
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal, init_db
from database.upload import DocumentUploadPipeline


def test_upload(pdf_path: str, user_id: str = "test_user_123"):
    """
    Test the upload pipeline with a PDF file

    Args:
        pdf_path: Path to your PDF file
        user_id: Auth0 user ID (use test ID for now)
    """
    print(f"\n🧪 Testing PDF Upload Pipeline")
    print(f"   PDF: {pdf_path}")
    print(f"   User: {user_id}\n")

    # Ensure database tables exist
    print("Checking database tables...")
    init_db()

    # Read PDF file
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    filename = Path(pdf_path).name

    # Create database session
    db = SessionLocal()

    try:
        # Create test user if doesn't exist
        from database.models.user import UserProfile

        existing_user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not existing_user:
            print(f"Creating test user: {user_id}")
            test_user = UserProfile(id=user_id)
            db.add(test_user)
            db.commit()
            print("✅ Test user created")
        else:
            print(f"✅ Using existing user: {user_id}")

        # Initialize pipeline (skip concept extraction to avoid Gemini quota)
        print("⚠️  Concept extraction disabled to avoid rate limits")
        print("   (Vector search will still work perfectly!)\n")
        pipeline = DocumentUploadPipeline(db, extract_concepts=False)

        # Process upload
        document = pipeline.process_upload(
            pdf_bytes=pdf_bytes,
            filename=filename,
            user_id=user_id,
            storage_url=f"file://{pdf_path}",  # Using local path for testing
        )

        print(f"\n✅ Upload successful!")
        print(f"   Document ID: {document.id}")
        print(f"   Status: {document.status}")
        print(f"   Owner: {document.owner_id}")

        # Test question generation
        print(f"\n🤖 Testing question generation...")
        question_data = pipeline.generate_question_from_document(
            document_id=str(document.id), topic="What are the key concepts?"
        )

        print(f"\n📝 Generated Question:")
        print(f"   Document ID: {question_data['document_id']}")
        print(f"   Context Chunks Used: {question_data['context_chunks']}")
        print(f"\n   Question Response:")
        print(f"   {question_data['question'][:500]}...")

        return document

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_upload.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_upload.py sample.pdf")
        print("  python test_upload.py C:\\Users\\Downloads\\textbook.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)

    test_upload(pdf_path)
