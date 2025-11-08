"""
FastAPI backend for LearnSpace - PDF-based question generation app
Integrates with NeuralSeek API for AI-powered question generation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    QuestionsListResponse,
    Question,
)
from utils import generate_questions_with_neuralseek
from auth import get_current_user, get_optional_user


# Initialize FastAPI app
app = FastAPI(
    title="LearnSpace API",
    description="Backend API for PDF-based question generation with NeuralSeek integration",
    version="1.0.0",
)

# Configure CORS to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default port
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        # Add your production frontend URL here when deploying
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# In-memory data store
# In production, replace with a proper database (PostgreSQL, MongoDB, etc.)
data_store: Dict[str, Any] = {
    "sessions": {},  # session_id -> {pdf_text, questions, answers}
    "questions": [],  # Global list of all questions
    "answers": [],  # Global list of all submitted answers
}


@app.get("/")
async def root():
    """
    Root endpoint - API health check

    Returns:
        Basic API information and available endpoints
    """
    return {
        "message": "LearnSpace API is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": [
            "POST /generate-questions - Generate questions from PDF text",
            "POST /submit-answer - Submit an answer to a question",
            "GET /questions - Get all generated questions",
            "GET /session/{session_id} - Get session data",
            "DELETE /reset - Reset all data (dev only)",
        ],
    }


@app.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest, current_user: dict = Depends(get_current_user)
):
    """
    Question generation endpoint

    Forwards request to NeuralSeek API to generate three types of questions:
    - Short response questions (open-ended)
    - Multiple choice questions (MCQ) with 4 options
    - Index cards (informational only)

    Args:
        request: GenerateQuestionsRequest with pdf_text and num_questions

    Returns:
        GenerateQuestionsResponse with array of generated questions and session_id

    Raises:
        HTTPException: If PDF text is too short or API call fails
    """
    try:
        # Validate request
        if not request.pdf_text or len(request.pdf_text) < 50:
            raise HTTPException(
                status_code=400,
                detail="PDF text is too short. Please provide at least 50 characters of content.",
            )

        # Generate questions using NeuralSeek API
        questions = await generate_questions_with_neuralseek(
            request.pdf_text, request.num_questions
        )

        # Create session for these questions
        session_id = str(uuid4())
        data_store["sessions"][session_id] = {
            "pdf_text": request.pdf_text,
            "questions": questions,
            "answers": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Also add to global questions list
        data_store["questions"].extend(questions)

        return GenerateQuestionsResponse(
            message="Questions generated successfully using NeuralSeek AI",
            num_questions=len(questions),
            questions=questions,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating questions: {str(e)}"
        )


@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest, current_user: dict = Depends(get_current_user)
):
    """
    Answer submission endpoint

    Accepts and stores user's answer to a question.
    Validates that the question exists before storing.

    Args:
        request: SubmitAnswerRequest with question_id and answer

    Returns:
        SubmitAnswerResponse confirming the submission with timestamp

    Raises:
        HTTPException: If question_id is not found
    """
    try:
        # Verify question exists
        question_exists = False
        question_type = None

        # Check in sessions
        for session_data in data_store["sessions"].values():
            for q in session_data["questions"]:
                if q.id == request.question_id:
                    question_exists = True
                    question_type = q.type
                    # Add answer to session
                    session_data["answers"].append(
                        {
                            "question_id": request.question_id,
                            "answer": request.answer,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    break
            if question_exists:
                break

        if not question_exists:
            # Check global questions list
            for q in data_store["questions"]:
                if q.id == request.question_id:
                    question_exists = True
                    question_type = q.type
                    break

        if not question_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Question with ID '{request.question_id}' not found",
            )

        # Store answer globally
        answer_data = {
            "question_id": request.question_id,
            "answer": request.answer,
            "question_type": question_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        data_store["answers"].append(answer_data)

        return SubmitAnswerResponse(
            message="Answer submitted successfully",
            question_id=request.question_id,
            answer=request.answer,
            timestamp=answer_data["timestamp"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error submitting answer: {str(e)}"
        )


@app.get("/questions", response_model=QuestionsListResponse)
async def get_questions(current_user: dict = Depends(get_current_user)):
    """
    Get all questions endpoint

    Returns all questions generated across all sessions.
    Useful for displaying question history or review.

    Returns:
        QuestionsListResponse with list of all questions
    """
    try:
        all_questions = data_store["questions"]

        return QuestionsListResponse(
            message="Questions retrieved successfully",
            total_questions=len(all_questions),
            questions=all_questions,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving questions: {str(e)}"
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get session data endpoint

    Returns all data for a specific session including:
    - Generated questions
    - Submitted answers
    - Session metadata

    Args:
        session_id: UUID of the session

    Returns:
        Session data dictionary with questions and answers

    Raises:
        HTTPException: If session_id is not found
    """
    if session_id not in data_store["sessions"]:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    session_data = data_store["sessions"][session_id]

    return {
        "session_id": session_id,
        "num_questions": len(session_data["questions"]),
        "num_answers": len(session_data["answers"]),
        "questions": session_data["questions"],
        "answers": session_data["answers"],
        "created_at": session_data.get("generated_at"),
        "text_preview": (
            session_data["pdf_text"][:200] + "..."
            if len(session_data["pdf_text"]) > 200
            else session_data["pdf_text"]
        ),
    }


@app.get("/stats")
async def get_stats(current_user: dict = Depends(get_optional_user)):
    """
    Get statistics endpoint (bonus feature)

    Returns overall statistics about the application usage:
    - Total sessions
    - Total questions generated
    - Total answers submitted
    - Breakdown by question type

    Returns:
        Statistics dictionary
    """
    total_short = sum(1 for q in data_store["questions"] if q.type == "short")
    total_mcq = sum(1 for q in data_store["questions"] if q.type == "mcq")
    total_index = sum(1 for q in data_store["questions"] if q.type == "index")

    return {
        "total_sessions": len(data_store["sessions"]),
        "total_questions": len(data_store["questions"]),
        "total_answers": len(data_store["answers"]),
        "questions_by_type": {
            "short_response": total_short,
            "multiple_choice": total_mcq,
            "index_cards": total_index,
        },
        "answer_rate": (
            f"{(len(data_store['answers']) / len(data_store['questions']) * 100):.1f}%"
            if data_store["questions"]
            else "0%"
        ),
    }


@app.delete("/reset")
async def reset_data():
    """
    Reset all data endpoint (development/testing only)

    Clears all sessions, questions, and answers from memory.
    WARNING: This deletes all data - use only for testing!

    Returns:
        Confirmation message with reset counts
    """
    sessions_count = len(data_store["sessions"])
    questions_count = len(data_store["questions"])
    answers_count = len(data_store["answers"])

    data_store["sessions"].clear()
    data_store["questions"].clear()
    data_store["answers"].clear()

    return {
        "message": "All data has been reset successfully",
        "deleted": {
            "sessions": sessions_count,
            "questions": questions_count,
            "answers": answers_count,
        },
    }


# Run with: uvicorn main:app --reload
# API docs available at: http://localhost:8000/docs
# Alternative docs: http://localhost:8000/redoc
