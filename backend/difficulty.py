"""
difficulty.py — Deterministic adaptive difficulty recommendation.

Intentional design decision: difficulty is determined by simple, testable
rules rather than asking the LLM.  This keeps the recommendation:
  - predictable (same input always gives same output)
  - testable (pure function, no I/O)
  - transparent (users can understand why they got a recommendation)
  - inexpensive (no Gemini API call required)

Usage:
    from difficulty import recommend_difficulty, VALID_DIFFICULTIES

    level = recommend_difficulty(average_score=76.0)  # → "hard"
    level = recommend_difficulty(average_score=None)  # → "medium" (no history)
"""

from typing import Optional

# ============================================================
# CONSTANTS
# ============================================================

VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})

# Thresholds — adjust here without touching route code
_THRESHOLD_HARD = 75.0   # >= 75 % → hard
_THRESHOLD_EASY = 50.0   # <  50 % → easy
                          # 50–74 % → medium


# ============================================================
# CORE FUNCTION
# ============================================================

def recommend_difficulty(average_score: Optional[float]) -> str:
    """
    Return a recommended difficulty string based on the user's average score.

    Args:
        average_score: The user's average quiz percentage (0–100), or None if
                       the user has no quiz history.

    Returns:
        One of: "easy", "medium", "hard"

    Rules:
        No history (None) → "medium"
        average_score < 50  → "easy"
        50 ≤ average_score < 75 → "medium"
        average_score ≥ 75  → "hard"
    """
    if average_score is None:
        return "medium"

    if average_score < _THRESHOLD_EASY:
        return "easy"

    if average_score < _THRESHOLD_HARD:
        return "medium"

    return "hard"
