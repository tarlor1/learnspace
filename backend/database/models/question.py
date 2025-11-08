"""
Question model - Question templates (not user-specific)
"""

from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import uuid


class Question(Base):
    """
    Question templates (not user-specific)
    Stores the question content, correct answer, and topic
    """

    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chapter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=False,
    )
    content = Column(
        JSONB, nullable=False
    )  # {"text": "...", "options": [...], "type": "mcq"}
    correct_answer = Column(Text)
    topic = Column(Text)  # e.g., "Mitochondria"
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="questions")
    chapter = relationship("Chapter", back_populates="questions")
    user_answers = relationship(
        "UserAnswer", back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Question(id={self.id}, topic={self.topic})>"
