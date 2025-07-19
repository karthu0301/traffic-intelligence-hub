from fastapi import FastAPI, UploadFile, File, Query, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, create_engine, Session, select, func
from collections import defaultdict
from datetime import datetime
import shutil, os

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
async def upload(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = detect_plates_and_characters(file_path)
    with Session(engine) as session:
        record = save_detection_to_db(session, file.filename, result)

        return {
            "filename": record.filename,
            "timestamp": record.timestamp,
            "annotated_image": record.annotated_image,
            "detections": result["detections"]
        }

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


@app.get("/detection-accuracy-trends")
def detection_accuracy_trends():
    with Session(engine) as session:
        records = session.exec(select(PlateInfo, DetectionRecord).join(DetectionRecord, PlateInfo.detection_id == DetectionRecord.id)).all()

        trends = defaultdict(list)
        for plate, record in records:
            day = record.timestamp.split("T")[0]
            trends[day].append(plate.plate_confidence)

        result = [
            {
                "date": date,
                "avg_confidence": round(sum(confs) / len(confs), 4)
            }
            for date, confs in sorted(trends.items())
        ]
        return JSONResponse(content=result)