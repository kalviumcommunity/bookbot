import React, { useState, useEffect } from 'react';
import './QuizInterface.css';

const QuizInterface = ({ quiz, onBackToSummary, onReset }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes default
  const [quizStarted, setQuizStarted] = useState(false);

  useEffect(() => {
    let timer;
    if (quizStarted && timeLeft > 0 && !showResults) {
      timer = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [quizStarted, timeLeft, showResults]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerSelect = (questionIndex, answer) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionIndex]: answer
    }));
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      setShowResults(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  const calculateScore = () => {
    let correct = 0;
    quiz.questions.forEach((question, index) => {
      if (selectedAnswers[index] === question.answer) {
        correct++;
      }
    });
    return {
      correct,
      total: quiz.questions.length,
      percentage: Math.round((correct / quiz.questions.length) * 100)
    };
  };

  const getScoreMessage = (percentage) => {
    if (percentage >= 90) return { message: "Excellent! 🎉", color: "excellent" };
    if (percentage >= 80) return { message: "Great job! 👏", color: "great" };
    if (percentage >= 70) return { message: "Good work! 👍", color: "good" };
    if (percentage >= 60) return { message: "Not bad! 💪", color: "okay" };
    return { message: "Keep studying! 📚", color: "needs-work" };
  };

  const startQuiz = () => {
    setQuizStarted(true);
  };

  if (!quiz || !quiz.questions) {
    return (
      <div className="quiz-container">
        <div className="error-state">
          <h3>❌ No quiz data available</h3>
          <button onClick={onBackToSummary} className="back-btn">
            Back to Summary
          </button>
        </div>
      </div>
    );
  }

  if (!quizStarted) {
    return (
      <div className="quiz-container">
        <div className="quiz-intro">
          <h2>🧠 Quiz Ready!</h2>
          <div className="quiz-info">
            <p><strong>Questions:</strong> {quiz.questions.length}</p>
            <p><strong>Time Limit:</strong> {formatTime(timeLeft)}</p>
            <p><strong>Instructions:</strong></p>
            <ul>
              <li>Read each question carefully</li>
              <li>Select the best answer</li>
              <li>You can navigate back and forth</li>
              <li>Take your time, but watch the clock!</li>
            </ul>
          </div>
          <button onClick={startQuiz} className="start-quiz-btn">
            Start Quiz 🚀
          </button>
          <button onClick={onBackToSummary} className="back-btn">
            Back to Summary
          </button>
        </div>
      </div>
    );
  }

  if (showResults) {
    const score = calculateScore();
    const scoreInfo = getScoreMessage(score.percentage);

    return (
      <div className="quiz-container">
        <div className="quiz-results">
          <h2>🎯 Quiz Complete!</h2>
          <div className={`score-display ${scoreInfo.color}`}>
            <div className="score-circle">
              <span className="score-percentage">{score.percentage}%</span>
              <span className="score-fraction">{score.correct}/{score.total}</span>
            </div>
            <h3 className="score-message">{scoreInfo.message}</h3>
          </div>

          <div className="detailed-results">
            <h4>📊 Detailed Results</h4>
            {quiz.questions.map((question, index) => {
              const userAnswer = selectedAnswers[index];
              const isCorrect = userAnswer === question.answer;
              
              return (
                <div key={index} className={`result-item ${isCorrect ? 'correct' : 'incorrect'}`}>
                  <div className="question-result">
                    <strong>Q{index + 1}:</strong> {question.question}
                  </div>
                  <div className="answer-result">
                    <span className="user-answer">
                      Your answer: {userAnswer || 'Not answered'}
                    </span>
                    {!isCorrect && (
                      <span className="correct-answer">
                        Correct answer: {question.answer}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="result-actions">
            <button onClick={() => {
              setCurrentQuestion(0);
              setSelectedAnswers({});
              setShowResults(false);
              setQuizStarted(false);
              setTimeLeft(600);
            }} className="retake-btn">
              🔄 Retake Quiz
            </button>
            <button onClick={onBackToSummary} className="back-btn">
              📖 Back to Summary
            </button>
            <button onClick={onReset} className="reset-btn">
              📄 New Document
            </button>
          </div>
        </div>
      </div>
    );
  }

  const question = quiz.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <div className="quiz-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="progress-text">
            Question {currentQuestion + 1} of {quiz.questions.length}
          </span>
        </div>
        <div className="quiz-timer">
          ⏰ {formatTime(timeLeft)}
        </div>
      </div>

      <div className="question-container">
        <h3 className="question-text">{question.question}</h3>
        
        <div className="options-container">
          {question.options.map((option, index) => (
            <label 
              key={index} 
              className={`option-label ${
                selectedAnswers[currentQuestion] === option ? 'selected' : ''
              }`}
            >
              <input
                type="radio"
                name={`question-${currentQuestion}`}
                value={option}
                checked={selectedAnswers[currentQuestion] === option}
                onChange={() => handleAnswerSelect(currentQuestion, option)}
                className="option-input"
              />
              <span className="option-text">{option}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="quiz-navigation">
        <button 
          onClick={handlePrevious} 
          disabled={currentQuestion === 0}
          className="nav-btn prev-btn"
        >
          ← Previous
        </button>
        
        <div className="question-indicators">
          {quiz.questions.map((_, index) => (
            <button
              key={index}
              className={`indicator ${
                index === currentQuestion ? 'current' : ''
              } ${
                selectedAnswers[index] ? 'answered' : ''
              }`}
              onClick={() => setCurrentQuestion(index)}
            >
              {index + 1}
            </button>
          ))}
        </div>

        <button 
          onClick={handleNext}
          className="nav-btn next-btn"
        >
          {currentQuestion === quiz.questions.length - 1 ? 'Finish' : 'Next →'}
        </button>
      </div>

      <div className="quiz-actions">
        <button onClick={onBackToSummary} className="back-btn">
          Back to Summary
        </button>
        <button onClick={onReset} className="reset-btn">
          New Document
        </button>
      </div>
    </div>
  );
};

export default QuizInterface;
