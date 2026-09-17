import React, { useEffect, useState } from 'react';
import './SummaryDisplay.css';
import apiService from '../services/api';

const SummaryDisplay = ({
  file,
  content,
  onSummaryGenerated,
  onGenerateQuiz,
  onStartChat,
  onReset,
}) => {
  const [summary, setSummary] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isQuizGenerating, setIsQuizGenerating] = useState(false);
  const [error, setError] = useState(null);
  // Adaptive difficulty
  const [recommendedDifficulty, setRecommendedDifficulty] = useState(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState('medium');

  useEffect(() => {
    if (content && !summary) {
      generateSummary();
    }
  }, [content]);

  // Fetch recommended difficulty once on mount (non-blocking)
  useEffect(() => {
    apiService.getPerformance()
      .then(data => {
        const rec = data?.recommended_difficulty || 'medium';
        setRecommendedDifficulty(rec);
        setSelectedDifficulty(rec);
      })
      .catch(() => {
        // Silently ignore — difficulty recommendation is optional
      });
  }, []);

  // ----------------------------------------------------------
  // REAL AI SUMMARY
  // ----------------------------------------------------------

  const generateSummary = async () => {
    if (!content || !content.trim()) {
      setError(
        'No readable text was extracted from this document.'
      );
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      console.log(
        `Generating summary from ${content.length} characters...`
      );

      const summaryData = await apiService.generateSummary(
        content,
        file?.name || 'Document'
      );

      if (!summaryData || !summaryData.summary) {
        throw new Error(
          'The AI did not return a valid summary.'
        );
      }

      const wordCount = content
        .trim()
        .split(/\s+/)
        .filter(Boolean).length;

      const normalizedSummary = {
        title:
          summaryData.title ||
          file?.name ||
          'Document',

        type:
          summaryData.type ||
          file?.type ||
          'document',

        summary: summaryData.summary,

        highlights:
          summaryData.key_points ||
          summaryData.highlights ||
          [],

        difficulty:
          summaryData.difficulty ||
          'intermediate',

        word_count: wordCount,

        char_count: content.length,
      };

      setSummary(normalizedSummary);
      onSummaryGenerated(normalizedSummary);

    } catch (err) {
      console.error(
        'Summary generation error:',
        err
      );

      setError(
        err?.message ||
        'Failed to generate summary. Please try again.'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // ----------------------------------------------------------
  // REAL AI QUIZ
  // ----------------------------------------------------------

  const handleGenerateQuiz = async (questionCount) => {
    if (isQuizGenerating) {
      return;
    }

    if (!content || !content.trim()) {
      setError(
        'No document content is available for quiz generation.'
      );
      return;
    }

    setIsQuizGenerating(true);
    setError(null);

    try {
      console.log(
        `Generating ${questionCount} quiz questions (difficulty: ${selectedDifficulty})...`
      );

      // Pass both questionCount and difficulty to the parent handler
      await onGenerateQuiz(questionCount, selectedDifficulty);

    } catch (err) {
      console.error(
        'Quiz generation error:',
        err
      );

      setError(
        err?.message ||
        'Failed to generate quiz. Please try again.'
      );

      setIsQuizGenerating(false);
      return;
    }

    // App.jsx changes the view after successful generation.
    setIsQuizGenerating(false);
  };

  // ----------------------------------------------------------
  // LOADING STATE - SUMMARY
  // ----------------------------------------------------------

  if (isGenerating) {
    return (
      <div className="summary-container">
        <div className="generating-state">
          <div className="spinner"></div>

          <h3>
            🤖 AI is analyzing your document...
          </h3>

          <p>
            Creating a summary from the actual document content.
          </p>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------------
  // ERROR STATE
  // ----------------------------------------------------------

  if (error && !summary) {
    return (
      <div className="summary-container">
        <div className="error-state">

          <h3>❌ Error</h3>

          <p>{error}</p>

          <button
            onClick={generateSummary}
            className="retry-btn"
          >
            Try Again
          </button>

          <button
            onClick={onReset}
            className="reset-btn"
          >
            Upload New File
          </button>

        </div>
      </div>
    );
  }

  // ----------------------------------------------------------
  // NO SUMMARY
  // ----------------------------------------------------------

  if (!summary) {
    return null;
  }

  // ----------------------------------------------------------
  // SUMMARY UI
  // ----------------------------------------------------------

  return (
    <div className="summary-container">

      <div className="summary-header">

        <h2>
          📖 Document Summary
        </h2>

        <div className="file-info">
          {/* File information intentionally hidden */}
        </div>

      </div>

      <div className="summary-content">

        <div className="summary-section">

          <h3>
            📝 Summary
          </h3>

          <p className="summary-text">
            {summary.summary}
          </p>

        </div>

        {summary.highlights &&
          summary.highlights.length > 0 && (

            <div className="highlights-section">

              <h3>
                ✨ Topic Highlights
              </h3>

              <ul className="highlights-list stagger-list">

                {summary.highlights.map(
                  (highlight, index) => (

                    <li
                      key={index}
                      className="highlight-item"
                    >
                      {highlight}
                    </li>

                  )
                )}

              </ul>

            </div>

          )}

      </div>

      <div className="summary-actions">

        {/* ------------------------------------------------ */}
        {/* CHAT */}
        {/* ------------------------------------------------ */}

        <h3>
          💬 Ask Questions
        </h3>

        <p>
          Chat directly with your interactive AI tutor
          about the document's contents.
        </p>

        <button
          onClick={onStartChat}
          className="chat-action-btn"
          disabled={isQuizGenerating}
        >
          💬 Chat with Document
        </button>

        {/* ------------------------------------------------ */}
        {/* DIFFICULTY RECOMMENDATION */}
        {/* ------------------------------------------------ */}

        {recommendedDifficulty && (
          <div className="difficulty-recommendation">
            <div className="diff-rec-label">
              💡 Recommended difficulty
              <span className={`diff-rec-badge diff-${recommendedDifficulty}`}>
                {recommendedDifficulty.charAt(0).toUpperCase() + recommendedDifficulty.slice(1)}
              </span>
            </div>
            <p className="diff-rec-hint">
              Based on your previous quiz performance.
            </p>
            <div className="diff-selector">
              {['easy', 'medium', 'hard'].map(d => (
                <button
                  key={d}
                  className={`diff-btn ${selectedDifficulty === d ? 'active' : ''}`}
                  onClick={() => setSelectedDifficulty(d)}
                  disabled={isQuizGenerating}
                >
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ------------------------------------------------ */}
        {/* QUIZ */}
        {/* ------------------------------------------------ */}

        <h3 style={{ marginTop: '2rem' }}>
          🎯 Ready for a Quiz?
        </h3>

        <p>
          Test your understanding with an AI-generated
          quiz based on this document.
        </p>

        {error && (
          <div className="error-state">
            <p>{error}</p>
          </div>
        )}

        {isQuizGenerating && (
          <div className="generating-state quiz-generating">

            <div className="spinner"></div>

            <h3>
              🤖 Generating Quiz...
            </h3>

            <p>
              Creating questions from your document.
              Please wait a moment.
            </p>

          </div>
        )}

        <div className="quiz-options">

          {/* QUICK QUIZ */}

          <button
            className="quiz-btn"
            onClick={() =>
              handleGenerateQuiz(5)
            }
            disabled={isQuizGenerating}
          >
            {isQuizGenerating
              ? '⏳ Generating...'
              : '📝 Quick Quiz (5 questions)'}
          </button>

          {/* STANDARD QUIZ */}

          <button
            className="quiz-btn"
            onClick={() =>
              handleGenerateQuiz(10)
            }
            disabled={isQuizGenerating}
          >
            {isQuizGenerating
              ? '⏳ Generating...'
              : '📚 Standard Quiz (10 questions)'}
          </button>

          {/* COMPREHENSIVE QUIZ */}

          <button
            className="quiz-btn"
            onClick={() =>
              handleGenerateQuiz(20)
            }
            disabled={isQuizGenerating}
          >
            {isQuizGenerating
              ? '⏳ Generating...'
              : '🧠 Comprehensive Quiz (20 questions)'}
          </button>

          {/* CUSTOM QUIZ */}

          <button
            className="quiz-btn custom"
            disabled={isQuizGenerating}
            onClick={() => {

              const count = window.prompt(
                'Enter number of questions (1-20):',
                '10'
              );

              if (!count) {
                return;
              }

              const parsedCount =
                Number.parseInt(
                  count,
                  10
                );

              if (
                Number.isInteger(parsedCount) &&
                parsedCount >= 1 &&
                parsedCount <= 20
              ) {
                handleGenerateQuiz(
                  parsedCount
                );
              } else {
                setError(
                  'Please enter a number between 1 and 20.'
                );
              }

            }}
          >
            {isQuizGenerating
              ? '⏳ Generating...'
              : '⚙️ Custom Quiz'}
          </button>

        </div>

        {/* ------------------------------------------------ */}
        {/* RESET */}
        {/* ------------------------------------------------ */}

        <button
          onClick={onReset}
          className="reset-btn"
          disabled={isQuizGenerating}
        >
          📄 Upload Another File
        </button>

      </div>

    </div>
  );
};

export default SummaryDisplay;