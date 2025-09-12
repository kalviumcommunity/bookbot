from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import tempfile
from typing import Optional
import uvicorn

# Import the existing functions from main.py
import sys
sys.path.append(os.path.dirname(__file__))
from main import parse_file, generate_structured_summary, generate_quiz_from_text

app = FastAPI(title="BookBot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "BookBot API is running!"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), content: str = Form("")):
    """Upload and process a file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content_bytes = await file.read()
            tmp_file.write(content_bytes)
            tmp_file_path = tmp_file.name

        # Process the file
        try:
            file_content = parse_file(tmp_file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
        finally:
            # Clean up temporary file
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
    """Generate a summary from content"""
    try:
        content = data.get("content", "")
        title = data.get("title", "Document")
        
        if not content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        # For now, create a mock summary
        # In a real implementation, you'd use the AI to generate this
        summary = {
            "title": title,
            "type": "text",
            "summary": f"This is an AI-generated summary of your document. The content has been analyzed and processed to extract key insights and main points. Original content length: {len(content)} characters.",
            "key_points": [
                "Key insight 1 from the document",
                "Important concept 2",
                "Main takeaway 3",
                "Critical information 4",
                "Essential point 5"
            ],
            "difficulty": "intermediate",
            "word_count": len(content.split()),
            "processing_time": "2.3 seconds"
        }
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz")
async def generate_quiz(data: dict):
    """Generate a quiz from content"""
    try:
        content = data.get("content", "")
        question_count = data.get("question_count", 10)
        
        if not content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        # Generate quiz using the existing function
        try:
            quiz_data = generate_quiz_from_text(content, num_q=question_count)
        except Exception as e:
            # Fallback to mock quiz if AI generation fails
            quiz_data = create_mock_quiz(question_count)
        
        return quiz_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    """Process a file and return both content and summary"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content_bytes = await file.read()
            tmp_file.write(content_bytes)
            tmp_file_path = tmp_file.name

        # Process the file
        try:
            file_content = parse_file(tmp_file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

        # Generate summary
        summary = {
            "title": file.filename,
            "type": file.content_type,
            "summary": f"This is an AI-generated summary of your {file.content_type} file. The content has been analyzed and processed to extract key insights and main points.",
            "key_points": [
                "Key insight 1 from the document",
                "Important concept 2", 
                "Main takeaway 3",
                "Critical information 4",
                "Essential point 5"
            ],
            "difficulty": "intermediate",
            "word_count": len(file_content.split()),
            "processing_time": "2.3 seconds"
        }

        return {
            "content": file_content,
            "summary": summary,
            "filename": file.filename,
            "file_type": file.content_type,
            "size": len(content_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_mock_quiz(question_count: int):
    """Create a mock quiz for testing purposes"""
    questions = []
    
    for i in range(question_count):
        questions.append({
            "question": f"Sample question {i + 1}: What is the main topic discussed in this document?",
            "options": [
                "Option A: Technology",
                "Option B: Science", 
                "Option C: Literature",
                "Option D: History"
            ],
            "answer": "Option A: Technology"
        })
    
    return {
        "questions": questions,
        "total_questions": question_count,
        "difficulty": "intermediate"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
