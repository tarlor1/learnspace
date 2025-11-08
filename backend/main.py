from fastapi import FastAPI, HTTPException, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
from datetime import datetime
from datetime import datetime
import hashlib
import secrets

from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    QuestionsListResponse
)
from utils import generate_questions_with_neuralseek, validate_answer_with_neuralseek
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
    request: GenerateQuestionsRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    session_token: Optional[str] = Cookie(None, alias="session_token")
):
    """Generate questions using NeuralSeek"""
    if not current_user or not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    print(f"\n📥 Generating {request.num_questions} questions for {current_user['username']}")

    try:
        questions = await generate_questions_with_neuralseek(
            num_questions=request.num_questions
        )

        data_store[session_token]["questions"].extend(questions)

        print(f"✅ Generated {len(questions)} questions")

        return GenerateQuestionsResponse(
            message="Questions generated successfully",
            num_questions=len(questions),
            questions=questions
        )

    except Exception as e:
        print(f"❌ Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    session_token: Optional[str] = Cookie(None, alias="session_token")
):
    """Submit an answer and validate it"""
    if not current_user or not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    print(f"\n📥 Answer submission from {current_user['username']} for question: {request.question_id}")

    try:
        # Make sure the question exists for this session
        questions = data_store.get(session_token, {}).get("questions", [])
        if request.question_id >= len(questions) or request.question_id < 0:
            raise HTTPException(status_code=404, detail="Question not found for this session")

        question_text = questions[request.question_id]

        validation = await validate_answer_with_neuralseek(
            question_text=question_text,
            user_answer=request.answer
        )

        return SubmitAnswerResponse(
            message="Answer submitted successfully",
            question_id=request.question_id,
            validation=validation,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        print(f"❌ Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")

# Run with: uvicorn main:app --reload
# API docs available at: http://localhost:8000/docs
# Alternative docs: http://localhost:8000/redoc
