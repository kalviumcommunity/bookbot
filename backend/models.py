"""
models.py — SQLAlchemy ORM models for BookBot.

Defines:
  - User       — authentication accounts
  - QuizAttempt — per-user quiz history for the learning progress feature
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship

from database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship — access user.quiz_attempts to get all attempts
    quiz_attempts = relationship(
        "QuizAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="QuizAttempt.completed_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ============================================================
# QUIZ ATTEMPT MODEL
# ============================================================

class QuizAttempt(Base):
    """
    Stores a single completed quiz attempt for a user.

    Security note: user_id is always set server-side from the JWT —
    it is never accepted from the client request body.

    Snapshot fields (nullable — absent on legacy rows):
      source_type     — "pdf" | "txt" | "docx" | "text" (pasted text)
      questions_json  — JSON array of question objects (immutable snapshot)
      answers_json    — JSON array of {question_index, selected_answer}
    """

    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_name = Column(String(500), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    difficulty = Column(String(20), nullable=False)
    completed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Snapshot fields (nullable — legacy rows have NULL here) ──────────────
    # What kind of source was used: "pdf", "txt", "docx", "text"
    source_type = Column(String(20), nullable=True)
    # JSON-serialised list of question objects (immutable at save time)
    questions_json = Column(Text, nullable=True)
    # JSON-serialised list of {question_index, selected_answer}
    answers_json = Column(Text, nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="quiz_attempts")

    def __repr__(self) -> str:
        return (
            f"<QuizAttempt id={self.id} user_id={self.user_id}"
            f" book={self.book_name!r} score={self.score}/{self.total_questions}>"
        )
