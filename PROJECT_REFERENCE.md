# 📚 BookBot AI — Comprehensive Project Reference

> **Purpose of this document**: A deep-dive technical reference for developers (and AI agents) working on this codebase. Read this before making any changes so you understand what exists, how it connects, and why it was built the way it was.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Tech Stack](#3-tech-stack)
4. [Backend — Deep Dive](#4-backend--deep-dive)
5. [Frontend — Deep Dive](#5-frontend--deep-dive)
6. [Data Flow Diagrams](#6-data-flow-diagrams)
7. [API Reference](#7-api-reference)
8. [Gemini AI Integration](#8-gemini-ai-integration)
9. [View State Machine](#9-view-state-machine)
10. [Known Patterns & Conventions](#10-known-patterns--conventions)
11. [Environment Variables](#11-environment-variables)
12. [Running the Project Locally](#12-running-the-project-locally)
13. [Gotchas & Important Notes](#13-gotchas--important-notes)
14. [Future Roadmap](#14-future-roadmap)

---

## 1. Project Overview

**BookBot AI** is a full-stack web application that acts as an AI-powered study assistant. A user uploads a document (PDF, TXT, or DOCX) or pastes raw text, and BookBot:

1. Extracts the raw text from the document.
2. Sends the text to **Google Gemini** (`gemini-3.6-flash`) to generate a structured summary with key points and a difficulty rating.
3. Lets the user generate a **multiple-choice quiz** (5, 10, 20, or custom number of questions) derived exclusively from the document's actual content.
4. Provides a **live chat interface** where the user can ask the AI tutor questions about the uploaded document.

The app deliberately does **not** use generic AI knowledge — every summary, quiz question, and chat answer must be grounded in the uploaded document's content.

---

## 2. Repository Structure

```
bookbot/
├── backend/                   # Python FastAPI backend
│   ├── main.py                # Core AI logic (parsing, summarization, quiz, chat)
│   ├── api.py                 # FastAPI REST API routes
│   ├── run_api.py             # Convenience script to start the API server
│   ├── test_chat.py           # Manual chat test script
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Secret keys (NOT committed to git)
│   └── .gitignore
│
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx            # Root component + global view state machine
│   │   ├── App.css            # Global styles + design system tokens
│   │   ├── index.css          # CSS reset / base styles
│   │   ├── main.jsx           # React DOM entry point
│   │   ├── assets/
│   │   │   └── bookbot logo.png
│   │   ├── components/
│   │   │   ├── FileUpload.jsx       # Upload zone + text paste mode
│   │   │   ├── FileUpload.css
│   │   │   ├── SummaryDisplay.jsx   # AI summary + quiz launcher
│   │   │   ├── SummaryDisplay.css
│   │   │   ├── QuizInterface.jsx    # Interactive quiz player
│   │   │   ├── QuizInterface.css
│   │   │   ├── DocumentChat.jsx     # Live chat with the document
│   │   │   └── DocumentChat.css
│   │   └── services/
│   │       └── api.js               # Singleton ApiService class
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── .env                   # Frontend env vars (VITE_API_URL)
│   └── .gitignore
│
├── Readme.md                  # Quick-start README
└── PROJECT_REFERENCE.md       # This file — comprehensive reference
```

---

## 3. Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Frontend Framework | React | ^19.1.1 | Function components + hooks only |
| Frontend Build Tool | Vite | ^7.1.2 | Dev server on `localhost:5173` |
| Backend Framework | FastAPI | 0.104.1 | Async Python web framework |
| Backend Server | Uvicorn | 0.24.0 | ASGI server, `reload=True` in dev |
| AI Provider | Google Gemini | `gemini-3.6-flash` | Via `google-generativeai >= 0.8.5` |
| PDF Parsing | PyPDF2 | 3.0.1 | Text-layer PDFs only (not scanned) |
| DOCX Parsing | python-docx | 1.1.0 | `python-docx` package |
| Form Multipart | python-multipart | latest | Required by FastAPI for file uploads |
| Environment Secrets | python-dotenv | 1.0.0 | Loads `backend/.env` |
| CSS | Vanilla CSS | — | No Tailwind, no CSS-in-JS |
| Fonts | Google Fonts (Coiny) | — | Loaded in `App.css` |
| State Management | React useState | — | No Redux/Zustand; state in `App.jsx` |

---

## 4. Backend — Deep Dive

### 4.1 Entry Points

| Script | Command | Purpose |
|---|---|---|
| `run_api.py` | `python run_api.py` | **Primary way to start the server.** Uvicorn on port 8000 with `reload=True`. |
| `api.py` | `python api.py` | Alternative direct entry (same config). |
| `main.py` | `python main.py` | CLI chatbot mode — interactive terminal. Not used by the web app. |

### 4.2 Environment Setup

The backend requires `backend/.env`:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

`main.py` loads this at module import time. If the key is missing, a `RuntimeError` is raised immediately — the server fails fast with a clear message.

### 4.3 Core Logic — `main.py`

`main.py` is the **brain** of BookBot. It has no FastAPI knowledge — purely functional Python. `api.py` imports from it.

#### Helper Functions

| Function | Signature | Purpose |
|---|---|---|
| `_strip_code_fences(text)` | `str → str` | Removes ` ```json ... ``` ` fences Gemini sometimes adds around its JSON output. |
| `_coerce_json(text)` | `str → dict` | Robust JSON parser. Tries `json.loads()` then falls back to a bracket-stack scan to find the first complete `{...}` or `[...]` block. Returns `{"error": ..., "raw": ...}` on failure. |

#### File Parsing — `parse_file(file_path)`

Supports three formats:
- **`.txt`** — reads with UTF-8 encoding.
- **`.pdf`** — uses `PyPDF2.PdfReader`, iterates pages, joins non-empty page text with `\n\n`. **Only works on text-layer PDFs, not scanned/image-based ones.**
- **`.docx`** — uses `python-docx`, reads all non-empty paragraphs, joins with `\n\n`.

Raises `FileNotFoundError` or `ValueError` for unsupported formats.

#### Text Validation — `validate_document_text(content)`

Ensures content is not `None`, not empty, and has **at least 50 characters**. Prevents sending garbage content to the AI. Called before every Gemini call.

#### Summary Generation — `generate_structured_summary(content, title)`

- Truncates document to **30,000 characters** (token safety).
- Requires Gemini to return this exact JSON:
  ```json
  {
    "title": "...",
    "summary": "detailed, student-friendly summary",
    "key_points": ["point1", "point2", "point3", "point4", "point5"],
    "difficulty": "beginner|intermediate|advanced"
  }
  ```
- Gemini config: `temperature=0.2`, `top_p=0.9`, `max_output_tokens=2500`, `response_mime_type="application/json"`.
- Validates that `summary` field is present; raises `ValueError` otherwise.

#### Quiz Generation — `generate_quiz_from_text(text, num_q)`

- Accepts `num_q` 1–50 (auto-clamped).
- Truncates document to **30,000 characters**.
- Gemini config: `temperature=0.3`, `top_p=0.9`, `max_output_tokens=5000`.
- Required JSON structure:
  ```json
  {
    "questions": [
      {
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "answer": "exact text of correct option",
        "explanation": "..."
      }
    ]
  }
  ```
- **Python-side validation** after Gemini responds:
  - Non-empty question text required.
  - Exactly 4 non-empty options required.
  - `answer` must exactly match one of the option strings.
  - Invalid questions are silently dropped.
  - Zero surviving questions → raises `ValueError`.

#### Book-Based Quiz — `generate_quiz_from_book()` (Disabled)

Always raises `ValueError`. Intentionally disabled — quizzes must be grounded in uploaded content.

#### Document Chat — `chat_about_document(content, user_message, history)`

- Uses Gemini multi-turn chat (`model.start_chat(history=...)`).
- Converts frontend history `[{"role", "text"}]` to Gemini format `[{"role", "parts": [...]}]`.
- Sends document context + system instructions + user question in a single prompt.
- Gemini config: `temperature=0.3`, `top_p=0.9`, `max_output_tokens=1500`.
- Returns raw reply string.

#### Dynamic Chat — `dynamic_chat(user_input)` (CLI only)

Detects `/cot` prefix for chain-of-thought, keywords like `convert`, `code`, `why`, `how`, `solve`, `explain` for routing. Not used by the web app.

### 4.4 REST API — `api.py`

Built with FastAPI. All routes accept/return JSON except `/upload` (multipart).

**CORS**: `allow_origins=["*"]` — open for local dev. Restrict before production.

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Returns `{"message": "✅ BookBot API is running!"}` |
| `GET` | `/health` | Returns `{"status": "ok"}` |
| `POST` | `/upload` | Upload file; returns extracted text + metadata |
| `POST` | `/summarize` | Generate AI summary from document text |
| `POST` | `/quiz` | Generate AI quiz from document text |
| `POST` | `/chat` | Chat message grounded in document |

**`/upload` process**: validate extension → write to `tempfile` → `parse_file()` → validate ≥50 chars → delete tempfile → return `{filename, content, file_type, size, characters_extracted}`.

### 4.5 Python Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
google-generativeai>=0.8.5
python-dotenv==1.0.0
PyPDF2==3.0.1
python-docx==1.1.0
python-multipart
```

---

## 5. Frontend — Deep Dive

### 5.1 App Shell & State Management (`App.jsx`)

Single source of truth for global state using `useState`:

| State | Type | Description |
|---|---|---|
| `uploadedFile` | `File \| null` | Raw browser `File` object |
| `fileContent` | `string` | Extracted text from `/upload` |
| `summary` | `object \| null` | Normalized summary from AI |
| `quiz` | `object \| null` | Validated quiz `{questions: [...]}` |
| `currentView` | `string` | `'upload'` / `'summary'` / `'quiz'` / `'chat'` |

Key handlers: `handleFileUpload`, `handleSummaryGenerated`, `handleQuizGenerated` (async, calls API + validates), `resetApp`.

**Quiz normalization in App.jsx** (second pass after backend): checks non-empty question, exactly 4 non-empty options, answer exists in options. Invalid questions filtered out.

### 5.2 Component: FileUpload

**Props**: `{ onFileUpload }`

Two input modes toggled by tab buttons:
1. **File mode** — drag-and-drop zone. Calls `apiService.uploadFile(file)` → `onFileUpload(file, response.content)`.
2. **Text paste mode** — `<textarea>`. Creates mock file object, calls `onFileUpload(mockFile, textInput)` directly **without any backend call**.

Local state: `isDragOver`, `isProcessing`, `textInput`, `inputMode`.

### 5.3 Component: SummaryDisplay

**Props**: `{ file, content, onSummaryGenerated, onGenerateQuiz, onStartChat, onReset }`

Auto-triggers `generateSummary()` on mount via `useEffect([content])`.

Summary fields mapped from backend:
```
key_points → highlights
difficulty → difficulty
computed word_count and char_count from content string
```

Quiz size buttons: Quick (5q), Standard (10q), Comprehensive (20q), Custom (window.prompt 1–20).

States: `summary`, `isGenerating`, `isQuizGenerating`, `error`.

### 5.4 Component: QuizInterface

**Props**: `{ quiz, onBackToSummary, onReset }`

Three phases:
1. **Intro** — question count + 10-minute timer, Start button.
2. **Active** — one question at a time, progress bar, timer, question indicators, Prev/Next nav.
3. **Results** — score % circle, color-coded message, per-question breakdown.

Score messages: ≥90% "Excellent!", ≥80% "Great job!", ≥70% "Good work!", ≥60% "Not bad!", <60% "Keep studying!".

State: `currentQuestion`, `selectedAnswers` (map `{index: answerText}`), `showResults`, `timeLeft`, `quizStarted`.

### 5.5 Component: DocumentChat

**Props**: `{ content, onBack }`

- Starts with a welcome `model` message.
- **Critical**: filters this welcome message from history before sending to `/chat` (Gemini requires history to start with `user` role).
- Auto-scrolls via `messagesEndRef`.
- Shows typing indicator (three animated dots) while waiting.
- Enter key triggers send.

### 5.6 Service Layer — `api.js`

Singleton `ApiService` class.

**Base URL**: `import.meta.env.VITE_API_URL || 'http://localhost:8000'`

| Method | Endpoint | Notes |
|---|---|---|
| `uploadFile(file)` | `POST /upload` | `multipart/form-data` |
| `generateSummary(content, title)` | `POST /summarize` | JSON body |
| `generateQuiz(content, questionCount)` | `POST /quiz` | Validates 1–50 count client-side |
| `sendChatMessage(content, message, history)` | `POST /chat` | Sends full history array |
| `processFile(file)` | `POST /process` | Legacy, unused |

Error handling: backend `detail` field used as user-facing message; `TypeError` (network) gives "Could not connect to backend" message.

### 5.7 Design System & CSS

**Theme**: Deep Burgundy + Oak White design token system (configured in `src/index.css`).

- **Brand Colors**: `--color-primary: #571133` (Deep Burgundy), `--color-primary-hover: #762448` (Wine)
- **Backgrounds**: `--color-background: #FAF8F5` (Luminous Oak White dominant bg), `--color-bg-secondary: #F3EFE8` (Soft Pale Oak)
- **Cards & Borders**: `--color-card: #FFFFFF` (Crisp Oak White card surface), `--color-border: #E5E0D8` (Pale Oak Wood-Grain border)
- **Accents**: `--color-accent: #A65B76` (Muted Rose / Berry), `--color-accent-soft: #E2D3D8` (Pale Oak Rose)
- **Text**: `--color-text: #231C1F` (Deep Charcoal), `--color-muted: #786E66` (Accessible Oak Taupe)

**Animation utilities** in `App.css`:
- `.animate-fade` — fade in 500ms
- `.animate-slide-up` — slide up + fade 600ms
- `.hover-float:hover` — lifts -4px with shadow
- `.hover-pop:hover` — lifts -2px + scale 1.02
- `.btn-shimmer` — gradient shimmer on hover
- `.stagger-list > *` — staggers child animations at 60ms intervals (up to 5 children)

**Spinner**: `.spinner` and `.spinner.small` — CSS border-top rotation.

**Card base**: `.card` — white bg, `border-radius: 12px`, `box-shadow: var(--shadow-md)`.

**Font**: Inter font family for typography + Google Font `Coiny` for logo/header accents.

### 5.8 Frontend Dependencies

Runtime: `react ^19.1.1`, `react-dom ^19.1.1`

Dev: `vite ^7.1.2`, `@vitejs/plugin-react ^5.0.0`, `eslint ^9.33.0` + react plugins.

---

## 6. Data Flow Diagrams

### 6.1 File Upload Flow

```
User drops/selects file
      │
      ▼
FileUpload.jsx → apiService.uploadFile(file)
      │               POST /upload (multipart)
      │                     │
      │           api.py: validate ext → tempfile
      │           → parse_file() → validate ≥50 chars
      │           → delete tempfile
      │                     │
      ◄── {filename, content, file_type, size, chars_extracted}
      │
      ▼
App.jsx: handleFileUpload(file, content)
  setUploadedFile / setFileContent / setCurrentView('summary')
```

### 6.2 Summary Generation Flow

```
SummaryDisplay mounts → useEffect → generateSummary()
      │
      ▼
apiService.generateSummary(content, title)
      │               POST /summarize
      │                     │
      │           main.py: validate → truncate 30k
      │           → Gemini prompt → parse JSON
      │                     │
      ◄── {title, summary, key_points, difficulty}
      │
      ▼
SummaryDisplay: normalize → setSummary()
App.jsx: onSummaryGenerated(data)
```

### 6.3 Quiz Generation Flow

```
User clicks quiz button (e.g. "Standard — 10q")
      │
      ▼
SummaryDisplay: handleGenerateQuiz(10) → onGenerateQuiz(10)
      │
      ▼
App.jsx: handleQuizGenerated(10)
      │
      ▼
apiService.generateQuiz(fileContent, 10)
      │               POST /quiz
      │                     │
      │           main.py: validate → truncate 30k
      │           → Gemini → parse → validate each question
      │                     │
      ◄── {questions: [...validated...]}
      │
      ▼
App.jsx: re-validate + normalize → setQuiz() → setCurrentView('quiz')
```

### 6.4 Document Chat Flow

```
User types + sends message
      │
      ▼
DocumentChat: handleSend()
  → append user message to messages
  → filter out initial welcome model message from history
      │
      ▼
apiService.sendChatMessage(content, msg, history)
      │               POST /chat
      │                     │
      │           main.py: convert history to Gemini format
      │           → model.start_chat(history=...)
      │           → chat.send_message(doc_context + question)
      │                     │
      ◄── {reply: "..."}
      │
      ▼
DocumentChat: append {role:'model', text:reply} → auto-scroll
```

---

## 7. API Reference

**Dev Base URL**: `http://localhost:8000`
**Prod Base URL**: Set via `VITE_API_URL` env var

### `POST /upload`
- Request: `multipart/form-data`, field `file`
- Allowed: `.pdf`, `.txt`, `.docx`
- Response 200: `{filename, content, file_type, size, characters_extracted}`
- Error 400: bad format, empty file, too little text
- Error 500: parse failure

### `POST /summarize`
- Request: `{"content": "...", "title": "..."}`
- Response 200: `{title, summary, key_points: [...], difficulty}`
- Error 400: missing content

### `POST /quiz`
- Request: `{"content": "...", "question_count": 10}`
- `question_count` must be integer 1–50
- Response 200: `{questions: [{question, options: [4 strings], answer, explanation}]}`
- Error 400: missing content, invalid count
- Error 500: Gemini failure or zero valid questions

### `POST /chat`
- Request: `{"content": "...", "message": "...", "history": [{role, text}]}`
- Response 200: `{"reply": "..."}`
- Error 400: missing content or message

---

## 8. Gemini AI Integration

**Model**: `gemini-3.6-flash` (hardcoded in `main.py` line 28)

| Feature | temperature | top_p | max_tokens | mime_type |
|---|---|---|---|---|
| Summary | 0.2 | 0.9 | 2500 | `application/json` |
| Quiz | 0.3 | 0.9 | 5000 | `application/json` |
| Chat | 0.3 | 0.9 | 1500 | *(plain text)* |

**Document context limit**: 30,000 characters for all features.

**JSON robustness**: `_strip_code_fences()` removes markdown fences; `_coerce_json()` uses bracket-stack fallback parsing if direct `json.loads()` fails.

---

## 9. View State Machine

```
    [ upload ]
         │ file uploaded
         ▼
    [ summary ] ◄── onBack() ──┬──── onReset() ──► [ upload ]
         │                     │
         │ onStartChat()        │
         ▼                     │
      [ chat ] ─── onBack() ───┘

    [ summary ]
         │ quiz generated (valid questions exist)
         ▼
      [ quiz ] ──── onBackToSummary() ───► [ summary ]
               ──── onReset() ───────────► [ upload ]
```

Only one view renders at a time (mutually exclusive `&&` conditionals in `App.jsx`).

---

## 10. Known Patterns & Conventions

### Double Validation of Quiz Questions
Validated **twice** — once in `main.py` (Python), once in `App.jsx` (JS). Intentional redundancy to ensure malformed Gemini output never reaches the UI.

### Stateless Backend
The backend stores no state. Every request from the frontend sends the **full document text** along with it. No sessions, no DB, no caching.

### Text Paste Bypasses Backend
"Paste Text" mode in `FileUpload` skips `/upload` entirely and passes text directly through `onFileUpload` with a mock file object.

### FastAPI Error Messages via `detail`
All `HTTPException` instances set a `detail` string. The frontend `request()` method reads `data?.detail` for user-facing error messages.

### Stagger Animation Pattern
Lists use the `.stagger-list` class which applies CSS `animation-delay` to the first 5 children (60ms, 120ms, 180ms, 240ms, 300ms) for a cascading reveal effect.

---

## 11. Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key from [Google AI Studio](https://aistudio.google.com/) |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ❌ Optional | Backend URL override. Default: `http://localhost:8000` |

---

## 12. Running the Project Locally

### Prerequisites
- Python 3.8+
- Node.js v16+
- Google Gemini API key

### Backend
```bash
cd backend

# Optional: create virtual environment
python -m venv ../.venv
../.venv\Scripts\activate  # Windows
# source ../.venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
echo GEMINI_API_KEY=your_key_here > .env
python run_api.py
```
API: `http://localhost:8000` | Swagger UI: `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App: `http://localhost:5173`

---

## 13. Gotchas & Important Notes

> **Scanned PDFs won't work.** PyPDF2 extracts text-layer only. Image/scanned PDFs return empty text and get rejected with a 400 error.

> **Gemini history must start with "user" role.** `DocumentChat.jsx` filters out the initial welcome `model` message before building the history array. Preserve this if refactoring the chat component.

> **Quiz `answer` must exactly match an option string.** Both backend and frontend use strict equality. If Gemini rephrases the answer, the question is dropped. If too many are dropped, consider tightening the prompt.

> **`gemini-3.6-flash` is hardcoded** in `main.py` line 28. Update if the model is deprecated.

> **CORS is wide open.** Restrict `allow_origins` before any public deployment.

> **No authentication.** Anyone reaching the backend can use Gemini API credits. Add auth middleware before going public.

> **Custom quiz UI caps at 20 questions** (via `window.prompt` validation). Backend allows up to 50. Intentional — the UI is more conservative.

> **`QuizGenerator.jsx` exists but is unused.** It appears to be a leftover from an earlier iteration. The quiz launching UI is inside `SummaryDisplay.jsx`.

> **The bookbot logo is positioned with standard flexbox alignment** in `.app-header` (`padding: 0.6rem 2rem; display: flex; align-items: center; justify-content: flex-start;`), ensuring clean rendering across all viewport sizes.

---

## 14. Future Roadmap

- [ ] User authentication & accounts — save quiz history, track progress
- [ ] Save & export quizzes — download as PDF or share via link
- [ ] Image-based PDF support — integrate OCR (e.g. `pytesseract`) for scanned docs
- [ ] Progress tracking & analytics — quiz score history, weak topic detection
- [ ] More file formats — `.epub`, `.pptx`, `.md`
- [ ] Flashcard mode — spaced-repetition flashcards from key points
- [ ] Multi-document support — upload multiple files, cross-reference them
- [ ] Collaborative features — share documents and quizzes with teammates
- [ ] Production hardening — CORS restrictions, HTTPS, rate limiting, auth
- [x] Fix logo CSS `translate` property to standard flexbox header alignment

---

*Last updated: September 2026 · Stack: React 19 + FastAPI 0.104 + Google Gemini `gemini-3.6-flash`*
