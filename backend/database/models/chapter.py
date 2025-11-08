"""
Chapter model - Chapters within documents
"""

from sqlalchemy import Column, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import uuid


class Chapter(Base):
    """
    Chapters within documents
    """

    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chapter_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="chapters")
    questions = relationship(
        "Question", back_populates="chapter", cascade="all, delete-orphan"
    )
    performances = relationship(
        "ChapterPerformance", back_populates="chapter", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Chapter(id={self.id}, chapter_number={self.chapter_number}, title={self.title})>"
