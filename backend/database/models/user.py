"""
UserProfile model - Links to Auth0 users
"""

from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class UserProfile(Base):
    """
    User profile linked to Auth0 users
    """

    __tablename__ = "user_profiles"

    id = Column(Text, primary_key=True)  # Auth0 sub (e.g., "auth0|123456")
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    documents = relationship(
        "Document", back_populates="owner", cascade="all, delete-orphan"
    )
    answers = relationship(
        "UserAnswer", back_populates="user", cascade="all, delete-orphan"
    )
    doc_performances = relationship(
        "DocumentPerformance", back_populates="user", cascade="all, delete-orphan"
    )
    chapter_performances = relationship(
        "ChapterPerformance", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserProfile(id={self.id})>"
