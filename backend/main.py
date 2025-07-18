from fastapi import FastAPI, UploadFile, File, Query, Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, create_engine, Session, select
from datetime import datetime
import shutil, os
from typing import List
from models import DetectionRecord, PlateInfo, CharacterBox
from utils import save_detection_to_db
from yolo_processor import detect_plates_and_characters

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="runs"), name="static")

UPLOAD_DIR = "../data/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# SQLite
engine = create_engine("sqlite:///detections.db")
SQLModel.metadata.create_all(engine)

@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    responses = []

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = detect_plates_and_characters(file_path)

        with Session(engine) as session:
            record = save_detection_to_db(session, file.filename, result)

            # Read values while session is open
            response = {
                "filename": record.filename,
                "timestamp": record.timestamp,
                "annotated_image": record.annotated_image,
                "detections": result["detections"]
            }

        responses.append(response)

    return responses


@app.get("/history")
def get_history():
    with Session(engine) as session:
        records = session.exec(select(DetectionRecord).order_by(DetectionRecord.id.desc())).all()
        return records

@app.get("/search")
def search(plate_query: str = Query(None), filename_query: str = Query(None)):
    with Session(engine) as session:
        query = select(DetectionRecord)

        if filename_query:
            query = query.where(DetectionRecord.filename.contains(filename_query))

        if plate_query:
            detection_ids = session.exec(
                select(PlateInfo.detection_id).where(PlateInfo.plate_string.contains(plate_query))
            ).all()
            query = query.where(DetectionRecord.id.in_(detection_ids))

        results = session.exec(query.order_by(DetectionRecord.id.desc())).all()
        return results

@app.get("/result/{detection_id}")
def get_full_result(detection_id: int = Path(...)):
    with Session(engine) as session:
        record = session.get(DetectionRecord, detection_id)
        if not record:
            raise HTTPException(status_code=404, detail="Detection not found.")

        plates = session.exec(select(PlateInfo).where(PlateInfo.detection_id == detection_id)).all()
        char_map = {}
        for c in session.exec(select(CharacterBox).where(CharacterBox.detection_id == detection_id)).all():
            char_map.setdefault(c.detection_id, []).append({
                "box": [c.x1, c.y1, c.x2, c.y2],
                "class_id": c.class_id,
                "confidence": c.confidence,
            })

        detections = []
        for p in plates:
            detections.append({
                "plate_string": p.plate_string,
                "plate_confidence": p.plate_confidence,
                "plate_crop_path": p.plate_crop_path,
                "characters": char_map.get(p.detection_id, [])
            })

        return JSONResponse({
            "filename": record.filename,
            "timestamp": record.timestamp,
            "annotated_image": record.annotated_image,
            "detections": detections
        })