# 📚 BookBot AI - Document Analysis & Quiz Generator

A modern web application that uses AI to analyze documents and generate interactive quizzes. Upload PDFs, text files, images, or Word documents and get instant AI-powered summaries and customizable quizzes.

## ✨ Features

- **📄 Multi-format Support**: Upload PDF, TXT, DOCX, and image files
- **🤖 AI-Powered Summarization**: Get intelligent summaries with key points
- **📝 Custom Quiz Generation**: Generate quizzes with 5, 10, 20, or custom number of questions
- **🎯 Interactive Quiz Interface**: Take quizzes with real-time feedback and scoring
- **📱 Responsive Design**: Works perfectly on desktop and mobile devices
- **⚡ Fast Processing**: Quick file processing and AI analysis

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

**Built with ❤️ using React, FastAPI, and Google Gemini AI**
