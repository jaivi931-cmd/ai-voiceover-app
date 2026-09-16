import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import whisper

app = FastAPI(title="VOXIFYR AI Backend Engine")

# CORS Setup - Enable Front-End Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Speech-To-Text Model
print("Loading Speech-To-Text AI Model...")
model = whisper.load_model("tiny")
print("Model Loaded Successfully!")

@app.get("/")
def home():
    return {"status": "VOXIFYR AI Engine Running Smoothly"}

@app.post("/extract-audio")
async def extract_audio_from_video(file: UploadFile = File(...)):
    try:
        # Save temp uploaded video file
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run Whisper STT for precise text extraction
        result = model.transcribe(file_path)
        extracted_text = result.get("text", "").strip()

        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

        if not extracted_text:
            extracted_text = "Could not extract clear speech. Please type your script manually."

        return JSONResponse(content={"success": True, "text": extracted_text})

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
