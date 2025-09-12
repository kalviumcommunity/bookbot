import React, { useState, useEffect } from 'react';
import './SummaryDisplay.css';
import apiService from '../services/api';

// Helper functions for generating detailed summaries
const generateDetailedSummary = (content, fileName, contentType, wordCount) => {
  // Build a friendly overview paragraph directly from the pasted text
  const sentences = String(content).replace(/\s+/g, ' ').trim().split(/(?<=[.!?])\s+/).filter(Boolean);
  const first = sentences.slice(0, 2).join(' ');

  const overviewLead = first || 'This text introduces a topic and develops it with supporting ideas.';

  // Light keyword extraction (non-technical) to describe the topic
  const words = String(content).toLowerCase().match(/[a-zA-Z][a-zA-Z\-']+/g) || [];
  const stop = new Set(['the','and','or','of','to','a','in','for','on','is','are','that','with','as','by','an','be','this','it','from','at','was','were','can','will','your','you']);
  const counts = new Map();
  for (const w of words) {
    if (w.length < 3 || stop.has(w)) continue;
    counts.set(w, (counts.get(w) || 0) + 1);
  }
  const keywords = Array.from(counts.entries()).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([w])=>w);
  const topicHint = keywords.length ? `The core theme centers around ${keywords.slice(0,3).join(', ')}${keywords.length>3 ? ' and related ideas' : ''}.` : '';

  return `${overviewLead} ${topicHint} The following explanation turns the ideas into simple language so the topic is easy to grasp.`;
};

// Generate narrative paragraphs to make topic understandable (no bullet specs)
const generateUnderstandingNarrative = (content, wordCount) => {
  const cleaned = String(content).replace(/\s+/g, ' ').trim();
  const sentences = cleaned.split(/(?<=[.!?])\s+/).filter(Boolean);

  const paragraphs = [];
  // Intro paragraph: what the topic is and why it matters
  const intro = sentences.length
    ? `In simple terms, the text explains: ${sentences[0].replace(/\s+/g,' ').trim()} It shows what the idea means and why it matters in everyday thinking.`
    : `In simple terms, the text introduces a main idea, explains what it means, and shows why it matters.`;
  paragraphs.push(intro);

  // Middle paragraph: how it works / core concepts in narrative
  const midSentences = sentences.slice(1, 4).join(' ');
  const middle = midSentences
    ? `How it works: the author develops the idea step by step — ${midSentences}. Read it as a small story: definition first, then the most important parts, then how they connect.`
    : `How it works: read it as a small story — definition first, then the most important parts, then how they connect.`;
  paragraphs.push(middle);

  // Example/explanation paragraph: bring it to life
  const tail = sentences.slice(4, 8).join(' ');
  const example = tail
    ? `To make it practical, connect the idea to familiar situations. For example: ${tail} This makes cause and effect clear and shows how to apply the idea.`
    : `To make it practical, connect the idea to familiar situations. This makes cause and effect clear and shows how to apply the idea.`;
  paragraphs.push(example);

  // Optional advanced/next steps if content is longer
  if (wordCount > 350) {
    const advanced = `If you want to go deeper, focus on patterns and relationships: what changes the outcome, which assumptions matter most, and how small adjustments can lead to better results. This creates a mental model you can reuse across different problems.`;
    paragraphs.push(advanced);
  }

  return paragraphs;
};

// Create topic-focused highlights (non-technical, learner-focused)
const generateTopicHighlights = (content) => {
  const text = String(content).replace(/\s+/g, ' ').trim();
  const sentences = text.split(/(?<=[.!?])\s+/).filter(Boolean);

  const highlights = [];
  if (sentences[0]) {
    highlights.push(`Main idea: ${sentences[0]}`);
  }
  if (sentences[1]) {
    highlights.push(`Why it matters: ${sentences[1]}`);
  }

  // Pull a few characteristic phrases to suggest subtopics
  const words = text.toLowerCase().match(/[a-zA-Z][a-zA-Z\-']+/g) || [];
  const stop = new Set(['the','and','or','of','to','a','in','for','on','is','are','that','with','as','by','an','be','this','it','from','at','was','were','can','will','your','you','their','them','they','these','those','but','not','into','about','over','under']);
  const counts = new Map();
  for (const w of words) {
    if (w.length < 4 || stop.has(w)) continue;
    counts.set(w, (counts.get(w) || 0) + 1);
  }
  const keywords = Array.from(counts.entries()).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([w])=>w);
  if (keywords.length) {
    highlights.push(`Focus terms: ${keywords.slice(0,3).join(', ')}${keywords[3] ? `, ${keywords[3]}` : ''}`);
  }

  if (sentences[2]) {
    highlights.push(`How it works: ${sentences[2]}`);
  }
  if (sentences[3]) {
    highlights.push(`Practical angle: ${sentences[3]}`);
  }

  return highlights.slice(0, 5);
};

const SummaryDisplay = ({ file, content, onSummaryGenerated, onGenerateQuiz, onReset }) => {
  const [summary, setSummary] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (content && !summary) {
      generateSummary();
    }
  }, [content, summary]);

  const generateSummary = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate detailed, contextual summary based on content
      const wordCount = content.split(/\s+/).length;
      const charCount = content.length;
      const isLongContent = wordCount > 500;
      const isShortContent = wordCount < 100;
      
      // Determine content type and difficulty
      let contentType = 'document';
      let difficulty = 'intermediate';
      
      if (file.type.includes('image')) {
        contentType = 'image';
        difficulty = 'beginner';
      } else if (file.type.includes('pdf')) {
        contentType = 'PDF document';
        difficulty = isLongContent ? 'advanced' : 'intermediate';
      } else if (file.type.includes('text')) {
        contentType = 'text document';
        difficulty = isShortContent ? 'beginner' : 'intermediate';
      }

      const summaryData = {
        title: file.name,
        type: file.type,
        summary: generateDetailedSummary(content, file.name, contentType, wordCount),
        understanding: generateUnderstandingNarrative(content, wordCount),
        highlights: generateTopicHighlights(content),
        difficulty: difficulty,
        word_count: wordCount,
        char_count: charCount,
        processing_time: '2.3 seconds',
        // internal analysis removed from UI to avoid specs
      };
      
      setSummary(summaryData);
      onSummaryGenerated(summaryData);
    } catch (err) {
      setError('Failed to generate summary. Please try again.');
      console.error('Summary generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateQuiz = (questionCount) => {
    onGenerateQuiz(questionCount);
  };

  if (isGenerating) {
    return (
      <div className="summary-container">
        <div className="generating-state">
          <div className="spinner"></div>
          <h3>🤖 AI is analyzing your document...</h3>
          <p>This may take a few moments depending on file size</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="summary-container">
        <div className="error-state">
          <h3>❌ Error</h3>
          <p>{error}</p>
          <button onClick={generateSummary} className="retry-btn">
            Try Again
          </button>
          <button onClick={onReset} className="reset-btn">
            Upload New File
          </button>
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="summary-container">
      <div className="summary-header">
        <h2>📖 Document Summary</h2>
        <div className="file-info">
          {/* <span className="file-name">{summary.title}</span> */}
          {/* <span className="file-type">{summary.type}</span> */}
        </div>
      </div>

      <div className="summary-content">
        <div className="summary-section">
          <h3>📝 Summary</h3>
          <p className="summary-text">{summary.summary}</p>
        </div>

        {/* <div className="understanding-section">
          <h3>🧠 Understanding the Topic</h3>
          {(summary.understanding || []).map((para, index) => (
            <p key={index} className="understanding-paragraph">{para}</p>
          ))}
        </div> */}

        {(summary.highlights && summary.highlights.length > 0) && (
          <div className="highlights-section">
            <h3>✨ Topic Highlights</h3>
            <ul className="highlights-list stagger-list">
              {summary.highlights.map((h, idx) => (
                <li key={idx} className="highlight-item">{h}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Technical stats removed to keep the output non-spec and learner-focused */}
      </div>

      <div className="summary-actions">
        <h3>🎯 Ready for a Quiz?</h3>
        <p>Test your understanding with an AI-generated quiz</p>
        
        <div className="quiz-options">
          <button 
            className="quiz-btn"
            onClick={() => handleGenerateQuiz(5)}
          >
            📝 Quick Quiz (5 questions)
          </button>
          <button 
            className="quiz-btn"
            onClick={() => handleGenerateQuiz(10)}
          >
            📚 Standard Quiz (10 questions)
          </button>
          <button 
            className="quiz-btn"
            onClick={() => handleGenerateQuiz(20)}
          >
            🧠 Comprehensive Quiz (20 questions)
          </button>
          <button 
            className="quiz-btn custom"
            onClick={() => {
              const count = prompt('Enter number of questions (1-50):', '15');
              if (count && !isNaN(count) && count > 0 && count <= 50) {
                handleGenerateQuiz(parseInt(count));
              }
            }}
          >
            ⚙️ Custom Quiz
          </button>
        </div>

        <button onClick={onReset} className="reset-btn">
          📄 Upload Another File
        </button>
      </div>
    </div>
  );
};

export default SummaryDisplay;
