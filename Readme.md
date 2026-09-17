# 📚 BookBot AI - Document Analysis & Quiz Generator

A modern web application that uses AI to analyze documents and generate interactive quizzes. Upload PDFs, text files, images, or Word documents and get instant AI-powered summaries and customizable quizzes.

## ✨ Features

- **📄 Multi-format Support**: Upload PDF, TXT, DOCX, and image files
- **🤖 AI-Powered Summarization**: Get intelligent summaries with key points
- **📝 Custom Quiz Generation**: Generate quizzes with 5, 10, 20, or custom number of questions
- **🎯 Interactive Quiz Interface**: Take quizzes with real-time feedback and scoring
- **📈 Learning Progress Tracking**: Persistent quiz history with performance stats per user
- **🧠 Adaptive Difficulty Recommendation**: Deterministic difficulty suggestion based on average score
- **💬 Document Chat**: Ask questions about your uploaded document via AI
- **📱 Responsive Design**: Works perfectly on desktop and mobile devices
- **⚡ Fast Processing**: Quick file processing and AI analysis
- **🔐 Authentication**: Email/password accounts with JWT-based sessions

## 🏗️ Architecture

- **Frontend**: React with Vite (JavaScript)
- **Backend**: Python with FastAPI
- **AI Integration**: Google Gemini AI
- **File Processing**: PyPDF2, python-docx

## 👩‍💻 My Contribution / Ownership

I contributed to BookBot as part of the project development, focusing on the implementation of the application's AI-powered learning workflow and supporting the development of the frontend and backend components.

My contributions included:

* Implementing the **LLM Function Calling workflow** for generating interactive quizzes from processed book content.
* Contributing to the **React-based user interface** for navigating document summaries, topics, and quizzes.
* Supporting the **Python/FastAPI backend and RAG pipeline** for processing book content and retrieving relevant context for AI-generated responses.
* Contributing to the integration of the document-processing, summarization, and quiz-generation workflow.

The quantitative performance claims previously associated with this project have not been retained because reproducible measurement evidence was not available. The project README therefore focuses on implemented functionality rather than unsupported performance metrics.


## 🚀 Quick Start

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Google Gemini API key

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd bookbot
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run the API server
python run_api.py
```

The API will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📖 Usage

1. **Upload a Document**: Drag and drop or click to upload your file
2. **View Summary**: Get an AI-generated summary with key points
3. **Generate Quiz**: Choose the number of questions (5, 10, 20, or custom)
4. **Take Quiz**: Answer questions and get instant feedback
5. **View Results**: See your score and detailed explanations

## 🛠️ API Endpoints

- `POST /upload` - Upload and process a file
- `POST /summarize` - Generate summary from content
- `POST /quiz` - Generate quiz from content
- `POST /process` - Process file and return content + summary

## 🎨 Components

- **FileUpload**: Drag-and-drop file upload with progress indicators
- **SummaryDisplay**: AI-generated summaries with key points
- **QuizInterface**: Interactive quiz with timer and scoring
- **QuizGenerator**: Customizable quiz generation options

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### API Configuration

Update the API base URL in `frontend/src/services/api.js` if needed:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Various screen sizes

## 🚀 Deployment

### Backend Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run: `python run_api.py`

### Frontend Deployment

1. Build: `npm run build`
2. Serve the `dist` folder with any static file server

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:

1. Check the console for error messages
2. Ensure all dependencies are installed
3. Verify your API key is correct
4. Check that both frontend and backend are running

## 🔮 Future Enhancements

- [ ] User authentication and accounts
- [ ] Save and share quizzes
- [ ] More file format support
- [ ] Advanced AI features
- [ ] Quiz analytics and progress tracking
- [ ] Collaborative features

---

## 📈 Learning Progress & Adaptive Quiz Difficulty

### Problem

BookBot allowed users to generate and take quizzes, but quiz attempts were ephemeral — no history, no feedback loop, no way to measure improvement over time.

### Solution

This feature adds a persistent learning layer on top of the existing quiz flow:

1. **Persistent quiz attempts** — every completed quiz is saved to the database under the authenticated user's account.
2. **My Learning page** — users can view their full quiz history with scores, book names, difficulty, and dates.
3. **Performance statistics** — aggregate stats: average score, quizzes attempted, unique books studied.
4. **Adaptive difficulty recommendation** — the next quiz difficulty is suggested based on the user's average score.

### Design Decisions

#### Why deterministic rules instead of asking the AI for difficulty?

The difficulty recommendation is calculated by a pure Python function in `backend/difficulty.py`:

| Average Score | Recommendation |
|---|---|
| No history | Medium |
| < 50% | Easy |
| 50–74% | Medium |
| ≥ 75% | Hard |

This approach was chosen because:
- **Predictable**: same average always gives the same recommendation
- **Testable**: pure function with no I/O, all boundary cases easily verified
- **Transparent**: users can understand why they got a recommendation
- **Inexpensive**: no Gemini API call required for a recommendation
- **Reliable**: recommendation is always available, even if Gemini is slow

#### Why is `percentage` calculated server-side?

The `POST /quiz/attempt` endpoint calculates `percentage = score / total_questions * 100` on the backend — it does not trust the value from the client. This prevents a user from submitting an artificially high percentage.

#### Why is `user_id` never in the request body?

The `user_id` is always extracted from the JWT token via `get_current_user()`. This ensures a user can never save an attempt attributed to another user's account.

### API Endpoints

All three endpoints require a valid `Authorization: Bearer <token>` header.

| Method | Path | Description |
|---|---|---|
| `POST` | `/quiz/attempt` | Save a completed quiz attempt |
| `GET` | `/quiz/history` | Return user's attempts, newest first |
| `GET` | `/quiz/performance` | Return stats + difficulty recommendation |

### Running Tests

```bash
cd backend
python test_learning.py
```

Covers: difficulty boundary cases (11 tests), validation rules (9 tests), API integration — auth guards, save, ordering, user isolation, performance (13 tests). **33 tests total.**

### Future Improvements

- Streaks and badges for consecutive quiz days
- Per-book progress breakdown
- Export quiz history as CSV
- ML-based difficulty recommendation once sufficient data is collected
- Weekly summary emails via SendGrid/similar

---

**Built with ❤️ using React, FastAPI, and Google Gemini AI**
