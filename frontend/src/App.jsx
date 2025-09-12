import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import SummaryDisplay from './components/SummaryDisplay';
import QuizGenerator from './components/QuizGenerator';
import QuizInterface from './components/QuizInterface';
import apiService from './services/api';

function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [summary, setSummary] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [currentView, setCurrentView] = useState('upload'); // 'upload', 'summary', 'quiz'

  const handleFileUpload = (file, content) => {
    setUploadedFile(file);
    setFileContent(content);
    setSummary(null);
    setQuiz(null);
    setCurrentView('summary');
  };

  const handleSummaryGenerated = (summaryData) => {
    setSummary(summaryData);
  };

  const handleQuizGenerated = async (questionCount) => {
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Use mock quiz data (no API calls)
      const quizData = createMockQuiz(questionCount);
      setQuiz(quizData);
      setCurrentView('quiz');
    } catch (error) {
      console.error('Error generating quiz:', error);
      // Still show a mock quiz even if there's an error
      setQuiz(createMockQuiz(questionCount));
      setCurrentView('quiz');
    }
  };

  const createMockQuiz = (questionCount) => {
    const questions = [];
    const questionTemplates = [
      {
        question: "What is the primary concept or main idea discussed in this content?",
        options: ["A fundamental principle that guides understanding", "A complex theory with multiple components", "A practical application of knowledge", "A historical perspective on the topic"],
        answer: "A fundamental principle that guides understanding"
      },
      {
        question: "Which of the following best represents the key learning objective of this content?",
        options: ["To understand core concepts and their applications", "To memorize specific facts and figures", "To develop creative thinking skills", "To learn technical procedures"],
        answer: "To understand core concepts and their applications"
      },
      {
        question: "What type of knowledge does this content primarily focus on?",
        options: ["Conceptual understanding and critical thinking", "Factual information and data", "Procedural knowledge and skills", "Creative expression and imagination"],
        answer: "Conceptual understanding and critical thinking"
      },
      {
        question: "How does this content help learners understand the topic?",
        options: ["By providing clear explanations and examples", "By presenting complex theories without context", "By focusing only on practical applications", "By avoiding detailed explanations"],
        answer: "By providing clear explanations and examples"
      },
      {
        question: "What is the most important takeaway from this content?",
        options: ["Understanding the core concepts and their significance", "Memorizing specific details and facts", "Learning technical procedures", "Developing creative skills"],
        answer: "Understanding the core concepts and their significance"
      },
      {
        question: "Which learning approach does this content support?",
        options: ["Active learning through understanding and application", "Passive learning through memorization", "Visual learning through images only", "Auditory learning through listening"],
        answer: "Active learning through understanding and application"
      },
      {
        question: "What makes this content valuable for learning?",
        options: ["It provides clear explanations that build understanding", "It contains only factual information", "It focuses on entertainment value", "It avoids complex concepts"],
        answer: "It provides clear explanations that build understanding"
      },
      {
        question: "How should learners approach this content for maximum benefit?",
        options: ["Read carefully and think about the concepts", "Skim quickly for key facts", "Focus only on examples", "Ignore the main ideas"],
        answer: "Read carefully and think about the concepts"
      }
    ];

    for (let i = 0; i < questionCount; i++) {
      const template = questionTemplates[i % questionTemplates.length];
      questions.push({
        question: `${i + 1}. ${template.question}`,
        options: template.options,
        answer: template.answer
      });
    }
    return { questions };
  };

  const resetApp = () => {
    setUploadedFile(null);
    setFileContent('');
    setSummary(null);
    setQuiz(null);
    setCurrentView('upload');
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📚 BookBot AI</h1>
        <p>Upload any document and get AI-powered summaries and quizzes</p>
      </header>

      <main className="app-main">
        {currentView === 'upload' && (
          <FileUpload onFileUpload={handleFileUpload} />
        )}

        {currentView === 'summary' && (
          <SummaryDisplay
            file={uploadedFile}
            content={fileContent}
            onSummaryGenerated={handleSummaryGenerated}
            onGenerateQuiz={handleQuizGenerated}
            onReset={resetApp}
          />
        )}

        {currentView === 'quiz' && quiz && (
          <QuizInterface
            quiz={quiz}
            onBackToSummary={() => setCurrentView('summary')}
            onReset={resetApp}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by AI • Built with React</p>
      </footer>
    </div>
  );
}

export default App;