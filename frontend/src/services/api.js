// API service for connecting to the Python backend
const API_BASE_URL = 'http://localhost:8000'; // Adjust this to match your backend URL

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async uploadFile(file, content) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('content', content);

      const response = await fetch(`${this.baseURL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  }

  async generateSummary(content, title = 'Document') {
    try {
      const response = await fetch(`${this.baseURL}/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content,
          title: title
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating summary:', error);
      throw error;
    }
  }

  async generateQuiz(content, questionCount = 10) {
    try {
      const response = await fetch(`${this.baseURL}/quiz`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content,
          question_count: questionCount
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating quiz:', error);
      throw error;
    }
  }

  async processFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseURL}/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error processing file:', error);
      throw error;
    }
  }
}

// Create a singleton instance
const apiService = new ApiService();

export default apiService;
