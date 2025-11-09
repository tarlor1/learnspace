from pydantic import BaseModel, Field
from typing import List, Dict, Any
from uuid import uuid4


class GenerateQuestionsRequest(BaseModel):
    """Request model for question generation"""
    topic: str = Field(..., min_length=1, description="Topic to generate questions for")
    num_questions: int = Field(default=1, ge=1, le=50, description="Number of questions to generate")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Python",
                "num_questions": 3
            }
        }


class Question(BaseModel):
    """Short response question model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    question: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "Introduction to Python",
                "question": "Explain what a Python virtual environment is and why it's useful.",
            }
        }


class GenerateQuestionsResponse(BaseModel):
    """Response model for question generation"""
    message: str
    num_questions: int
    questions: List[Question]


class SubmitAnswerRequest(BaseModel):
    """Request model for answer submission"""
    topic: str = Field(..., min_length=1, description="Topic of the question")
    question_id: str = Field(..., description="Unique ID of the question")
    answer: str = Field(..., min_length=1, description="User's short response answer")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Python",
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "answer": "It isolates dependencies per project."
            }
        }


class SubmitAnswerResponse(BaseModel):
    """Response model for answer submission"""
    message: str
    topic: str
    question_id: str
    answer: str
    validation: Dict[str, Any]
    timestamp: str

