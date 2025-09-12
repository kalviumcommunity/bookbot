import React, { useState } from 'react';
import './QuizGenerator.css';

const QuizGenerator = ({ onQuizGenerated, isGenerating, error }) => {
  const [questionCount, setQuestionCount] = useState(10);
  const [quizType, setQuizType] = useState('mixed');

  const handleGenerateQuiz = () => {
    onQuizGenerated(questionCount, quizType);
  };

  return (
    <div className="quiz-generator">
      <h3>🎯 Generate Quiz</h3>
      
      <div className="quiz-settings">
        <div className="setting-group">
          <label htmlFor="questionCount">Number of Questions:</label>
          <select 
            id="questionCount"
            value={questionCount} 
            onChange={(e) => setQuestionCount(parseInt(e.target.value))}
            disabled={isGenerating}
          >
            <option value={5}>5 Questions (Quick)</option>
            <option value={10}>10 Questions (Standard)</option>
            <option value={15}>15 Questions (Detailed)</option>
            <option value={20}>20 Questions (Comprehensive)</option>
            <option value={25}>25 Questions (Thorough)</option>
            <option value={30}>30 Questions (Extensive)</option>
          </select>
        </div>

        <div className="setting-group">
          <label htmlFor="quizType">Quiz Type:</label>
          <select 
            id="quizType"
            value={quizType} 
            onChange={(e) => setQuizType(e.target.value)}
            disabled={isGenerating}
          >
            <option value="mixed">Mixed Questions</option>
            <option value="concepts">Key Concepts</option>
            <option value="details">Specific Details</option>
            <option value="application">Practical Application</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <button 
        onClick={handleGenerateQuiz}
        disabled={isGenerating}
        className={`generate-btn ${isGenerating ? 'generating' : ''}`}
      >
        {isGenerating ? (
          <>
            <div className="spinner small"></div>
            Generating Quiz...
          </>
        ) : (
          '🚀 Generate Quiz'
        )}
      </button>

      <div className="quiz-preview">
        <h4>What to expect:</h4>
        <ul>
          <li>Multiple choice questions</li>
          <li>Questions based on document content</li>
          <li>Immediate feedback after completion</li>
          <li>Detailed explanations for answers</li>
        </ul>
      </div>
    </div>
  );
};

export default QuizGenerator;
