# Database Models Documentation

This directory contains all SQLAlchemy models for the LearnSpace application.

## Structure

```
database/
├── connection.py           # Database connection and session management
└── models/
    ├── __init__.py         # Exports all models
    ├── user.py             # UserProfile model
    ├── document.py         # Document model
    ├── chapter.py          # Chapter model
    ├── question.py         # Question model (templates)
    ├── user_answer.py      # UserAnswer model (instances)
    └── performance.py      # Performance tracking models
```

## Models Overview

### UserProfile (`user.py`)
Links to Auth0 users. Only stores the Auth0 `sub` as the primary key.
- **Primary Key**: `id` (TEXT) - Auth0 sub (e.g., "auth0|123456")
- **Fields**: `created_at`
- **Relationships**: documents, answers, performances

### Document (`document.py`)
Represents uploaded PDF documents.
- **Primary Key**: `id` (UUID)
- **Foreign Keys**: `owner_id` → UserProfile
- **Fields**: `name`, `storage_url`, `status`, `created_at`
- **Status values**: 'pending', 'processing', 'ready', 'error'

### Chapter (`chapter.py`)
Chapters within documents.
- **Primary Key**: `id` (UUID)
- **Foreign Keys**: `doc_id` → Document
- **Fields**: `chapter_number`, `title`, `summary`, `created_at`

### Question (`question.py`)
Question templates (not user-specific).
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `doc_id` → Document (CASCADE)
  - `chapter_id` → Chapter (SET NULL, nullable)
- **Fields**:
  - `content` (JSONB) - Flexible storage: `{"text": "...", "options": [...], "type": "mcq"}`
  - `correct_answer` (TEXT)
  - `topic` (TEXT) - e.g., "Mitochondria"
  - `created_at`

### UserAnswer (`user_answer.py`)
User's specific answers to questions (join table).
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `user_id` → UserProfile (CASCADE)
  - `question_id` → Question (CASCADE)
- **Fields**:
  - `user_answer` (TEXT) - What the user submitted
  - `was_correct` (BOOLEAN) - Simple right/wrong
  - `answer_score` (NUMERIC 0-100) - **Quality score for grading**
  - `question_rating` (INTEGER 1-5) - **User's rating of question quality**
  - `answered_at` (TIMESTAMP)
- **Constraints**:
  - `answer_score` between 0 and 100
  - `question_rating` between 1 and 5

### DocumentPerformance (`performance.py`)
Tracks user performance on documents.
- **Composite Primary Key**: `user_id` + `doc_id`
- **Fields**: `overall_score` (0-100), `last_reviewed`

### ChapterPerformance (`performance.py`)
Tracks user performance on chapters.
- **Composite Primary Key**: `user_id` + `chapter_id`
- **Fields**: `score` (0-100), `last_reviewed`

## Key Features

### 1. Answer Quality Scoring
The `answer_score` field (0-100) allows for nuanced grading beyond just correct/incorrect:
- 100: Perfect answer
- 75-99: Good answer with minor issues
- 50-74: Partial answer
- 0-49: Poor answer
- Use with LLM to evaluate answer quality

### 2. Question Rating System
Users can rate question quality (1-5 stars) in the `question_rating` field:
- 5 stars: Excellent question
- 4 stars: Good question
- 3 stars: Average question
- 2 stars: Poor question
- 1 star: Very poor question
- Use this data to improve LLM prompts

### 3. Flexible Question Storage
`content` field uses JSONB for different question types:

**MCQ Example**:
```json
{
  "type": "mcq",
  "text": "What is the powerhouse of the cell?",
  "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi apparatus"]
}
```

**Short Answer Example**:
```json
{
  "type": "short",
  "text": "Explain the process of photosynthesis."
}
```

**Index Card Example**:
```json
{
  "type": "index",
  "front": "What is DNA?",
  "back": "Deoxyribonucleic acid, the molecule that carries genetic information."
}
```

## Usage Example

```python
from database.connection import get_db
from database.models import UserProfile, Document, Question, UserAnswer
from sqlalchemy.orm import Session

# Get database session
db: Session = next(get_db())

# Create a user profile (from Auth0 sub)
user = UserProfile(id="auth0|123456")
db.add(user)
db.commit()

# Create a document
document = Document(
    owner_id=user.id,
    name="Biology 101.pdf",
    storage_url="https://storage.url/file.pdf",
    status="processing"
)
db.add(document)
db.commit()

# Create a question
question = Question(
    doc_id=document.id,
    content={
        "type": "mcq",
        "text": "What is the powerhouse of the cell?",
        "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi"]
    },
    correct_answer="Mitochondria",
    topic="Cell Biology"
)
db.add(question)
db.commit()

# Submit an answer
answer = UserAnswer(
    user_id=user.id,
    question_id=question.id,
    user_answer="Mitochondria",
    was_correct=True,
    answer_score=100.0,  # Perfect answer
    question_rating=5     # Excellent question
)
db.add(answer)
db.commit()
```

## Setup

1. Install dependencies:
```bash
pip install sqlalchemy psycopg2-binary alembic supabase
```

2. Set DATABASE_URL in `.env.local`:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

3. Initialize database:
```python
from database.connection import init_db
init_db()  # Creates all tables
```

## Migrations

Use Alembic for database migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
