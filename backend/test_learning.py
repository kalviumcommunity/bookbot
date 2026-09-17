"""
test_learning.py — Unit and integration tests for the Learning Progress feature.

Run:
    python test_learning.py
    # or
    python -m pytest test_learning.py -v

Tests cover:
  1. Difficulty recommendation logic (pure function — all boundary cases)
  2. AttemptCreate validation (pydantic schemas)
  3. API integration: save attempt, history ordering, user isolation
"""

import sys
import os
import unittest
from datetime import datetime, timezone, timedelta

# ─── Make sure imports resolve when run from the backend/ directory ──────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# 1. UNIT TESTS — difficulty.recommend_difficulty()
# ============================================================

class TestRecommendDifficulty(unittest.TestCase):
    """All boundary and typical cases for the difficulty recommendation function."""

    def setUp(self):
        from difficulty import recommend_difficulty
        self.f = recommend_difficulty

    def test_no_history_returns_medium(self):
        self.assertEqual(self.f(None), "medium")

    def test_zero_percent_returns_easy(self):
        self.assertEqual(self.f(0.0), "easy")

    def test_40_percent_returns_easy(self):
        self.assertEqual(self.f(40.0), "easy")

    def test_49_9_returns_easy(self):
        self.assertEqual(self.f(49.9), "easy")

    def test_50_percent_returns_medium(self):
        self.assertEqual(self.f(50.0), "medium")

    def test_74_percent_returns_medium(self):
        self.assertEqual(self.f(74.0), "medium")

    def test_74_9_returns_medium(self):
        self.assertEqual(self.f(74.9), "medium")

    def test_75_percent_returns_hard(self):
        self.assertEqual(self.f(75.0), "hard")

    def test_90_percent_returns_hard(self):
        self.assertEqual(self.f(90.0), "hard")

    def test_100_percent_returns_hard(self):
        self.assertEqual(self.f(100.0), "hard")

    def test_return_type_is_string(self):
        for score in [None, 0, 40, 50, 74, 75, 90, 100]:
            result = self.f(score)
            self.assertIsInstance(result, str)
            self.assertIn(result, {"easy", "medium", "hard"})


# ============================================================
# 2. UNIT TESTS — AttemptCreate pydantic validation
# ============================================================

class TestAttemptValidation(unittest.TestCase):
    """Verify that invalid attempt payloads are rejected before hitting the DB."""

    def _make(self, **kwargs):
        from quiz_routes import AttemptCreate
        defaults = {
            "book_name": "Test Book",
            "score": 7,
            "total_questions": 10,
            "difficulty": "medium",
        }
        defaults.update(kwargs)
        return AttemptCreate(**defaults)

    def test_valid_attempt_passes(self):
        attempt = self._make()
        self.assertEqual(attempt.score, 7)

    def test_negative_score_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._make(score=-1)

    def test_zero_total_questions_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._make(total_questions=0)

    def test_negative_total_questions_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._make(total_questions=-5)

    def test_invalid_difficulty_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._make(difficulty="extreme")

    def test_empty_book_name_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._make(book_name="   ")

    def test_difficulty_case_insensitive_normalized(self):
        attempt = self._make(difficulty="HARD")
        self.assertEqual(attempt.difficulty, "hard")

    def test_difficulty_medium_valid(self):
        attempt = self._make(difficulty="medium")
        self.assertEqual(attempt.difficulty, "medium")

    def test_difficulty_easy_valid(self):
        attempt = self._make(difficulty="easy")
        self.assertEqual(attempt.difficulty, "easy")


# ============================================================
# 3. INTEGRATION TESTS — FastAPI TestClient
# ============================================================

class TestQuizAPI(unittest.TestCase):
    """
    Integration tests against the live FastAPI app using TestClient.

    Patches database.engine and database.SessionLocal before issuing any
    requests so every route (including auth_routes) uses the test database.
    """

    @classmethod
    def setUpClass(cls):
        import database as db_module
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database import Base
        from fastapi.testclient import TestClient
        import api

        # Use a named temp file so we avoid in-memory isolation issues
        cls._test_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bookbot_test.db"
        )
        # Remove stale test DB if it exists
        if os.path.exists(cls._test_db_path):
            os.remove(cls._test_db_path)

        cls._test_engine = create_engine(
            f"sqlite:///{cls._test_db_path}",
            connect_args={"check_same_thread": False},
        )
        cls._TestSession = sessionmaker(
            bind=cls._test_engine, autocommit=False, autoflush=False
        )

        # Create all tables in the test DB
        Base.metadata.create_all(bind=cls._test_engine)

        # Patch the database module globals so ALL code paths use our test DB
        cls._orig_engine = db_module.engine
        cls._orig_session = db_module.SessionLocal
        db_module.engine = cls._test_engine
        db_module.SessionLocal = cls._TestSession

        cls.client = TestClient(api.app)

        # Register user A
        resp_a = cls.client.post("/auth/signup", json={
            "name": "Alice",
            "email": "alice@test.com",
            "password": "password123",
        })
        cls.token_a = resp_a.json().get("access_token", "")

        # Register user B
        resp_b = cls.client.post("/auth/signup", json={
            "name": "Bob",
            "email": "bob@test.com",
            "password": "password456",
        })
        cls.token_b = resp_b.json().get("access_token", "")

    @classmethod
    def tearDownClass(cls):
        import database as db_module
        # Restore the real engine
        db_module.engine = cls._orig_engine
        db_module.SessionLocal = cls._orig_session
        # Remove the test DB file
        if os.path.exists(cls._test_db_path):
            try:
                cls._test_engine.dispose()
                os.remove(cls._test_db_path)
            except OSError:
                pass  # Windows may lock the file briefly



    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    # ── Authentication guard ─────────────────────────────────

    def test_attempt_requires_auth(self):
        resp = self.client.post("/quiz/attempt", json={
            "book_name": "Book",
            "score": 5,
            "total_questions": 10,
            "difficulty": "medium",
        })
        self.assertEqual(resp.status_code, 401)

    def test_history_requires_auth(self):
        resp = self.client.get("/quiz/history")
        self.assertEqual(resp.status_code, 401)

    def test_performance_requires_auth(self):
        resp = self.client.get("/quiz/performance")
        self.assertEqual(resp.status_code, 401)

    # ── Save attempt ─────────────────────────────────────────

    def test_save_valid_attempt(self):
        resp = self.client.post("/quiz/attempt", json={
            "book_name": "Atomic Habits",
            "score": 8,
            "total_questions": 10,
            "difficulty": "medium",
        }, headers=self._headers(self.token_a))
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("attempt_id", data)
        self.assertEqual(data["percentage"], 80.0)

    def test_save_attempt_rejects_score_exceeds_total(self):
        resp = self.client.post("/quiz/attempt", json={
            "book_name": "Book",
            "score": 11,
            "total_questions": 10,
            "difficulty": "medium",
        }, headers=self._headers(self.token_a))
        self.assertIn(resp.status_code, [422, 400])

    def test_save_attempt_rejects_negative_score(self):
        resp = self.client.post("/quiz/attempt", json={
            "book_name": "Book",
            "score": -1,
            "total_questions": 10,
            "difficulty": "medium",
        }, headers=self._headers(self.token_a))
        self.assertEqual(resp.status_code, 422)

    def test_save_attempt_rejects_zero_total(self):
        resp = self.client.post("/quiz/attempt", json={
            "book_name": "Book",
            "score": 0,
            "total_questions": 0,
            "difficulty": "medium",
        }, headers=self._headers(self.token_a))
        self.assertEqual(resp.status_code, 422)

    def test_save_attempt_rejects_invalid_difficulty(self):
        resp = self.client.post("/quiz/attempt", json={
            "book_name": "Book",
            "score": 5,
            "total_questions": 10,
            "difficulty": "extreme",
        }, headers=self._headers(self.token_a))
        self.assertEqual(resp.status_code, 422)

    # ── History ordering ─────────────────────────────────────

    def test_history_ordered_newest_first(self):
        """Save two attempts for user A, verify descending order."""
        self.client.post("/quiz/attempt", json={
            "book_name": "Python Basics",
            "score": 4,
            "total_questions": 10,
            "difficulty": "easy",
        }, headers=self._headers(self.token_a))

        self.client.post("/quiz/attempt", json={
            "book_name": "Machine Learning",
            "score": 9,
            "total_questions": 10,
            "difficulty": "hard",
        }, headers=self._headers(self.token_a))

        resp = self.client.get("/quiz/history", headers=self._headers(self.token_a))
        self.assertEqual(resp.status_code, 200)
        history = resp.json()
        self.assertGreaterEqual(len(history), 2)

        timestamps = [h["completed_at"] for h in history]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    # ── User isolation ───────────────────────────────────────

    def test_user_b_sees_empty_history_initially(self):
        """User B should have no attempts at all (isolated DB session)."""
        resp = self.client.get("/quiz/history", headers=self._headers(self.token_b))
        self.assertEqual(resp.status_code, 200)
        history = resp.json()
        # Bob has made no attempts yet — should be empty
        bob_books = [h["book_name"] for h in history]
        self.assertNotIn("Atomic Habits", bob_books)

    def test_user_b_after_own_attempt_sees_only_own(self):
        """After User B saves an attempt, they only see their own."""
        self.client.post("/quiz/attempt", json={
            "book_name": "Bob's Book",
            "score": 3,
            "total_questions": 5,
            "difficulty": "easy",
        }, headers=self._headers(self.token_b))

        resp_b = self.client.get("/quiz/history", headers=self._headers(self.token_b))
        history_b = resp_b.json()
        book_names_b = [h["book_name"] for h in history_b]
        self.assertIn("Bob's Book", book_names_b)

        # User A's history should NOT contain Bob's book
        resp_a = self.client.get("/quiz/history", headers=self._headers(self.token_a))
        history_a = resp_a.json()
        book_names_a = [h["book_name"] for h in history_a]
        self.assertNotIn("Bob's Book", book_names_a)

    # ── Performance endpoint ─────────────────────────────────

    def test_performance_for_new_user_returns_medium(self):
        resp = self.client.post("/auth/signup", json={
            "name": "Carol",
            "email": "carol@test.com",
            "password": "password789",
        })
        token_c = resp.json().get("access_token", "")

        perf = self.client.get("/quiz/performance", headers=self._headers(token_c))
        self.assertEqual(perf.status_code, 200)
        data = perf.json()
        self.assertEqual(data["quizzes_attempted"], 0)
        self.assertIsNone(data["average_score"])
        self.assertEqual(data["recommended_difficulty"], "medium")

    def test_performance_calculates_correctly_for_user_a(self):
        perf = self.client.get("/quiz/performance", headers=self._headers(self.token_a))
        self.assertEqual(perf.status_code, 200)
        data = perf.json()
        self.assertGreater(data["quizzes_attempted"], 0)
        self.assertGreater(data["books_studied"], 0)
        self.assertIsNotNone(data["average_score"])
        self.assertIn(data["recommended_difficulty"], ["easy", "medium", "hard"])





# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("BookBot — Learning Progress Feature Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
