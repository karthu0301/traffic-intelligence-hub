from fastapi import FastAPI, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select
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
def search(
    plate_query: str = Query(None),
    filename_query: str = Query(None),
    sort_by: str = Query("timestamp"),
    order: str = Query("desc")
):
    with Session(engine) as session:
        query = select(DetectionRecord)

        if filename_query:
            query = query.where(DetectionRecord.filename.contains(filename_query))

        if plate_query:
            detection_ids = session.exec(
                select(PlateInfo.detection_id).where(PlateInfo.plate_string.contains(plate_query))
            ).all()
            query = query.where(DetectionRecord.id.in_(detection_ids))

        # Sorting
        if sort_by == "filename":
            sort_column = DetectionRecord.filename
        else:
            sort_column = DetectionRecord.timestamp

        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        results = session.exec(query).all()
        return results
