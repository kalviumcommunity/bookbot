
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware

import os
import tempfile
import uvicorn

from main import (
    parse_file,
    generate_structured_summary,
    generate_quiz_from_text,
    chat_about_document,
)

# ── Auth imports ──────────────────────────────────────────────
from database import create_tables
from auth import get_current_user
from models import User
import auth_routes

# ── Learning progress router ───────────────────────────────────
import quiz_routes


app = FastAPI(
    title="BookBot API",
    version="2.0.0",
    description="AI-powered study assistant with email/password authentication.",
)


# ============================================================
# STARTUP — create database tables if they don't exist yet
# ============================================================

@app.on_event("startup")
async def on_startup() -> None:
    create_tables()


# ============================================================
# AUTH ROUTER
# ============================================================

app.include_router(auth_routes.router)
app.include_router(quiz_routes.router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK  (public — no auth required)
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "✅ BookBot API is running!"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


# ============================================================
# UPLOAD  (protected)
# ============================================================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document and extract its text.
    Requires a valid Bearer token.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    temp_path = None

    try:

        extension = os.path.splitext(
            file.filename
        )[1].lower()

        allowed_extensions = {
            ".pdf",
            ".txt",
            ".docx"
        }

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported file format. "
                    "Use PDF, TXT, or DOCX."
                )
            )

        content_bytes = await file.read()

        if not content_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            temp_file.write(
                content_bytes
            )

            temp_path = temp_file.name

        # Extract actual document text.
        file_content = parse_file(
            temp_path
        )

        if not file_content or len(
            file_content.strip()
        ) < 50:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract enough readable text "
                    "from this document. The PDF may be "
                    "scanned/image-based."
                )
            )

        return {
            "filename": file.filename,
            "content": file_content,
            "file_type": file.content_type,
            "size": len(content_bytes),
            "characters_extracted": len(
                file_content
            )
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Error processing file: {str(error)}"
            )
        )

    finally:

        if (
            temp_path and
            os.path.exists(temp_path)
        ):
            os.unlink(temp_path)


# ============================================================
# SUMMARY  (protected)
# ============================================================

@app.post("/summarize")
async def summarize_content(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI summary from ACTUAL document text.
    Requires a valid Bearer token.
    """

    try:

        content = data.get(
            "content",
            ""
        ).strip()

        title = data.get(
            "title",
            "Document"
        )

        if not content:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No document content provided."
                )
            )

        summary = generate_structured_summary(
            content=content,
            title=title
        )

        return summary

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Summary generation failed: {str(error)}"
            )
        )


# ============================================================
# QUIZ  (protected)
# ============================================================

@app.post("/quiz")
async def generate_quiz(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI quiz from ACTUAL document content.
    Requires a valid Bearer token.
    """

    try:

        content = data.get(
            "content",
            ""
        ).strip()

        question_count = data.get(
            "question_count",
            5
        )

        if not content:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No document content provided."
                )
            )

        try:
            question_count = int(
                question_count
            )
        except Exception:

            raise HTTPException(
                status_code=400,
                detail=(
                    "question_count must be a number."
                )
            )

        if (
            question_count < 1 or
            question_count > 50
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "question_count must be between 1 and 50."
                )
            )

        quiz_data = generate_quiz_from_text(
            text=content,
            num_q=question_count
        )

        return quiz_data

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Quiz generation failed: {str(error)}"
            )
        )


# ============================================================
# DOCUMENT CHAT  (protected)
# ============================================================

@app.post("/chat")
async def document_chat(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Ask questions about the uploaded document.
    Requires a valid Bearer token.
    """

    try:

        content = data.get(
            "content",
            ""
        ).strip()

        message = data.get(
            "message",
            ""
        ).strip()

        history = data.get(
            "history",
            []
        )

        if not content:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No document content provided."
                )
            )

        if not message:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No message provided."
                )
            )

        reply = chat_about_document(
            content=content,
            user_message=message,
            history=history
        )

        return {
            "reply": reply
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Chat failed: {str(error)}"
            )
        )


# ============================================================
# LOCAL SERVER
# ============================================================

if __name__ == "__main__":

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
