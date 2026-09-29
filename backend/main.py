
import os
import re
import json
from typing import Any, Dict, Union

from dotenv import load_dotenv
import google.generativeai as genai


# ============================================================
# ENVIRONMENT / GEMINI CONFIGURATION
# ============================================================

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "❌ GEMINI_API_KEY not found in backend/.env file"
    )

genai.configure(api_key=api_key)

# Use a current Gemini Flash model.
model = genai.GenerativeModel("gemini-3.6-flash")


# ============================================================
# HELPERS
# ============================================================

BOOK_PATTERN = re.compile(
    r"^(.*)\s+by\s+(.*)$",
    re.IGNORECASE
)


def _strip_code_fences(text: str) -> str:
    """
    Remove markdown code fences if Gemini returns JSON
    wrapped inside ```json ... ```.
    """

    if not text:
        return ""

    text = text.strip()

    if text.startswith("```"):
        first_newline = text.find("\n")

        if first_newline != -1:
            text = text[first_newline + 1:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def _coerce_json(
    text: str
) -> Union[Dict[str, Any], Any]:
    """
    Robustly parse JSON returned by Gemini.
    """

    if not text:
        return {
            "error": "Empty AI response",
            "raw": ""
        }

    candidate = _strip_code_fences(text)

    # --------------------------------------------------------
    # First attempt: direct JSON parsing
    # --------------------------------------------------------

    try:
        return json.loads(candidate)
    except Exception:
        pass

    # --------------------------------------------------------
    # Second attempt: locate JSON object/array in response
    # --------------------------------------------------------

    start_obj = candidate.find("{")
    start_arr = candidate.find("[")

    starts = [
        x
        for x in (start_obj, start_arr)
        if x != -1
    ]

    if starts:
        start = min(starts)

        stack = []
        end = None

        for i, ch in enumerate(
            candidate[start:],
            start=start
        ):
            if ch in "{[":
                stack.append(ch)

            elif ch in "}]":
                if not stack:
                    break

                opener = stack.pop()

                if (
                    (opener == "{" and ch == "}") or
                    (opener == "[" and ch == "]")
                ):
                    if not stack:
                        end = i + 1
                        break

        if end:
            fragment = candidate[start:end]

            try:
                return json.loads(fragment)
            except Exception:
                pass

    return {
        "error": "Failed to parse JSON",
        "raw": text
    }


# ============================================================
# FILE PARSING
# ============================================================

def parse_file(file_path: str) -> str:
    """
    Extract readable text from:
        .txt
        .pdf
        .docx
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    ext = os.path.splitext(file_path)[1].lower()

    # --------------------------------------------------------
    # TXT
    # --------------------------------------------------------

    if ext == ".txt":
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            return file.read().strip()

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if ext == ".pdf":
        import PyPDF2

        extracted_pages = []

        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)

            for page in reader.pages:
                page_text = page.extract_text() or ""

                if page_text.strip():
                    extracted_pages.append(
                        page_text.strip()
                    )

        return "\n\n".join(
            extracted_pages
        ).strip()

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if ext == ".docx":
        import docx

        document = docx.Document(file_path)

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n\n".join(paragraphs).strip()

    raise ValueError(
        "Unsupported file format. "
        "Use .txt, .pdf, or .docx."
    )


# ============================================================
# TEXT VALIDATION
# ============================================================

def validate_document_text(
    content: str
) -> str:
    """
    Ensure the extracted document actually contains
    meaningful text before sending it to Gemini.
    """

    if content is None:
        raise ValueError(
            "No document content was provided."
        )

    content = str(content).strip()

    if not content:
        raise ValueError(
            "Document content is empty."
        )

    if len(content) < 50:
        raise ValueError(
            "Very little readable text was extracted "
            "from the document. The PDF may be scanned "
            "or image-based."
        )

    return content


# ============================================================
# SUMMARY GENERATION
# ============================================================

def generate_structured_summary(
    content: str,
    title: str = "Document"
):
    """
    Generate a detailed AI summary using the ACTUAL
    document content.
    """

    content = validate_document_text(content)

    # Prevent extremely large prompts.
    max_chars = 30000
    document_text = content[:max_chars]

    prompt = f"""
You are BookBot, an AI learning assistant.

Your job is to analyze the actual document provided below
and create a useful study-oriented summary.

CRITICAL REQUIREMENTS:

1. Use ONLY information found in the document.
2. Do NOT invent facts.
3. Identify the actual subject and topics discussed.
4. Explain important concepts clearly and simply.
5. Include important definitions when present.
6. Include important examples when present.
7. Explain important processes or steps when present.
8. Identify important conclusions or takeaways.
9. The summary must be specific to this document.
10. NEVER give generic placeholder text such as:
   "The document discusses..."
   without explaining what it actually discusses.
11. NEVER say:
   "PDF content will be processed by backend."
12. NEVER create fake facts.
13. Make the summary useful for a student preparing for an exam.
14. Return ONLY valid JSON.

Create exactly this JSON structure:

{{
  "title": "{title}",
  "summary": "A detailed, easy-to-understand summary of the actual document.",
  "key_points": [
    "Specific important point from the document",
    "Specific important point from the document",
    "Specific important point from the document",
    "Specific important point from the document",
    "Specific important point from the document"
  ],
  "difficulty": "beginner"
}}

Difficulty must be one of:
"beginner"
"intermediate"
"advanced"

DOCUMENT:
==================================================
{document_text}
==================================================
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
            "top_p": 0.9,
            "max_output_tokens": 2500,
        },
    )

    result = _coerce_json(response.text)

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini returned an invalid summary."
        )

    if result.get("error"):
        raise ValueError(
            result.get("error")
        )

    if not result.get("summary"):
        raise ValueError(
            "Gemini did not return a summary."
        )

    return result


# ============================================================
# QUIZ GENERATION
# ============================================================

def generate_quiz_from_text(
    text: str,
    num_q: int = 5
):
    """
    Generate multiple-choice questions based ONLY on
    the actual document.
    """

    text = validate_document_text(text)

    try:
        num_q = int(num_q)
    except Exception:
        num_q = 5

    if num_q < 1:
        num_q = 1

    if num_q > 50:
        num_q = 50

    document_text = text[:30000]

    prompt = f"""
You are BookBot, an AI quiz generator.

Create exactly {num_q} multiple-choice questions based
ONLY on the document below.

VERY IMPORTANT:

1. Every question MUST come directly from information
   contained in the document.
2. Questions must test real concepts, facts, definitions,
   examples, processes, comparisons, causes/effects,
   applications, or other meaningful information.
3. Do NOT use generic questions such as:
   "What is the primary concept?"
   "What is the main idea?"
   unless the document specifically discusses that concept.
4. Questions should be different from each other.
5. Avoid asking the same fact repeatedly.
6. Each question must have EXACTLY 4 options.
7. There must be EXACTLY ONE correct answer.
8. Incorrect options should be plausible but incorrect
   according to the document.
9. The correct answer must be the EXACT TEXT of one option.
10. Add a short explanation based on the document.
11. NEVER use outside knowledge.
12. NEVER invent information.
13. Return ONLY valid JSON.

Return exactly:

{{
  "questions": [
    {{
      "question": "A specific question based on the document",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "answer": "Exact text of the correct option",
      "explanation": "Why this option is correct according to the document."
    }}
  ]
}}

DOCUMENT:
==================================================
{document_text}
==================================================
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.3,
            "top_p": 0.9,
            "max_output_tokens": 5000,
        },
    )

    result = _coerce_json(response.text)

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini returned an invalid quiz response."
        )

    if result.get("error"):
        raise ValueError(
            result.get("error")
        )

    questions = result.get("questions")

    if not isinstance(questions, list):
        raise ValueError(
            "Gemini did not return a questions array."
        )

    validated_questions = []

    for question in questions:
        if not isinstance(question, dict):
            continue

        question_text = str(
            question.get("question", "")
        ).strip()

        options = question.get(
            "options",
            []
        )

        answer = str(
            question.get("answer", "")
        ).strip()

        explanation = str(
            question.get(
                "explanation",
                "This answer is supported by the document."
            )
        ).strip()

        # ----------------------------------------------------
        # Validate question
        # ----------------------------------------------------

        if not question_text:
            continue

        if not isinstance(options, list):
            continue

        if len(options) != 4:
            continue

        clean_options = [
            str(option).strip()
            for option in options
        ]

        if any(
            not option
            for option in clean_options
        ):
            continue

        if answer not in clean_options:
            continue

        validated_questions.append({
            "question": question_text,
            "options": clean_options,
            "answer": answer,
            "explanation": explanation,
        })

    if not validated_questions:
        raise ValueError(
            "Gemini generated quiz data, but "
            "none of the questions passed validation."
        )

    # Return requested amount where possible.
    validated_questions = validated_questions[:num_q]

    return {
        "questions": validated_questions
    }


# ============================================================
# BOOK-BASED QUIZ
# ============================================================

def generate_quiz_from_book(
    title: str,
    author: str,
    num_q: int = 5
):
    """
    Kept for CLI compatibility.

    This function cannot reliably generate a quiz from a
    book title alone because the book content is not available.
    """

    raise ValueError(
        "Book-title-only quiz generation is not supported. "
        "Upload the document so BookBot can generate "
        "questions from its actual content."
    )


# ============================================================
# DOCUMENT CHAT
# ============================================================

def chat_about_document(
    content: str,
    user_message: str,
    history: list
) -> str:

    content = validate_document_text(content)

    if not user_message or not user_message.strip():
        raise ValueError(
            "Please enter a message."
        )

    # Limit context size.
    document_context = content[:30000]

    system_instruction = f"""
You are BookBot, an AI tutor.

Answer the student's question using the uploaded
document as the primary source.

RULES:

1. Use the document content.
2. Do not invent facts.
3. If the answer is clearly present in the document,
   explain it accurately.
4. If the answer cannot be found in the document,
   say that the information is not available in
   the uploaded document.
5. Keep explanations student-friendly.
6. Do not pretend something is in the document
   when it is not.

DOCUMENT:
==================================================
{document_context}
==================================================
"""

    gemini_history = []

    # Convert frontend history into Gemini format.
    for message in history or []:

        if not isinstance(message, dict):
            continue

        role = message.get(
            "role",
            "user"
        )

        text = message.get(
            "text",
            ""
        )

        if not text:
            continue

        gemini_role = (
            "user"
            if role == "user"
            else "model"
        )

        gemini_history.append({
            "role": gemini_role,
            "parts": [text]
        })

    chat = model.start_chat(
        history=gemini_history
    )

    prompt = f"""
{system_instruction}

STUDENT QUESTION:
{user_message}
"""

    response = chat.send_message(
        prompt,
        generation_config={
            "temperature": 0.3,
            "top_p": 0.9,
            "max_output_tokens": 1500,
        },
    )

    return response.text


# ============================================================
# DYNAMIC CHAT MODES
# ============================================================

def dynamic_chat(user_input: str):

    if not user_input or not user_input.strip():
        return "Please enter a question."

    if user_input.startswith("/cot"):

        query = (
            user_input
            .replace("/cot", "", 1)
            .strip()
        )

        prompt = f"""
You are a careful reasoning assistant.

Answer the question clearly without revealing
private chain-of-thought.

Question:
{query}

Return:

Final: <answer>

Why:
- <short reason>
- <short reason>
"""

        return model.generate_content(
            prompt
        ).text

    if any(
        word in user_input.lower()
        for word in ["convert", "code", "format"]
    ):

        prompt = f"""
Solve the following task clearly.

User request:
{user_input}
"""

        return model.generate_content(
            prompt
        ).text

    if any(
        word in user_input.lower()
        for word in [
            "why",
            "how",
            "solve",
            "explain"
        ]
    ):

        prompt = f"""
Answer the question clearly and concisely.

Question:
{user_input}
"""

        return model.generate_content(
            prompt
        ).text

    return model.generate_content(
        user_input
    ).text


# ============================================================
# CLI
# ============================================================

def chatbot():

    print(
        "🤖 BookBot AI Assistant\n"
    )

    print(
        "Commands:"
    )

    print(
        " • /sumfile <path>  → summarize a file"
    )

    print(
        " • /quizfile <path> → generate quiz from file"
    )

    print(
        " • /cot <question>  → reasoning-style answer"
    )

    print(
        " • exit             → quit\n"
    )

    while True:

        user_input = input(
            "You: "
        ).strip()

        if user_input.lower() in {
            "exit",
            "quit"
        }:
            break

        # ----------------------------------------------------
        # FILE SUMMARY
        # ----------------------------------------------------

        if user_input.startswith(
            "/sumfile "
        ):

            path = user_input.replace(
                "/sumfile ",
                "",
                1
            ).strip()

            try:
                text = parse_file(path)

                summary = generate_structured_summary(
                    content=text,
                    title=os.path.basename(path)
                )

                print(
                    "\n📖 Summary:\n"
                )

                print(
                    json.dumps(
                        summary,
                        indent=2,
                        ensure_ascii=False
                    )
                )

            except Exception as error:

                print(
                    f"\n❌ {error}\n"
                )

            continue

        # ----------------------------------------------------
        # FILE QUIZ
        # ----------------------------------------------------

        if user_input.startswith(
            "/quizfile "
        ):

            path = user_input.replace(
                "/quizfile ",
                "",
                1
            ).strip()

            try:

                text = parse_file(path)

                quiz = generate_quiz_from_text(
                    text,
                    num_q=5
                )

                print(
                    "\n📝 Quiz:\n"
                )

                print(
                    json.dumps(
                        quiz,
                        indent=2,
                        ensure_ascii=False
                    )
                )

            except Exception as error:

                print(
                    f"\n❌ {error}\n"
                )

            continue

        # ----------------------------------------------------
        # COT
        # ----------------------------------------------------

        if user_input.startswith(
            "/cot "
        ):

            print(
                "\n"
                + dynamic_chat(user_input)
                + "\n"
            )

            continue

        # ----------------------------------------------------
        # NORMAL CHAT
        # ----------------------------------------------------

        print(
            "\n"
            + dynamic_chat(user_input)
            + "\n"
        )


if __name__ == "__main__":
    chatbot()

