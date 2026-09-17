import React, { useState, useEffect } from 'react';
import './LearningHistory.css';
import apiService from '../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Format an ISO timestamp string into a human-readable date.
 * e.g. "2026-09-17T18:30:00" → "Sep 17, 2026"
 */
function formatDate(isoString) {
  if (!isoString) return '—';
  try {
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return isoString;
  }
}

/**
 * Return a CSS class modifier based on percentage.
 * Mirrors the QuizInterface score color scheme.
 */
function scoreClass(percentage) {
  if (percentage >= 90) return 'score-excellent';
  if (percentage >= 80) return 'score-great';
  if (percentage >= 70) return 'score-good';
  if (percentage >= 60) return 'score-okay';
  return 'score-needs-work';
}

/**
 * Return a CSS class for the difficulty badge.
 */
function difficultyClass(difficulty) {
  const d = (difficulty || '').toLowerCase();
  if (d === 'easy') return 'badge-easy';
  if (d === 'hard') return 'badge-hard';
  return 'badge-medium';
}

/**
 * Return a CSS class for the recommended difficulty stat value.
 */
function diffValueClass(difficulty) {
  const d = (difficulty || '').toLowerCase();
  if (d === 'easy') return 'diff-easy';
  if (d === 'hard') return 'diff-hard';
  return 'diff-medium';
}

// ─── LearningHistory Component ────────────────────────────────────────────────

/**
 * Learning History page.
 *
 * Props:
 *   onBack — callback to navigate back to the main BookBot view
 */
const LearningHistory = ({ onBack }) => {
  const [performance, setPerformance] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load performance and history on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch both in parallel
      const [perf, hist] = await Promise.all([
        apiService.getPerformance(),
        apiService.getQuizHistory(),
      ]);
      setPerformance(perf);
      setHistory(Array.isArray(hist) ? hist : []);
    } catch (err) {
      console.error('Failed to load learning history:', err);
      setError(
        err?.message ||
        'Could not load your learning history. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // ── Loading ──────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="learning-page">
        <div className="learning-loading">
          <div className="spinner" />
          <p>Loading your learning history…</p>
        </div>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="learning-page">
        <button className="learning-back-btn" onClick={onBack}>
          ← Back
        </button>
        <div className="learning-error">
          <h3>⚠️ Something went wrong</h3>
          <p>{error}</p>
          <button className="retry-btn" onClick={loadData}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const quizzesAttempted = performance?.quizzes_attempted ?? 0;
  const booksStudied = performance?.books_studied ?? 0;
  const averageScore = performance?.average_score;
  const recommendedDifficulty = performance?.recommended_difficulty ?? 'medium';

  // ── Page ─────────────────────────────────────────────────────────────────────

  return (
    <div className="learning-page">

      {/* Back button */}
      <button className="learning-back-btn" onClick={onBack}>
        ← Back to BookBot
      </button>

      {/* Page heading */}
      <div className="learning-header">
        <h1>📈 My Learning</h1>
        <p>Track your progress and see how your quiz performance improves over time.</p>
      </div>

      {/* ── Performance Summary ────────────────────────────────────── */}

      <section className="performance-section">
        <h2>🎯 Performance Summary</h2>

        <div className="stats-grid">

          {/* Average Score */}
          <div className="stat-card">
            <div className="stat-label">Average Score</div>
            <div className="stat-value">
              {averageScore !== null && averageScore !== undefined
                ? `${Math.round(averageScore)}%`
                : '—'}
            </div>
          </div>

          {/* Quizzes Attempted */}
          <div className="stat-card">
            <div className="stat-label">Quizzes Attempted</div>
            <div className="stat-value">{quizzesAttempted}</div>
          </div>

          {/* Books Studied */}
          <div className="stat-card">
            <div className="stat-label">Books Studied</div>
            <div className="stat-value">{booksStudied}</div>
          </div>

          {/* Recommended Difficulty */}
          <div className="stat-card difficulty-card">
            <div className="stat-label">Recommended Difficulty</div>
            <div className={`stat-value ${diffValueClass(recommendedDifficulty)}`}>
              {recommendedDifficulty.charAt(0).toUpperCase() +
                recommendedDifficulty.slice(1)}
            </div>
          </div>

        </div>
      </section>

      {/* ── Quiz History ───────────────────────────────────────────── */}

      <section className="history-section">
        <h2>📚 Quiz History</h2>

        {history.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🎓</span>
            <h3>No quiz attempts yet</h3>
            <p>
              Complete your first quiz to start building your learning history.
              Your scores, books, and progress will appear here.
            </p>
            <button className="empty-state-btn" onClick={onBack}>
              Start a Quiz
            </button>
          </div>
        ) : (
          <div className="attempt-list">
            {history.map((attempt) => {
              const pct = Math.round(attempt.percentage ?? 0);
              return (
                <div key={attempt.id} className="attempt-card">

                  {/* Score circle */}
                  <div className={`attempt-score-circle ${scoreClass(pct)}`}>
                    {pct}%
                  </div>

                  {/* Details */}
                  <div className="attempt-body">
                    <div className="attempt-book-name" title={attempt.book_name}>
                      {attempt.book_name}
                    </div>

                    <div className="attempt-meta">
                      <span className="attempt-fraction">
                        {attempt.score} / {attempt.total_questions}
                      </span>

                      <span className={`difficulty-badge ${difficultyClass(attempt.difficulty)}`}>
                        {attempt.difficulty}
                      </span>

                      <span className="attempt-date">
                        {formatDate(attempt.completed_at)}
                      </span>
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        )}
      </section>

    </div>
  );
};

export default LearningHistory;
