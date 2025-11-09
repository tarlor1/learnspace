from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from routes.questions import router as questions_router

app = FastAPI(
    title="LearnSpace API",
    description="Backend API for PDF-based question generation and learning.",
    version="1.0.0",
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


@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "LearnSpace API is running",
        "version": "1.0.0",
        "status": "healthy",
    }


# Include routers
app.include_router(auth_router)
app.include_router(questions_router)


# Run with: uvicorn main:app --reload
# Docs: http://localhost:8000/docs
# ------------------------------------------------------------
