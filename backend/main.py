import os
import re
import json
from typing import Any, Dict, Union

from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------
# ENV / Gemini setup
# -------------------------------
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("❌ GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

# One shared model is fine; pass per-call configs as needed.
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------
# Helpers
# -------------------------------
BOOK_PATTERN = re.compile(r"^(.*)\s+by\s+(.*)$", re.IGNORECASE)

def _strip_code_fences(text: str) -> str:
    """Remove ```...``` fences if the model wrapped JSON."""
    text = text.strip()
    if text.startswith("```"):
        # Remove first fence
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _coerce_json(text: str) -> Union[Dict[str, Any], Any]:
    """
    Try hard to parse JSON out of model output.
    Returns dict/obj if JSON, else original text.
    """
    # 1) remove fences
    candidate = _strip_code_fences(text)
    try:
        return json.loads(candidate)
    except Exception:
        pass

    # 2) try to find a JSON object or array inside
    start_obj = candidate.find("{")
    start_arr = candidate.find("[")
    starts = [x for x in [start_obj, start_arr] if x != -1]
    if starts:
        start = min(starts)
        # simple brace matching to find the end
        stack = []
        end = None
        for i, ch in enumerate(candidate[start:], start=start):
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack:
                    break
                opener = stack.pop()
                if (opener == "{" and ch == "}") or (opener == "[" and ch == "]"):
                    if not stack:
                        end = i + 1
                        break
        if end:
            frag = candidate[start:end]
            try:
                return json.loads(frag)
            except Exception:
                pass

    # 3) give up -> return raw text
    return {"error": "Failed to parse JSON", "raw": text}

# -------------------------------
# File parsing
# -------------------------------
def parse_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    if ext == ".pdf":
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        return text.strip()

    if ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    raise ValueError("Unsupported file format (use .txt, .pdf, or .docx)")

# -------------------------------
# Summaries & quizzes
# -------------------------------
def generate_structured_summary(title: str, author: str):
    """
    Ask the model to return strict JSON and parse it robustly.
    """
    prompt = f"""
You are BookBot. Return ONLY valid JSON with this shape (no explanations):

{{
  "title": "{title}",
  "author": "{author}",
  "summary": "1–3 concise paragraphs",
  "key_points": ["point 1", "point 2", "point 3"],
  "difficulty": "beginner"  // allowed: beginner|intermediate|advanced
}}
"""
    resp = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.5,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        },
    )
    return _coerce_json(resp.text)

def generate_quiz_from_text(text: str, num_q: int = 5):
    """
    Create a multiple-choice quiz (strict JSON).
    """
    prompt = f"""
Create a {num_q}-question multiple-choice quiz based ONLY on this text:

{text[:7000]}

Return ONLY valid JSON like:
{{
  "questions": [
    {{
      "question": "…",
      "options": ["A", "B", "C", "D"],
      "answer": "B"
    }}
  ]
}}
"""
    resp = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.4,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        },
    )
    return _coerce_json(resp.text)

def generate_quiz_from_book(title: str, author: str, num_q: int = 5):
    summary = generate_structured_summary(title, author)
    # If parsing failed, summary may be dict with "raw" string
    summary_text = json.dumps(summary) if isinstance(summary, dict) else str(summary)
    return generate_quiz_from_text(summary_text, num_q=num_q)

# -------------------------------
# Dynamic chat modes
# -------------------------------
def dynamic_chat(user_input: str):
    if user_input.startswith("/cot"):
        query = user_input.replace("/cot", "").strip()
        prompt = f"""
You are a careful reasoning assistant.
Think privately, but ONLY output:
Final answer + 2–4 short bullets (no step-by-step).

Question: {query}

Return format:
Final: <answer>
Why (brief):
- <bullet>
- <bullet>
"""
        return model.generate_content(prompt).text

    if any(w in user_input.lower() for w in ["convert", "code", "format"]):
        prompt = f"You are in multi-shot style. Solve/convert clearly with one short example:\n\n{user_input}"
        return model.generate_content(prompt).text

    if any(w in user_input.lower() for w in ["why", "how", "solve", "explain"]):
        prompt = f"""
Answer the question and provide a short, high-level rationale (2–4 bullets).
Do NOT reveal step-by-step internal reasoning.

Question: {user_input}
"""
        return model.generate_content(prompt).text

    return model.generate_content(user_input).text

# -------------------------------
# CLI
# -------------------------------
def chatbot():
    print("🤖 AI Chatbot (Dynamic Prompting + Structured Output + Quiz + File Parsing)  — type 'exit' to quit\n")
    print("Commands:")
    print(" • /book <title> by <author>        → structured JSON summary")
    print(" • /quiz <title> by <author>        → quiz from the book")
    print(" • /sumfile <path>                  → summarize a file (txt/pdf/docx)")
    print(" • /quizfile <path>                 → quiz from a file")
    print(" • /cot <question>                  → safe chain-of-thought style")
    print(" • Plain '<Title> by <Author>'      → auto structured summary\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        # --- file: summarize ---
        if user_input.startswith("/sumfile "):
            path = user_input.replace("/sumfile ", "", 1).strip()
            try:
                text = parse_file(path)
                prompt = f"Summarize the following text in a few concise paragraphs:\n\n{text[:7000]}"
                print("\n📄 Summarizing file...\n")
                print(model.generate_content(prompt).text, "\n")
            except Exception as e:
                print(f"❌ {e}\n")
            continue

        # --- file: quiz ---
        if user_input.startswith("/quizfile "):
            path = user_input.replace("/quizfile ", "", 1).strip()
            try:
                text = parse_file(path)
                print("\n📝 Generating quiz from file...\n")
                quiz = generate_quiz_from_text(text)
                print(json.dumps(quiz, indent=2), "\n")
            except Exception as e:
                print(f"❌ {e}\n")
            continue

        # --- book: structured summary ---
        if user_input.startswith("/book "):
            rest = user_input.replace("/book ", "", 1).strip()
            m = BOOK_PATTERN.match(rest)
            if not m:
                print("❌ Use: /book <title> by <author>\n")
                continue
            title, author = m.groups()
            print("\n📖 Generating structured summary...\n")
            summary = generate_structured_summary(title.strip(), author.strip())
            print("Structured Book Summary (JSON):\n", json.dumps(summary, indent=2), "\n")
            continue

        # --- book: quiz ---
        if user_input.startswith("/quiz "):
            rest = user_input.replace("/quiz ", "", 1).strip()
            m = BOOK_PATTERN.match(rest)
            if not m:
                print("❌ Use: /quiz <title> by <author>\n")
                continue
            title, author = m.groups()
            print("\n📝 Generating quiz from book...\n")
            quiz = generate_quiz_from_book(title.strip(), author.strip())
            print(json.dumps(quiz, indent=2), "\n")
            continue

        # --- auto-detect "Title by Author" ---
        m = BOOK_PATTERN.match(user_input)
        if m:
            title, author = m.groups()
            print("\n📖 Detected book request → Generating structured summary...\n")
            summary = generate_structured_summary(title.strip(), author.strip())
            print("Structured Book Summary (JSON):\n", json.dumps(summary, indent=2), "\n")
            continue

        # --- default dynamic chat ---
        reply = dynamic_chat(user_input)
        print(reply, "\n")

if __name__ == "__main__":
    chatbot()
