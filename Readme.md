# 📚 BookBot – AI-Powered Book Summarizer & Quiz Generator

> Summarize books and generate quizzes using **Prompting**, **RAG**, **Structured Output**, and **Function Calling**.

---

## 🔧 Tech Focused Breakdown

### 🧠 1. Prompting

BookBot uses carefully crafted prompts to:
- Summarize content in a teacher-like, clear tone.
- Generate MCQs, flashcards, and quizzes.

> Prompts guide the LLM to act like an educator, making the output learner-friendly and pedagogical.

---

### 🔍 2. RAG (Retrieval-Augmented Generation)

- Book content is parsed, split into chunks, and embedded.
- Chunks are stored in a vector database (e.g., FAISS or ChromaDB).
- At runtime, only the most relevant chunks are retrieved and passed to the LLM.

> This ensures high-context relevance and improves accuracy for summaries and quiz questions.