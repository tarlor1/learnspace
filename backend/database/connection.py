"""
Database connection configuration for Supabase + SQLAlchemy
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in .env.local")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from database.models import (
        UserProfile,
        Document,
        Chapter,
        Question,
        UserAnswer,
        DocumentPerformance,
        ChapterPerformance,
    )

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
