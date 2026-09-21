import React, { useState, useEffect } from 'react';
import './QuizReview.css';
import apiService from '../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

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

function sourceIcon(sourceType) {
  if (!sourceType) return '📄';
  const t = sourceType.toLowerCase();
  if (t === 'text') return '📝';
  if (t === 'pdf') return '📄';
  if (t === 'docx' || t === 'doc') return '📝';
  if (t === 'txt') return '📃';
  return '📄';
}

function difficultyClass(difficulty) {
  const d = (difficulty || '').toLowerCase();
  if (d === 'easy') return 'badge-easy';
  if (d === 'hard') return 'badge-hard';
  return 'badge-medium';
}

/**
 * Find a question's selected answer from the answers array.
 * answers = [{question_index, selected_answer}]
 */
function getSelectedAnswer(answers, questionIndex) {
  if (!Array.isArray(answers)) return null;
  const entry = answers.find((a) => a.question_index === questionIndex);
  return entry ? entry.selected_answer : null;
}

// ─── QuizReview Component ─────────────────────────────────────────────────────

/**
 * Quiz Review page — shows the exact questions, options, user answers,
 * and correct answers for a previously completed quiz attempt.
 *
 * Props:
 *   attemptId — integer ID of the quiz attempt to display
 *   onBack    — callback to return to the Learning History page
 */
const QuizReview = ({ attemptId, onBack }) => {
  const [attempt, setAttempt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiService.getQuizAttempt(attemptId);
        if (!cancelled) setAttempt(data);
      } catch (err) {
        if (!cancelled) {
          setError(
            err?.message ||
            'Could not load this quiz attempt. Please try again.'
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [attemptId]);

  // ── Loading ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="review-page">
        <div className="learning-loading">
          <div className="spinner" />
          <p>Loading quiz review…</p>
        </div>
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="review-page">
        <button className="learning-back-btn" onClick={onBack}>
          ← Back to Learning
        </button>
        <div className="learning-error">
          <h3>⚠️ Something went wrong</h3>
          <p>{error}</p>
          <button className="retry-btn" onClick={onBack}>
            ← Back to Learning
          </button>
        </div>
      </div>
    );
  }

  if (!attempt) return null;

  const {
    book_name,
    source_type,
    score,
    total_questions,
    percentage,
    difficulty,
    completed_at,
    has_snapshot,
    questions,
    answers,
  } = attempt;

  const wrongCount = total_questions - score;
  const pctRounded = Math.round(percentage);

  // ── Page ───────────────────────────────────────────────────────────────────

  return (
    <div className="review-page">

      {/* Back button */}
      <button className="learning-back-btn" onClick={onBack}>
        ← Back to Learning
      </button>

      {/* Page heading */}
      <div className="learning-header">
        <h1>🔍 Quiz Review</h1>
        <p>Review your answers for this quiz attempt.</p>
      </div>

      {/* ── Header Card ─────────────────────────────────────────────────────── */}

      <div className="review-header-card">

        {/* Source */}
        <div className="review-source">
          <span className="review-source-icon">{sourceIcon(source_type)}</span>
          <span className="review-source-name" title={book_name}>
            {book_name}
          </span>
        </div>

        {/* Meta chips */}
        <div className="review-meta">
          <span className={`difficulty-badge ${difficultyClass(difficulty)}`}>
            {difficulty}
          </span>
          <span className="review-date">{formatDate(completed_at)}</span>
        </div>

      </div>

      {/* ── Score Summary ────────────────────────────────────────────────────── */}

      <div className="review-stats">
        <div className="review-stat-card">
          <div className="stat-label">Score</div>
          <div className="stat-value review-score-val">{score} / {total_questions}</div>
        </div>
        <div className="review-stat-card">
          <div className="stat-label">Percentage</div>
          <div className="stat-value review-score-val">{pctRounded}%</div>
        </div>
        <div className="review-stat-card">
          <div className="stat-label">Correct</div>
          <div className="stat-value review-correct-val">✓ {score}</div>
        </div>
        <div className="review-stat-card">
          <div className="stat-label">Wrong</div>
          <div className="stat-value review-wrong-val">✗ {wrongCount}</div>
        </div>
      </div>

      {/* ── No snapshot — legacy attempt ─────────────────────────────────────── */}

      {!has_snapshot && (
        <div className="review-no-snapshot">
          <span className="review-no-snapshot-icon">📋</span>
          <h3>Detailed review not available</h3>
          <p>
            This attempt was recorded before quiz snapshots were supported.
            The summary above is still accurate, but the individual questions
            and answers were not stored at the time.
          </p>
          <p>
            Future quizzes will include full question-by-question review.
          </p>
        </div>
      )}

      {/* ── Question-by-question review ───────────────────────────────────────── */}

      {has_snapshot && Array.isArray(questions) && (
        <section className="review-questions-section">
          <h2>📝 Question Review</h2>

          {questions.map((q, idx) => {
            const selected = getSelectedAnswer(answers, idx);
            const correct = q.correct_answer;
            const isCorrect = selected !== null && selected === correct;
            const isWrong = selected !== null && selected !== correct;
            const notAnswered = selected === null || selected === undefined;

            return (
              <div
                key={idx}
                className={`review-question-card ${
                  isCorrect ? 'review-question-card--correct' :
                  isWrong   ? 'review-question-card--wrong' :
                              'review-question-card--unanswered'
                }`}
              >
                {/* Question number + verdict */}
                <div className="review-question-header">
                  <span className="review-question-num">Q{idx + 1}</span>
                  {isCorrect && (
                    <span className="review-verdict review-verdict--correct">
                      ✓ Correct
                    </span>
                  )}
                  {isWrong && (
                    <span className="review-verdict review-verdict--wrong">
                      ✗ Wrong
                    </span>
                  )}
                  {notAnswered && (
                    <span className="review-verdict review-verdict--unanswered">
                      — Not answered
                    </span>
                  )}
                </div>

                {/* Question text */}
                <p className="review-question-text">{q.question}</p>

                {/* Options list */}
                <div className="review-options">
                  {(q.options || []).map((option, oi) => {
                    const isSelectedOption = option === selected;
                    const isCorrectOption  = option === correct;

                    let optClass = 'review-option';
                    if (isCorrectOption) optClass += ' review-option--correct';
                    else if (isSelectedOption && isWrong) optClass += ' review-option--wrong-selected';

                    return (
                      <div key={oi} className={optClass}>
                        <span className="review-option-marker">
                          {isCorrectOption ? '✓' : isSelectedOption ? '✗' : '○'}
                        </span>
                        <span className="review-option-text">{option}</span>
                        {isCorrectOption && (
                          <span className="review-option-label review-option-label--correct">
                            Correct
                          </span>
                        )}
                        {isSelectedOption && isWrong && (
                          <span className="review-option-label review-option-label--yours">
                            Your answer
                          </span>
                        )}
                        {isSelectedOption && isCorrect && (
                          <span className="review-option-label review-option-label--correct">
                            Your answer · Correct
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Not answered note */}
                {notAnswered && (
                  <p className="review-not-answered-note">
                    You did not answer this question.
                    The correct answer is highlighted above.
                  </p>
                )}

              </div>
            );
          })}
        </section>
      )}

      {/* Bottom back button */}
      <button className="review-back-bottom-btn" onClick={onBack}>
        ← Back to Learning
      </button>

    </div>
  );
};

export default QuizReview;
