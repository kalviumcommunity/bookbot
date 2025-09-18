from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import uvicorn
import json

# Import AI logic from main.py
from main import parse_file, generate_structured_summary, generate_quiz_from_text

app = FastAPI(title="BookBot API", version="1.0.0")

# Allow frontend requests (Netlify, Vercel, local React dev servers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later to your Netlify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "✅ BookBot API is running!"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content_bytes = await file.read()
            tmp_file.write(content_bytes)
            tmp_file_path = tmp_file.name

        try:
            file_content = parse_file(tmp_file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

        return {
            "filename": file.filename,
            "content": file_content,
            "file_type": file.content_type,
            "size": len(content_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_content(data: dict):
    """Generate AI-powered structured summary"""
    try:
        title = data.get("title", "Document")
        author = data.get("author", "Unknown")
        summary = generate_structured_summary(title, author)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz")
async def generate_quiz(data: dict):
    """Generate quiz from content"""
    try:
        content = data.get("content", "")
        question_count = data.get("question_count", 5)

        if not content:
            raise HTTPException(status_code=400, detail="No content provided")

        quiz_data = generate_quiz_from_text(content, num_q=question_count)
        return quiz_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # For local testing
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
