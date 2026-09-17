"""
quiz_routes.py — Authenticated endpoints for the learning progress feature.

Routes (all require a valid Bearer JWT):

    POST /quiz/attempt     — save a completed quiz attempt
    GET  /quiz/history     — return the current user's attempts (newest first)
    GET  /quiz/performance — return aggregate stats + difficulty recommendation

Security contract:
    user_id is ALWAYS extracted from the JWT via get_current_user().
    It is never read from the request body or query parameters.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from difficulty import recommend_difficulty, VALID_DIFFICULTIES
from models import QuizAttempt, User

router = APIRouter(prefix="/quiz", tags=["Quiz Progress"])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class AttemptCreate(BaseModel):
    """Payload for POST /quiz/attempt — submitted by the frontend."""

    book_name: str
    score: int
    total_questions: int
    difficulty: str

    @field_validator("book_name")
    @classmethod
    def book_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("book_name must not be empty.")
        return v[:500]  # cap to column length

    @field_validator("score")
    @classmethod
    def score_not_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("score cannot be negative.")
        return v

    @field_validator("total_questions")
    @classmethod
    def total_questions_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("total_questions must be greater than zero.")
        return v

    @field_validator("difficulty")
    @classmethod
    def difficulty_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_DIFFICULTIES:
            raise ValueError(
                f"difficulty must be one of: {sorted(VALID_DIFFICULTIES)}"
            )
        return v


class AttemptOut(BaseModel):
    """Shape returned in GET /quiz/history."""

    id: int
    book_name: str
    score: int
    total_questions: int
    percentage: float
    difficulty: str
    completed_at: datetime

    model_config = {"from_attributes": True}


class PerformanceOut(BaseModel):
    """Shape returned by GET /quiz/performance."""

    average_score: Optional[float]   # None when no history
    quizzes_attempted: int
    books_studied: int
    recommended_difficulty: str


# ============================================================
# POST /quiz/attempt — save a completed quiz attempt
# ============================================================

@router.post(
    "/attempt",
    status_code=status.HTTP_201_CREATED,
    summary="Save a completed quiz attempt",
)
async def save_attempt(
    payload: AttemptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save a quiz attempt for the currently authenticated user.

    - percentage is calculated server-side (not trusted from client)
    - score must be 0 ≤ score ≤ total_questions
    - difficulty must be one of: easy | medium | hard
    """

    # Cross-field validation: score cannot exceed total_questions
    if payload.score > payload.total_questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="score cannot exceed total_questions.",
        )

    # Calculate percentage server-side
    percentage = round((payload.score / payload.total_questions) * 100, 2)

    attempt = QuizAttempt(
        user_id=current_user.id,   # always from JWT — never from request body
        book_name=payload.book_name,
        score=payload.score,
        total_questions=payload.total_questions,
        percentage=percentage,
        difficulty=payload.difficulty,
        completed_at=datetime.now(timezone.utc),
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "message": "Quiz attempt saved successfully.",
        "attempt_id": attempt.id,
        "percentage": attempt.percentage,
    }


# ============================================================
# GET /quiz/history — return user's attempts, newest first
# ============================================================

@router.get(
    "/history",
    response_model=List[AttemptOut],
    summary="Return the current user's quiz attempt history",
)
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all quiz attempts belonging to the authenticated user,
    ordered newest first.

    A user can only ever see their own attempts — isolation is enforced
    by filtering on user_id from the JWT.
    """

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.completed_at.desc())
        .all()
    )

    return attempts


# ============================================================
# GET /quiz/performance — aggregate stats for current user
# ============================================================

@router.get(
    "/performance",
    response_model=PerformanceOut,
    summary="Return aggregate learning performance statistics",
)
async def get_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return aggregate quiz statistics for the authenticated user:
      - average_score       — average percentage across all attempts
      - quizzes_attempted   — total number of completed quizzes
      - books_studied       — distinct book/document names studied
      - recommended_difficulty — deterministic recommendation from difficulty.py

    All statistics are scoped strictly to the current user — global stats
    across all users are never calculated here.
    """

    # Single aggregation query — efficient even with large history
    result = db.query(
        func.avg(QuizAttempt.percentage).label("avg_score"),
        func.count(QuizAttempt.id).label("total_count"),
        func.count(func.distinct(QuizAttempt.book_name)).label("distinct_books"),
    ).filter(QuizAttempt.user_id == current_user.id).one()

    quizzes_attempted = result.total_count or 0
    books_studied = result.distinct_books or 0

    # avg() returns None when there are no rows
    average_score: Optional[float] = (
        round(result.avg_score, 2) if result.avg_score is not None else None
    )

    recommended = recommend_difficulty(average_score)

    return PerformanceOut(
        average_score=average_score,
        quizzes_attempted=quizzes_attempted,
        books_studied=books_studied,
        recommended_difficulty=recommended,
    )
