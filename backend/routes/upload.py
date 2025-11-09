"""
API endpoints for document upload and management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Any, Optional

from database.connection import get_db
from database.upload import DocumentUploadPipeline
from database.models.document import Document
from auth import get_current_user

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF document and process it through the GraphRAG pipeline.

    Workflow:
    1. Validate PDF file
    2. Create Document record in PostgreSQL
    3. Extract and chunk text from PDF
    4. Index chunks in Neo4j with embeddings
    5. Return document metadata

    Note: Chapters are created symbolically based on content sections,
    not from explicit chapter markers in the PDF.
    """
    try:
        user_id = current_user.get("sub")

        # Validate filename exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        logger.info(f"Upload request from user '{user_id}' for file '{file.filename}'")

        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Read PDF bytes
        pdf_bytes = await file.read()

        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        logger.info(f"Read {len(pdf_bytes)} bytes from PDF")

        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid user authentication")

        # Process upload through pipeline
        # Note: We're using a placeholder storage_url since we're not actually storing files yet
        # In production, you'd upload to S3/Supabase Storage first
        storage_url = f"local://{file.filename}"

        pipeline = DocumentUploadPipeline(db_session=db, extract_concepts=False)
        document = pipeline.process_upload(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
            user_id=user_id,
            storage_url=storage_url,
        )

        logger.info(f"✅ Document uploaded successfully: {document.id}")

        # Fetch created chapters
        from database.models.chapter import Chapter

        chapters = (
            db.query(Chapter)
            .filter(Chapter.doc_id == document.id)
            .order_by(Chapter.chapter_number)
            .all()
        )

        return {
            "id": str(document.id),
            "name": document.name,
            "status": document.status,
            "created_at": document.created_at.isoformat(),
            "message": "Document uploaded and indexed successfully",
            "chapters": [
                {
                    "id": str(ch.id),
                    "chapter_number": ch.chapter_number,
                    "title": ch.title,
                    "summary": ch.summary,
                }
                for ch in chapters
            ],
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {str(e)}"
        )


@router.get("/")
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all documents for the current user
    """
    logger.info("📥 list_documents: START")
    try:
        user_id = current_user.get("sub")
        logger.info(f"📥 list_documents: user_id = {user_id}")

        # Simple query - just get documents, no joins
        logger.info("📥 list_documents: Fetching documents (no joins)...")
        documents = (
            db.query(Document)
            .filter(Document.owner_id == user_id)
            .order_by(Document.created_at.desc())
            .all()
        )
        logger.info(f"📥 list_documents: Found {len(documents)} documents")

        result_docs = []
        for doc in documents:
            result_docs.append(
                {
                    "id": str(doc.id),
                    "name": doc.name,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat(),
                    "storage_url": doc.storage_url,
                    "chapter_count": 0,  # Set to 0 for now - can fetch separately if needed
                    "chapters": [],
                }
            )

        logger.info(
            f"📥 list_documents: SUCCESS - returning {len(result_docs)} documents"
        )
        return {"documents": result_docs}

    except Exception as e:
        logger.error(f"❌ list_documents: FAILED - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details for a specific document
    """
    try:
        user_id = current_user.get("sub")

        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.owner_id == user_id)
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=404, detail="Document not found or access denied"
            )

        return {
            "id": str(document.id),
            "name": document.name,
            "status": document.status,
            "created_at": document.created_at.isoformat(),
            "storage_url": document.storage_url,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to get document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a document and its associated chunks from Neo4j
    """
    try:
        user_id = current_user.get("sub")

        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.owner_id == user_id)
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=404, detail="Document not found or access denied"
            )

        # TODO: Also delete from Neo4j
        # For now, just delete from PostgreSQL
        db.delete(document)
        db.commit()

        logger.info(f"✅ Document deleted: {document_id}")

        return {"message": "Document deleted successfully", "id": document_id}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/cleanup-stuck")
async def cleanup_stuck_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clean up documents that have been stuck in 'processing' state for too long (>10 minutes)
    This handles cases where upload was cancelled or failed without proper error handling
    """
    try:
        from datetime import datetime, timedelta

        user_id = current_user.get("sub")

        # Find documents stuck in processing for more than 10 minutes
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)

        stuck_docs = (
            db.query(Document)
            .filter(
                Document.owner_id == user_id,
                Document.status == "processing",
                Document.created_at < ten_minutes_ago,
            )
            .all()
        )

        if not stuck_docs:
            return {"message": "No stuck documents found", "count": 0}

        # Mark them as error
        stuck_doc_ids = [doc.id for doc in stuck_docs]
        stuck_doc_names = [{"id": str(doc.id), "name": doc.name} for doc in stuck_docs]

        db.query(Document).filter(Document.id.in_(stuck_doc_ids)).update(
            {"status": "error"}, synchronize_session=False
        )
        db.commit()

        for doc_info in stuck_doc_names:
            logger.info(
                f"⚠️  Marked stuck document as error: {doc_info['id']} ({doc_info['name']})"
            )

        return {
            "message": f"Cleaned up {len(stuck_docs)} stuck documents",
            "count": len(stuck_docs),
            "documents": stuck_doc_names,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup stuck documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cleanup stuck documents")
