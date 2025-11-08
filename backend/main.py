from fastapi import FastAPI, HTTPException, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
from datetime import datetime

from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse
)
from utils import generate_questions_with_neuralseek, validate_answer_with_neuralseek
from auth import get_current_user, get_optional_user

app = FastAPI(
    title="LearnSpace API",
    description="Backend API for PDF-based question generation with NeuralSeek integration",
    version="1.0.0",
)

# Enable CORS (for Next.js frontend during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "*",  # dev only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Each key = session_token, value = dict of user data & questions
data_store: Dict[str, Dict[str, Any]] = {}

# Each key = username, value = hashed password
user_store: Dict[str, str] = {}

# Each key = session_token, value = user info
active_sessions: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "LearnSpace API is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": [
            "POST /generate-questions - Generate questions from PDF text",
            "POST /submit-answer - Submit an answer to a question"
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
        
        question_text = ""
        for question in data_store[session_token]["questions"]:
            if question["id"] == request.question_id:
                question_text = question["text"]
                break

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
# Docs: http://localhost:8000/docs
# ------------------------------------------------------------
