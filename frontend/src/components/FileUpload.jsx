import React, { useState, useCallback } from 'react';
import './FileUpload.css';

const FileUpload = ({ onFileUpload }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [inputMode, setInputMode] = useState('file'); // 'file' or 'text'

  const handleFile = useCallback(async (file) => {
    if (!file) return;

    setIsProcessing(true);
    
    try {
      let content = '';
      const fileType = file.type;
      const fileName = file.name;

      if (fileType === 'text') {
        content = await readTextFile(file);
      } else if (fileType === 'application/pdf') {
        content = await readPDFFile(file);
      } else if (fileType.startsWith('image/')) {
        content = await readImageFile(file);
      } else if (fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        content = await readDocxFile(file);
      } else {
        throw new Error('Unsupported file type. Please upload PDF, TXT, DOCX, or image files.');
      }

      onFileUpload(file, content);
    } catch (error) {
      alert(`Error processing file: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  }, [onFileUpload]);

  const readTextFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error('Failed to read text file'));
      reader.readAsText(file);
    });
  };

  const readPDFFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        // For now, we'll send the file to backend for PDF processing
        // In a real implementation, you'd use a PDF parsing library
        resolve('PDF content will be processed by backend...');
      };
      reader.onerror = () => reject(new Error('Failed to read PDF file'));
      reader.readAsArrayBuffer(file);
    });
  };

  const readImageFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        // For images, we'll send the base64 data to backend for OCR processing
        resolve(`Image: ${file.name} (${file.size} bytes)`);
      };
      reader.onerror = () => reject(new Error('Failed to read image file'));
      reader.readAsDataURL(file);
    });
  };

  const readDocxFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        // For DOCX files, we'll send to backend for processing
        resolve('DOCX content will be processed by backend...');
      };
      reader.onerror = () => reject(new Error('Failed to read DOCX file'));
      reader.readAsArrayBuffer(file);
    });
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleTextSubmit = async () => {
    if (!textInput.trim()) {
      alert('Please enter some text to analyze');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Create a mock file object for text input
      const mockFile = {
        name: 'Text Input',
        type: 'text',
        size: textInput.length
      };

      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onFileUpload(mockFile, textInput.trim());
    } catch (error) {
      alert(`Error processing text: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleModeChange = (mode) => {
    setInputMode(mode);
    setTextInput('');
  };

  return (
    <div className="file-upload-container">
      <div className="upload-header">
        <h2>Upload Your Document</h2>
        <p>Upload files or paste text directly to get started</p>
      </div>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button 
          className={`mode-btn ${inputMode === 'file' ? 'active' : ''}`}
          onClick={() => handleModeChange('file')}
        >
          Upload File
        </button>
        <button 
          className={`mode-btn ${inputMode === 'text' ? 'active' : ''}`}
          onClick={() => handleModeChange('text')}
        >
          Paste Text
        </button>
      </div>

      {inputMode === 'file' ? (
        <div
          className={`upload-zone ${isDragOver ? 'drag-over' : ''} ${isProcessing ? 'processing' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isProcessing ? (
            <div className="processing-content">
              <div className="spinner"></div>
              <p>Processing your file...</p>
            </div>
          ) : (
            <div className="upload-content">
              <div className="upload-icon">📁</div>
              <p className="upload-text">
                Drag and drop your file here, or{' '}
                <label className="file-input-label">
                  click to browse
                  <input
                    type="file"
                    accept=".pdf,.txt,.docx,.doc,image/*"
                    onChange={handleFileInput}
                    className="file-input"
                  />
                </label>
              </p>
              <p className="upload-hint">
                Supports: PDF, TXT, DOCX, and image files
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-input-zone">
          <div className="text-input-header">
            <h3>📝 Paste Your Text</h3>
            <p>Enter or paste your text content below for AI analysis</p>
          </div>
          <textarea
            className="text-input"
            placeholder="Paste your text here... (articles, essays, notes, etc.)"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            rows={8}
            disabled={isProcessing}
          />
          <div className="text-input-footer">
            <div className="char-count">
              {textInput.length} characters
            </div>
            <button 
              className="submit-text-btn"
              onClick={handleTextSubmit}
              disabled={isProcessing || !textInput.trim()}
            >
              {isProcessing ? (
                <>
                  <div className="spinner small"></div>
                  Processing...
                </>
              ) : (
                '🚀 Analyze Text'
              )}
            </button>
          </div>
        </div>
      )}

      <div className="upload-features">
        <div className="feature">
          <span className="feature-icon">🤖</span>
          <span>AI-Powered Summarization</span>
        </div>
        <div className="feature">
          <span className="feature-icon">📝</span>
          <span>Generate Custom Quizzes</span>
        </div>
        <div className="feature">
          <span className="feature-icon">⚡</span>
          <span>Fast Processing</span>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
