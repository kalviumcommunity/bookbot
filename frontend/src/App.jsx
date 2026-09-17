
import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

import FileUpload from './components/FileUpload';
import SummaryDisplay from './components/SummaryDisplay';
import QuizInterface from './components/QuizInterface';
import DocumentChat from './components/DocumentChat';
import ProtectedRoute from './components/ProtectedRoute';
import WelcomeTransition from './components/WelcomeTransition';
import LearningHistory from './pages/LearningHistory';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';

import { useAuth } from './context/AuthContext';
import apiService from './services/api';
import bookbotLogo from './assets/bookbot logo.png';

// ─── Main authenticated BookBot experience ────────────────────────────────────

function BookBotApp() {
  const { user, logout, showWelcome, isNewUser, clearWelcome } = useAuth();

  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [summary, setSummary] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [currentView, setCurrentView] = useState('upload');
  const [quizDifficulty, setQuizDifficulty] = useState('medium'); // tracks the difficulty used for the current quiz

  // Called after a file is successfully parsed by FileUpload
  const handleFileUpload = (file, content) => {
    if (!file) {
      console.error('No file received.');
      return;
    }

    if (!content || !content.trim()) {
      console.error('No readable content extracted from the file.');
      alert(
        'Could not extract readable text from this document. ' +
        'Please try a text-based PDF or another supported file.'
      );
      return;
    }

    setUploadedFile(file);
    setFileContent(content);
    setSummary(null);
    setQuiz(null);
    setCurrentView('summary');
  };

  // Called by SummaryDisplay after AI summary generation
  const handleSummaryGenerated = (summaryData) => {
    setSummary(summaryData);
  };

  // Generate a REAL AI quiz from the uploaded document
  const handleQuizGenerated = async (questionCount, difficulty = 'medium') => {
    try {
      if (!fileContent || !fileContent.trim()) {
        throw new Error(
          'No document content is available for quiz generation.'
        );
      }

      if (!questionCount || questionCount < 1) {
        throw new Error('Please select a valid number of questions.');
      }

      console.log(
        `Generating ${questionCount} questions (difficulty: ${difficulty})...`
      );

      // Call the actual backend instead of generating mock questions
      const quizData = await apiService.generateQuiz(
        fileContent,
        questionCount
      );

      // Validate backend response
      if (
        !quizData ||
        !Array.isArray(quizData.questions) ||
        quizData.questions.length === 0
      ) {
        throw new Error(
          'The AI did not return any valid quiz questions.'
        );
      }

      // Normalize question data before passing it to QuizInterface
      const normalizedQuestions = quizData.questions
        .map((question, index) => {
          if (!question) return null;

          const questionText = String(
            question.question || ''
          ).trim();

          const options = Array.isArray(question.options)
            ? question.options.map((option) =>
                String(option).trim()
              )
            : [];

          const answer = String(
            question.answer || ''
          ).trim();

          const explanation = String(
            question.explanation ||
              'This answer is supported by the document.'
          ).trim();

          // Every question needs exactly 4 options
          if (
            !questionText ||
            options.length !== 4 ||
            options.some((option) => !option) ||
            !answer ||
            !options.includes(answer)
          ) {
            console.warn(
              `Skipping invalid question at index ${index}:`,
              question
            );
            return null;
          }

          return {
            question: questionText,
            options,
            answer,
            explanation,
          };
        })
        .filter(Boolean);

      if (normalizedQuestions.length === 0) {
        throw new Error(
          'The AI returned quiz data, but none of the questions were valid.'
        );
      }

      setQuiz({
        questions: normalizedQuestions,
      });

      setQuizDifficulty(difficulty); // store for QuizInterface to save with attempt
      setCurrentView('quiz');
    } catch (error) {
      console.error('Quiz generation error:', error);

      alert(
        error?.message ||
          'Failed to generate the quiz. Please try again.'
      );
    }
  };

  const resetApp = () => {
    setUploadedFile(null);
    setFileContent('');
    setSummary(null);
    setQuiz(null);
    setQuizDifficulty('medium');
    setCurrentView('upload');
  };

  return (
    <div className="App">
      <header className="app-header">
        <img
          src={bookbotLogo}
          alt="BookBot Logo"
          className="bookbot-logo"
        />

        {/* User info + logout + learning history nav */}
        <div className="app-header-user">
          <span className="app-header-greeting">
            👋 {user?.name || 'User'}
          </span>
          <button
            onClick={() => setCurrentView('learning')}
            className="learning-nav-btn"
            title="My Learning History"
          >
            📈 My Learning
          </button>
          <button
            onClick={logout}
            className="logout-btn"
            title="Log out"
          >
            Log Out
          </button>
        </div>
      </header>

      <main className="app-main">
        {currentView === 'upload' && (
          <FileUpload
            onFileUpload={handleFileUpload}
          />
        )}

        {currentView === 'summary' && uploadedFile && (
          <SummaryDisplay
            file={uploadedFile}
            content={fileContent}
            onSummaryGenerated={handleSummaryGenerated}
            onGenerateQuiz={handleQuizGenerated}
            onStartChat={() => setCurrentView('chat')}
            onReset={resetApp}
          />
        )}

        {currentView === 'quiz' && quiz && (
          <QuizInterface
            quiz={quiz}
            bookName={uploadedFile?.name || 'Unknown Document'}
            difficulty={quizDifficulty}
            onBackToSummary={() => setCurrentView('summary')}
            onReset={resetApp}
          />
        )}

        {currentView === 'chat' && (
          <DocumentChat
            content={fileContent}
            onBack={() => setCurrentView('summary')}
          />
        )}

        {currentView === 'learning' && (
          <LearningHistory
            onBack={() => setCurrentView('upload')}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by AI • Built with React</p>
      </footer>

      {/* Full-screen welcome transition — only shown after live login/signup */}
      {showWelcome && (
        <WelcomeTransition
          userName={user?.name}
          isNewUser={isNewUser}
          onDone={clearWelcome}
        />
      )}
    </div>
  );
}

// ─── Root App with routing ────────────────────────────────────────────────────

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"  element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* Protected route — renders the full BookBot SPA */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <BookBotApp />
          </ProtectedRoute>
        }
      />

      {/* Catch-all: redirect unknown paths to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
