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
from utils import validate_answer_with_neuralseek

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
    """Generate questions using NeuralSeek from user's documents (requires Auth0 authentication)
    
    This endpoint now generates questions from the user's uploaded documents using
    the topic_generator agent to identify topics and question_maker agent to generate questions.
    """
    from database.connection import get_db
    from database.models.document import Document
    from utils import generate_questions_from_user_documents
    
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

    if user_id not in user_question_store:
        user_question_store[user_id] = {"questions": {}}

    try:
        # Get database session
        db = next(get_db())
        
        try:
            # Fetch user's documents
            user_documents = (
                db.query(Document)
                .filter(Document.owner_id == user_id, Document.status == "ready")
                .all()
            )
            
            if not user_documents:
                raise HTTPException(
                    status_code=404,
                    detail="No documents found. Please upload a document first."
                )
            
            document_ids = [str(doc.id) for doc in user_documents]
            
            # Generate questions from user's documents
            questions_data = await generate_questions_from_user_documents(
                document_ids=document_ids,
                num_questions=request.num_questions,
            )
            
            if not questions_data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate questions from your documents."
                )
            
            # Convert to Question model format for response
            from models import Question as QuestionModel
            from uuid import uuid4
            
            questions = []
            for q_data in questions_data:
                if q_data.get("error"):
                    continue
                
                q_id = str(uuid4())
                topic = q_data.get("topic", "General")
                content = q_data.get("content", q_data)
                
                # Extract question text from content
                if isinstance(content, dict):
                    question_text = content.get("question", content.get("text", str(content)))
                else:
                    question_text = str(content)
                
                question = QuestionModel(
                    id=q_id,
                    topic=topic,
                    question=question_text
                )
                
                questions.append(question)
                user_question_store[user_id]["questions"][q_id] = {
                    "id": q_id,
                    "topic": topic,
                    "question": question_text,
                    "document_id": q_data.get("document_id"),
                    "chapter_id": q_data.get("chapter_id"),
                }
            
            return GenerateQuestionsResponse(
                message="Questions generated successfully from your documents",
                num_questions=len(questions),
                questions=questions,
            )
        finally:
            db.close()
            
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
