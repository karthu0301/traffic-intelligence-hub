from fastapi import FastAPI, UploadFile, File
import shutil, os
from fastapi.middleware.cors import CORSMiddleware
from yolo_processor import detect_plates_and_characters
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify "http://192.168.50.143:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="runs"), name="static")

history = []

UPLOAD_DIR = "../data/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run YOLO detection
    result = detect_plates_and_characters(file_path)
    
    record = {
        "filename": file.filename,
        "timestamp": datetime.now().isoformat(),
        "annotated_image": result["annotated_image"],
        "detections": result["detections"]
    }

    history.append(record)
    return record

@app.get("/history")
def get_history():
    return history
