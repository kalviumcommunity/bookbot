
// frontend/src/services/api.js

// Use VITE_API_URL when deployed.
// Falls back to localhost for local development.
const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL.replace(/\/$/, '');
  }

  /**
   * Generic helper for API requests.
   * Handles JSON parsing and useful backend error messages.
   */
  async request(endpoint, options = {}) {
    try {
      const response = await fetch(
        `${this.baseURL}${endpoint}`,
        options
      );

      // Try to parse JSON regardless of status code.
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMessage =
          data?.detail ||
          data?.message ||
          data?.error ||
          `Request failed with status ${response.status}`;

        throw new Error(errorMessage);
      }

      return data;
    } catch (error) {
      // Network/server unavailable
      if (error instanceof TypeError) {
        throw new Error(
          `Could not connect to BookBot backend at ${this.baseURL}. ` +
          `Make sure the backend server is running.`
        );
      }

      throw error;
    }
  }

  /**
   * Upload a document to the backend.
   */
  async uploadFile(file) {
    if (!file) {
      throw new Error('No file selected.');
    }

    const formData = new FormData();
    formData.append('file', file);

    console.log('Uploading file:', file.name);

    return await this.request('/upload', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Generate an AI summary from the actual document content.
   */
  async generateSummary(content, title = 'Document') {
    if (!content || !content.trim()) {
      throw new Error(
        'No document content is available for summarization.'
      );
    }

    console.log(
      `Sending ${content.length} characters to summary API...`
    );

    return await this.request('/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: content.trim(),
        title: title || 'Document',
      }),
    });
  }

  /**
   * Generate an AI quiz based ONLY on the uploaded document.
   */
  async generateQuiz(content, questionCount = 10) {
    if (!content || !content.trim()) {
      throw new Error(
        'No document content is available for quiz generation.'
      );
    }

    const count = Number(questionCount);

    if (!Number.isInteger(count) || count < 1 || count > 50) {
      throw new Error(
        'Question count must be between 1 and 50.'
      );
    }

    console.log(
      `Sending ${content.length} characters to quiz API for ${count} questions...`
    );

    const data = await this.request('/quiz', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: content.trim(),
        question_count: count,
      }),
    });

    // Validate the response before giving it to App.jsx
    if (
      !data ||
      !Array.isArray(data.questions) ||
      data.questions.length === 0
    ) {
      throw new Error(
        'The backend returned no quiz questions.'
      );
    }

    return data;
  }

  /**
   * Process a document.
   * Kept for compatibility with the existing project.
   */
  async processFile(file) {
    if (!file) {
      throw new Error('No file selected.');
    }

    const formData = new FormData();
    formData.append('file', file);

    return await this.request('/process', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Send a question to the document chat.
   */
  async sendChatMessage(content, message, history = []) {
    if (!content || !content.trim()) {
      throw new Error(
        'No document content is available for chat.'
      );
    }

    if (!message || !message.trim()) {
      throw new Error('Please enter a message.');
    }

    return await this.request('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: content.trim(),
        message: message.trim(),
        history: Array.isArray(history) ? history : [],
      }),
    });
  }
}

// Create one shared API service instance.
const apiService = new ApiService();

export default apiService;

