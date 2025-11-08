"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from uuid import uuid4


class GenerateQuestionsRequest(BaseModel):
    """Request model for question generation"""
    pdf_text: Optional[str] = Field(default="", description="Extracted text from PDF (optional)")
    num_questions: int = Field(default=1, ge=1, le=50, description="Number of questions to generate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pdf_text": "This is sample text from a PDF about Python programming...",
                "num_questions": 1
            }
        }


class Question(BaseModel):
    """Base question model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["short", "mcq", "index"]
    chapter: str
    question: str
    options: Optional[List[str]] = None  # Only for MCQ type
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "mcq",
                "chapter": "Introduction to Python",
                "question": "What is Python primarily used for?",
                "options": ["Web Development", "Game Development", "Data Science", "All of the above"]
            }
        }


class GenerateQuestionsResponse(BaseModel):
    """Response model for question generation"""
    message: str
    num_questions: int
    questions: List[Question]
    session_id: str


class SubmitAnswerRequest(BaseModel):
    """Request model for answer submission"""
    question_id: str = Field(..., description="Unique ID of the question")
    answer: str = Field(..., min_length=1, description="User's answer or selected option")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "answer": "All of the above"
            }
        }


class SubmitAnswerResponse(BaseModel):
    """Response model for answer submission"""
    message: str
    question_id: str
    answer: str
    timestamp: str


class QuestionsListResponse(BaseModel):
    """Response model for getting all questions"""
    message: str
    total_questions: int
    questions: List[Question]
