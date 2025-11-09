"""
API endpoints for user profile and statistics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db
from database.models.user_answer import UserAnswer
from database.models.user import UserProfile
from database.models.question import Question
from auth import get_current_user

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=Dict[str, Any])
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user profile statistics including:
    - Total answers submitted
    - Correct answers count
    - Average score
    - Recent activity
    """
    try:
        user_id = current_user.get("sub")
        logger.info(f"Fetching stats for user '{user_id}'")

        # Ensure user profile exists
        user_profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user_profile:
            user_profile = UserProfile(id=user_id)
            db.add(user_profile)
            db.commit()

        # Get total answers
        total_answers = (
            db.query(func.count(UserAnswer.id))
            .filter(UserAnswer.user_id == user_id)
            .scalar()
        )

        # Get correct answers count
        correct_answers = (
            db.query(func.count(UserAnswer.id))
            .filter(UserAnswer.user_id == user_id, UserAnswer.was_correct == True)
            .scalar()
        )

        # Get average score
        avg_score = (
            db.query(func.avg(UserAnswer.answer_score))
            .filter(UserAnswer.user_id == user_id)
            .scalar()
        )
        avg_score = float(avg_score) if avg_score else 0.0

        # Calculate accuracy percentage
        accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0.0

        # Get recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_answers = (
            db.query(func.count(UserAnswer.id))
            .filter(
                UserAnswer.user_id == user_id, UserAnswer.answered_at >= seven_days_ago
            )
            .scalar()
        )

        # Calculate streak (consecutive days with activity)
        streak_days = 0
        current_date = datetime.utcnow().date()

        for i in range(365):  # Check up to 365 days back
            check_date = current_date - timedelta(days=i)
            day_start = datetime.combine(check_date, datetime.min.time())
            day_end = datetime.combine(check_date, datetime.max.time())

            has_activity = (
                db.query(func.count(UserAnswer.id))
                .filter(
                    UserAnswer.user_id == user_id,
                    UserAnswer.answered_at >= day_start,
                    UserAnswer.answered_at <= day_end,
                )
                .scalar()
            )

            if has_activity > 0:
                streak_days += 1
            else:
                break

        logger.info(f"✅ Stats retrieved for user '{user_id}'")

        return {
            "total_answers": total_answers or 0,
            "correct_answers": correct_answers or 0,
            "accuracy": round(accuracy, 1),
            "average_score": round(avg_score, 1),
            "recent_activity_7d": recent_answers or 0,
            "streak_days": streak_days,
            "member_since": (
                user_profile.created_at.isoformat()
                if hasattr(user_profile.created_at, "isoformat")
                else None
            ),
        }

    except Exception as e:
        logger.error(f"Failed to fetch user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching statistics: {str(e)}",
        )


@router.get("/recent-answers", response_model=List[Dict[str, Any]])
async def get_recent_answers(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's recent answers with question details
    """
    try:
        user_id = current_user.get("sub")
        logger.info(f"Fetching recent answers for user '{user_id}'")

        # Query recent answers with question details
        recent_answers = (
            db.query(UserAnswer, Question)
            .join(Question, UserAnswer.question_id == Question.id)
            .filter(UserAnswer.user_id == user_id)
            .order_by(desc(UserAnswer.answered_at))
            .limit(limit)
            .all()
        )

        results = []
        for answer, question in recent_answers:
            results.append(
                {
                    "id": str(answer.id),
                    "question_id": str(answer.question_id),
                    "question_topic": question.topic if question else "Unknown",
                    "user_answer": answer.user_answer,
                    "was_correct": answer.was_correct,
                    "answer_score": float(answer.answer_score),
                    "answered_at": answer.answered_at.isoformat(),
                    "is_good_question": answer.isGoodQuestion,
                }
            )

        logger.info(f"✅ Retrieved {len(results)} recent answers")
        return results

    except Exception as e:
        logger.error(f"Failed to fetch recent answers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching recent answers: {str(e)}",
        )


@router.post("/rate-question/{answer_id}")
async def rate_question(
    answer_id: str,
    is_good: bool,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rate a question as good or bad
    """
    try:
        user_id = current_user.get("sub")

        # Find the answer
        answer = (
            db.query(UserAnswer)
            .filter(UserAnswer.id == answer_id, UserAnswer.user_id == user_id)
            .first()
        )

        if not answer:
            raise HTTPException(status_code=404, detail="Answer not found")

        # Update rating using setattr to avoid type checker issues
        setattr(answer, "isGoodQuestion", is_good)
        db.commit()

        return {"message": "Question rated successfully", "is_good": is_good}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to rate question: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while rating the question: {str(e)}",
        )
