import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from auth import router as auth_router, get_current_user
from routes.questions import router as questions_router
from routes.upload import router as upload_router
from utils import generate_questions_with_neuralseek, validate_answer_with_neuralseek

# In-memory store for user questions
user_question_store = {}

app = FastAPI(
    title="LearnSpace API",
    description="Backend API for PDF-based question generation and learning.",
    version="1.0.0",
)

# CORS configuration
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "LearnSpace API is running",
        "version": "1.0.0",
        "status": "healthy",
        "auth": "Auth0",
    }


# Include routers
app.include_router(auth_router)
app.include_router(questions_router)
app.include_router(upload_router)


@app.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest, current_user: dict = Depends(get_current_user)
):
    """Generate questions using NeuralSeek (requires Auth0 authentication)
    
    If no topic is provided, questions will be generated with random topics from a predefined list.
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

    if user_id not in user_question_store:
        user_question_store[user_id] = {"questions": {}}

    try:
        questions = await generate_questions_with_neuralseek(
            topic=request.topic,  # Can be None for random topics
            num_questions=request.num_questions,
        )
        for q in questions:
            user_question_store[user_id]["questions"][q.id] = q.dict()

        return GenerateQuestionsResponse(
            message="Questions generated successfully",
            num_questions=len(questions),
            questions=questions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating questions: {str(e)}"
        )


@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest, current_user: dict = Depends(get_current_user)
):
    """Submit an answer and validate it (requires Auth0 authentication)"""
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

    try:
        question_obj = (
            user_question_store.get(user_id, {})
            .get("questions", {})
            .get(request.question_id)
        )
        if not question_obj:
            raise HTTPException(
                status_code=404, detail="Question not found for this user"
            )

        question_text = question_obj.get("question", "")

        validation = await validate_answer_with_neuralseek(
            topic=request.topic, question_text=question_text, user_answer=request.answer
        )

        return SubmitAnswerResponse(
            message="Answer submitted successfully",
            topic=request.topic,
            question_id=request.question_id,
            answer=request.answer,
            validation=validation or {},
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error submitting answer: {str(e)}"
        )
