from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    QuestionsListResponse
)
from utils import generate_questions_with_neuralseek


# Initialize FastAPI app
app = FastAPI(
    title="LearnSpace API",
    description="Backend API for PDF-based question generation with NeuralSeek integration",
    version="1.0.0"
)

# Configure CORS to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default port
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "*",  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# In-memory data store
data_store: Dict[str, Any] = {
    "sessions": {},
    "questions": []
}


@app.get("/")
async def root():
    return {
        "message": "LearnSpace API is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": [
            "POST /generate-questions - Generate questions from PDF text",
            "POST /submit-answer - Submit an answer to a question"
        ]
    }


@app.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """Generate questions from PDF text using NeuralSeek"""
    try:
        print(f"\n📥 Received request to generate {request.num_questions} questions")
        
        # Generate questions using NeuralSeek API
        questions = await generate_questions_with_neuralseek(
            pdf_text=request.pdf_text or "",
            num_questions=request.num_questions
        )
        
        print(f"✅ Generated {len(questions)} questions")
        
        # Create session
        session_id = str(uuid4())
        data_store["sessions"][session_id] = {
            "pdf_text": request.pdf_text or "",
            "questions": questions,
            "answers": [],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Add to global questions list
        data_store["questions"].extend(questions)
        
        return GenerateQuestionsResponse(
            message="Questions generated successfully using NeuralSeek AI",
            num_questions=len(questions),
            questions=questions,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )


@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """Submit an answer to a question"""
    try:
        print(f"\n📥 Received answer for question: {request.question_id}")
        
        # Verify question exists
        question_exists = any(
            q.id == request.question_id 
            for q in data_store["questions"]
        )
        
        if not question_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Question with ID '{request.question_id}' not found"
            )
        
        # Store answer
        answer_data = {
            "question_id": request.question_id,
            "answer": request.answer,
            "timestamp": datetime.utcnow().isoformat()
        }
        data_store["answers"].append(answer_data)
        
        print(f"✅ Answer stored successfully")
        
        return SubmitAnswerResponse(
            message="Answer submitted successfully",
            question_id=request.question_id,
            answer=request.answer,
            timestamp=answer_data["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting answer: {str(e)}"
        )

# Run with: uvicorn main:app --reload
# API docs available at: http://localhost:8000/docs
# Alternative docs: http://localhost:8000/redoc