"""
UserAnswer model - User's specific answers to questions
"""

from sqlalchemy import (
    Column,
    Text,
    Integer,
    Numeric,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import uuid


class UserAnswer(Base):
    """
    User's specific answers to questions
    Includes answer correctness, quality score, and question rating
    """

    __tablename__ = "user_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_answer = Column(Text, nullable=False)
    was_correct = Column(Boolean, nullable=False)
    answer_score = Column(
        Numeric(5, 2)
    )  # 0.00 to 100.00 - quality score for the answer
    question_rating = Column(
        Integer
    )  # 1-5 stars - user's rating of the question quality
    answered_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Check constraints
    __table_args__ = (
        CheckConstraint(
            "answer_score >= 0 AND answer_score <= 100", name="check_answer_score_range"
        ),
        CheckConstraint(
            "question_rating >= 1 AND question_rating <= 5",
            name="check_question_rating_range",
        ),
    )

    # Relationships
    user = relationship("UserProfile", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")

    def __repr__(self):
        return f"<UserAnswer(id={self.id}, was_correct={self.was_correct}, score={self.answer_score})>"
