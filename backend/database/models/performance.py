"""
Performance tracking models
- DocumentPerformance: Track user performance on documents
- ChapterPerformance: Track user performance on chapters
"""

from sqlalchemy import Column, Text, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class DocumentPerformance(Base):
    """
    User's performance on a specific document
    """

    __tablename__ = "document_performance"

    user_id = Column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    overall_score = Column(Numeric(5, 2), nullable=False, default=0.0)  # 0.00 to 100.00
    last_reviewed = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("UserProfile", back_populates="doc_performances")
    document = relationship("Document", back_populates="performances")

    def __repr__(self):
        return f"<DocumentPerformance(user_id={self.user_id}, doc_id={self.doc_id}, score={self.overall_score})>"


class ChapterPerformance(Base):
    """
    User's performance on a specific chapter
    """

    __tablename__ = "chapter_performance"

    user_id = Column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    chapter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score = Column(Numeric(5, 2), nullable=False, default=0.0)  # 0.00 to 100.00
    last_reviewed = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("UserProfile", back_populates="chapter_performances")
    chapter = relationship("Chapter", back_populates="performances")

    def __repr__(self):
        return f"<ChapterPerformance(user_id={self.user_id}, chapter_id={self.chapter_id}, score={self.score})>"
