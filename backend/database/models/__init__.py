"""
Database models for LearnSpace
All models are organized in separate files for better maintainability
"""

from database.models.user import UserProfile
from database.models.document import Document
from database.models.chapter import Chapter
from database.models.question import Question
from database.models.user_answer import UserAnswer
from database.models.performance import DocumentPerformance, ChapterPerformance

# Export all models
__all__ = [
    "UserProfile",
    "Document",
    "Chapter",
    "Question",
    "UserAnswer",
    "DocumentPerformance",
    "ChapterPerformance",
]
