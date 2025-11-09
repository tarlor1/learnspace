"""
API endpoints for question generation
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any, List

# Add parent directory to path to allow imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db
from database.upload import GraphRAGIndexer
from database.models.question import Question
from auth import get_current_user
from utils import generate_question_from_context, generate_questions_from_user_documents
from database.models.document import Document

router = APIRouter(
    prefix="",
    tags=["Questions"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/generate-question", response_model=Dict[str, Any])
async def generate_question(
    document_id: str = Body(..., embed=True),
    topic: str = Body(None, embed=True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a new question for a user based on their progress in a document.

    Workflow:
    1.  Determines the current chapter/topic for the user.
    2.  Uses GraphRAG to find the most relevant text chunks for that topic.
    3.  Passes the chunks to the NeuralSeek 'question_maker' agent.
    4.  Returns the structured JSON question from NeuralSeek.
    """
    try:
        user_id = current_user.get("sub")
        logger.info(
            f"Generating question for user '{user_id}' and document '{document_id}'"
        )

        # --- 1. Determine Current Chapter/Topic ---
        # If no topic is provided, we'll use a default.
        # TODO: Implement logic to fetch user's actual progress to determine the topic.
        current_topic = topic or "Introduction to Programming Language Pragmatics"
        logger.info(f"Determined current topic for user: '{current_topic}'")

        # --- 2. Fetch Relevant Chunks with GraphRAG ---
        indexer = GraphRAGIndexer(extract_concepts=False)
        logger.info("Querying for relevant text chunks using GraphRAGIndexer...")
        relevant_chunks = indexer.query_document(
            document_id=document_id,
            query_text=current_topic,
            top_k=5,  # Using top 5 chunks for better context
        )

        if not relevant_chunks:
            logger.warning(
                f"No relevant chunks found for document '{document_id}' on topic '{current_topic}'"
            )
            raise HTTPException(
                status_code=404,
                detail="Could not find relevant content to generate a question. Please try another topic or document.",
            )

        logger.info(f"Found {len(relevant_chunks)} relevant chunks.")

        # Extract chapter_id from the first chunk (all should have the same chapter)
        chapter_id = relevant_chunks[0].get("chapter_id") if relevant_chunks else None

        context_text = "\n\n---\n\n".join([chunk["text"] for chunk in relevant_chunks])

        # --- 3. Call Real Question Generation Service ---
        logger.info("Calling 'generate_question_from_context' utility...")
        generated_question = await generate_question_from_context(context=context_text)

        if generated_question.get("error"):
            logger.error(
                f"Failed to generate question from NeuralSeek: {generated_question}"
            )
            raise HTTPException(
                status_code=502,
                detail=generated_question.get(
                    "error", "Unknown error from question generation service."
                ),
            )

        # --- 4. Save Question to Database ---
        logger.info("Saving question to database...")

        # Map NeuralSeek response to our Question model structure
        question_content = generated_question.get("content", {})
        topic = generated_question.get("topic", current_topic)
        correct_answer = generated_question.get("correct_answer", "")

        new_question = Question(
            doc_id=document_id,
            chapter_id=chapter_id,
            content=question_content,  # This is the JSONB field
            correct_answer=correct_answer,
            topic=topic,
        )

        db.add(new_question)
        db.commit()
        db.refresh(new_question)

        logger.info(f"✅ Question saved with ID: {new_question.id}")

        # --- 5. Return the question ---
        logger.info("Successfully generated and saved question.")
        return {
            "id": str(new_question.id),
            "document_id": document_id,
            "chapter_id": str(chapter_id) if chapter_id else None,
            "topic": topic,
            "content": question_content,
            "correct_answer": correct_answer,
            "created_at": new_question.created_at.isoformat(),
        }

    except HTTPException as http_exc:
        # Re-raise HTTPException to be handled by FastAPI
        raise http_exc
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while generating a question: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )


@router.post("/generate-random-questions", response_model=List[Dict[str, Any]])
async def generate_random_questions(
    num_questions: int = Body(10, embed=True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates questions from random chunks across all user's documents.

    This is the new approach that:
    1. Fetches all user's documents from the database
    2. Gets random chunks from Neo4j for those documents
    3. Generates questions using NeuralSeek question_maker agent

    Args:
        num_questions: Number of questions to generate (default: 10)

    Returns:
        List of generated questions with document/chapter metadata
    """
    try:
        user_id = current_user.get("sub")
        logger.info(
            f"🎯 Generating {num_questions} random questions for user '{user_id}'"
        )

        # Fetch user's documents from database
        user_documents = (
            db.query(Document)
            .filter(Document.owner_id == user_id, Document.status == "ready")
            .all()
        )

        if not user_documents:
            logger.warning(f"No documents found for user '{user_id}'")
            raise HTTPException(
                status_code=404,
                detail="No documents found. Please upload a document first.",
            )

        document_ids = [str(doc.id) for doc in user_documents]
        logger.info(f"   📚 Found {len(document_ids)} documents for user")

        # Generate questions from random chunks
        questions = await generate_questions_from_user_documents(
            document_ids=document_ids, num_questions=num_questions
        )

        if not questions:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate questions from your documents.",
            )

        # Save questions to database
        saved_questions = []
        for q_data in questions:
            if q_data.get("error"):
                logger.warning(f"   ⚠️  Skipping failed question: {q_data.get('error')}")
                continue

            try:
                question_content = q_data.get(
                    "content", q_data
                )  # Handle different formats
                new_question = Question(
                    doc_id=q_data.get("document_id"),
                    chapter_id=q_data.get("chapter_id"),
                    content=question_content,
                    correct_answer=q_data.get("correct_answer", ""),
                    topic=q_data.get("topic", "General"),
                )

                db.add(new_question)
                db.flush()  # Get the ID without committing

                chapter_id_str = (
                    str(new_question.chapter_id)
                    if new_question.chapter_id is not None
                    else None
                )

                saved_questions.append(
                    {
                        "id": str(new_question.id),
                        "document_id": str(new_question.doc_id),
                        "chapter_id": chapter_id_str,
                        "content": question_content,
                        "correct_answer": new_question.correct_answer,
                        "topic": new_question.topic,
                        "source_chunks": q_data.get("source_chunks", []),
                    }
                )
            except Exception as e:
                logger.error(f"   ❌ Failed to save question: {e}")
                continue

        db.commit()

        logger.info(
            f"✅ Successfully generated and saved {len(saved_questions)} questions"
        )
        return saved_questions

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"❌ Failed to generate random questions: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating questions: {str(e)}",
        )
