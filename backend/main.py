from fastapi import FastAPI, HTTPException, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import secrets

from models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse
)
from utils import generate_questions_with_neuralseek, validate_answer_with_neuralseek


# ------------------------------------------------------------
# Initialize FastAPI app
# ------------------------------------------------------------
app = FastAPI(
    title="LearnSpace API",
    description="Backend API for PDF-based question generation with NeuralSeek integration",
    version="1.0.0"
)

# Enable CORS (for Next.js frontend during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "*",  # dev only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# In-memory stores
# ------------------------------------------------------------

# Each key = session_token, value = dict of user data & questions
data_store: Dict[str, Dict[str, Any]] = {}

# Each key = username, value = hashed password
user_store: Dict[str, str] = {}

# Each key = session_token, value = user info
active_sessions: Dict[str, Dict[str, Any]] = {}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed


def get_current_user(session_token: Optional[str] = Cookie(None, alias="session_token")) -> Optional[Dict[str, Any]]:
    """Return current user info from cookie, if authenticated"""
    if not session_token:
        return None
    return active_sessions.get(session_token)


# ------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------

@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "LearnSpace API is running",
        "version": "1.0.0",
        "status": "healthy",
    }


# ------------------------------------------------------------
# Auth: Register
# ------------------------------------------------------------

@app.post("/register", response_model=LoginResponse)
async def register(request: LoginRequest, response: Response):
    """Register a new user and create a session"""
    try:
        print(f"\n📥 Registration attempt for user: {request.username}")

        if request.username in user_store:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Store hashed password
        user_store[request.username] = hash_password(request.password)

        # Create session
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "username": request.username,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }

        active_sessions[session_token] = session_data
        data_store[session_token] = {"questions": []}

        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            samesite="lax",
            secure=False,  # Set to True in production with HTTPS
        )

        print(f"✅ Registered and logged in: {request.username}")

        return LoginResponse(
            message="User registered and logged in successfully",
            username=request.username,
            session_id=session_token
        )

    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


# ------------------------------------------------------------
# Auth: Login
# ------------------------------------------------------------

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """Login an existing user"""
    try:
        print(f"\n📥 Login attempt for user: {request.username}")

        if request.username not in user_store:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not verify_password(request.password, user_store[request.username]):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create new session
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "username": request.username,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }

        active_sessions[session_token] = session_data
        data_store[session_token] = {"questions": []}

        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            samesite="lax",
            secure=False
        )

        print(f"✅ Logged in: {request.username}")

        return LoginResponse(
            message="Login successful",
            username=request.username,
            session_id=session_token
        )

    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ------------------------------------------------------------
# Auth: Logout
# ------------------------------------------------------------

@app.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    session_token: Optional[str] = Cookie(None, alias="session_token")
):
    """Logout and clear session"""
    if not current_user or not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = current_user.get("username")
    print(f"\n📥 Logout request for user: {username}")

    # Remove session
    active_sessions.pop(session_token, None)
    data_store.pop(session_token, None)

    # Clear cookie
    response.delete_cookie("session_token")

    print(f"✅ Logged out: {username}")

    return LogoutResponse(message="Logout successful")


# ------------------------------------------------------------
# Generate Questions
# ------------------------------------------------------------

@app.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    session_token: Optional[str] = Cookie(None, alias="session_token")
):
    """Generate questions using NeuralSeek"""
    if not current_user or not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    print(f"\n📥 Generating {request.num_questions} questions for {current_user['username']}")

    try:
        questions = await generate_questions_with_neuralseek(
            num_questions=request.num_questions
        )

        data_store[session_token]["questions"].extend(questions)

        print(f"✅ Generated {len(questions)} questions")

        return GenerateQuestionsResponse(
            message="Questions generated successfully",
            num_questions=len(questions),
            questions=questions
        )

    except Exception as e:
        print(f"❌ Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


# ------------------------------------------------------------
# Submit Answer
# ------------------------------------------------------------

@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    session_token: Optional[str] = Cookie(None, alias="session_token")
):
    """Submit an answer and validate it"""
    if not current_user or not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    print(f"\n📥 Answer submission from {current_user['username']} for question: {request.question_id}")

    try:
        # Make sure the question exists for this session
        questions = data_store.get(session_token, {}).get("questions", [])
        if request.question_id >= len(questions) or request.question_id < 0:
            raise HTTPException(status_code=404, detail="Question not found for this session")

        question_text = questions[request.question_id]

        validation = await validate_answer_with_neuralseek(
            question_text=question_text,
            user_answer=request.answer
        )

        answer_data = {
            "question_id": request.question_id,
            "answer": request.answer,
            "timestamp": datetime.utcnow().isoformat()
        }

        return SubmitAnswerResponse(
            message="Answer submitted successfully",
            question_id=request.question_id,
            answer=request.answer,
            timestamp=answer_data["timestamp"]
        )

    except Exception as e:
        print(f"❌ Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")


# ------------------------------------------------------------
# Current User
# ------------------------------------------------------------

@app.get("/me")
async def get_current_user_info(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Return current user info"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "username": current_user.get("username"),
        "created_at": current_user.get("created_at"),
        "last_activity": current_user.get("last_activity")
    }


# ------------------------------------------------------------
# Run with: uvicorn main:app --reload
# Docs: http://localhost:8000/docs
# ------------------------------------------------------------
