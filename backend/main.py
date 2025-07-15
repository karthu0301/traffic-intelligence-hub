from fastapi import FastAPI, UploadFile, File
import shutil, os
from fastapi.middleware.cors import CORSMiddleware
from yolo_processor import detect_plates

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify "http://192.168.50.143:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "../data/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run YOLO detection
    results = detect_plates(file_path)
    boxes = results.boxes.xyxy.tolist()
    classes = results.boxes.cls.tolist()
    confs = results.boxes.conf.tolist()

    return {
        "filename": file.filename,
        "detections": len(boxes),
        "results": [
            {
                "box": box,
                "class_id": int(cls),
                "confidence": round(conf, 2)
            }
            for box, cls, conf in zip(boxes, classes, confs)
        ]
    }