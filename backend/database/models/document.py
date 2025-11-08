"""
Document model - Uploaded PDFs
"""

from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import uuid


class Document(Base):
    """
    Uploaded documents
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        Text, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(Text, nullable=False)
    storage_url = Column(Text, nullable=False)
    status = Column(
        Text, nullable=False, default="pending"
    )  # pending, processing, ready, error
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    owner = relationship("UserProfile", back_populates="documents")
    chapters = relationship(
        "Chapter", back_populates="document", cascade="all, delete-orphan"
    )
    questions = relationship(
        "Question", back_populates="document", cascade="all, delete-orphan"
    )
    performances = relationship(
        "DocumentPerformance", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, name={self.name})>"
