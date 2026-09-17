
// frontend/src/services/api.js
//
// Singleton ApiService that handles all communication with the BookBot backend.
// All authenticated requests automatically attach the stored JWT as a Bearer token.

const TOKEN_KEY = 'bookbot_token';

// Use VITE_API_URL when deployed. Falls back to localhost for local development.
const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL.replace(/\/$/, '');
  }

  // ─── Token helpers ─────────────────────────────────────────────────────────

  _getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  _authHeaders() {
    const token = this._getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // ─── Generic request helper ────────────────────────────────────────────────

  /**
   * Make an HTTP request.
   * Automatically attaches Authorization header if a token exists.
   * Reads backend `detail` / `message` / `error` for error messages.
   */
  async request(endpoint, options = {}) {
    try {
      // Merge auth headers into every request
      const headers = {
        ...(options.headers || {}),
        ...this._authHeaders(),
      };

      const response = await fetch(
        `${this.baseURL}${endpoint}`,
        { ...options, headers }
      );

      // Try to parse JSON regardless of status code.
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        // Handle 401 specifically — token expired or invalid
        if (response.status === 401) {
          // Clear stale token so the user gets redirected to /login
          localStorage.removeItem(TOKEN_KEY);
          throw new Error(
            data?.detail ||
            'Your session has expired. Please log in again.'
          );
        }

        const errorMessage =
          data?.detail ||
          data?.message ||
          data?.error ||
          `Request failed with status ${response.status}`;

        throw new Error(errorMessage);
      }

      return data;
    } catch (error) {
      // Network / server unavailable
      if (error instanceof TypeError) {
        throw new Error(
          `Could not connect to BookBot backend at ${this.baseURL}. ` +
          `Make sure the backend server is running.`
        );
      }

      throw error;
    }
  }

  // ─── Auth API ──────────────────────────────────────────────────────────────

  /**
   * Register a new user.
   * Returns { access_token, token_type }.
   */
  async signup(name, email, password) {
    return await this.request('/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
  }

  /**
   * Log in with email + password.
   * Returns { access_token, token_type }.
   */
  async login(email, password) {
    return await this.request('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  }

  /**
   * Fetch the currently authenticated user.
   * Returns { id, name, email }.
   */
  async getCurrentUser() {
    return await this.request('/auth/me');
  }

  // ─── Document API ──────────────────────────────────────────────────────────

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
      headers: { 'Content-Type': 'application/json' },
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
      headers: { 'Content-Type': 'application/json' },
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: content.trim(),
        message: message.trim(),
        history: Array.isArray(history) ? history : [],
      }),
    });
  }

  // ─── Learning Progress API ──────────────────────────────────────────────────

  /**
   * Save a completed quiz attempt.
   * percentage is calculated server-side — not sent from the client.
   * user_id comes from the JWT on the backend — never from this call.
   */
  async saveQuizAttempt(bookName, score, totalQuestions, difficulty) {
    return await this.request('/quiz/attempt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        book_name: String(bookName || 'Unknown Document').trim().slice(0, 500),
        score: Number(score),
        total_questions: Number(totalQuestions),
        difficulty: String(difficulty || 'medium').toLowerCase(),
      }),
    });
  }

  /**
   * Fetch the authenticated user's quiz history (newest first).
   * Returns an array of attempt objects.
   */
  async getQuizHistory() {
    return await this.request('/quiz/history');
  }

  /**
   * Fetch aggregate performance stats and difficulty recommendation.
   * Returns { average_score, quizzes_attempted, books_studied, recommended_difficulty }.
   */
  async getPerformance() {
    return await this.request('/quiz/performance');
  }
}


// Create one shared API service instance.
const apiService = new ApiService();

export default apiService;
