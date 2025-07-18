from fastapi import FastAPI, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import SQLModel, create_engine, Session, select
from models import DetectionRecord, PlateInfo, CharacterBox
from datetime import datetime
import shutil, os, io
import zipfile
import tempfile
import json

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

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join("runs", "results", filename)
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')

@app.get("/download-all")
def download_all_results(
    plate_query: str = "",
    filename_query: str = ""
):
    with Session(engine) as session:
        statement = select(DetectionRecord).order_by(DetectionRecord.timestamp.desc())
        all_sessions = session.exec(statement).all()

    # Filter sessions based on query
    filtered_sessions = []
    for record in all_sessions:
        if filename_query and filename_query.lower() not in record.filename.lower():
            continue
        if plate_query:
            matching_plates = session.exec(
                select(PlateInfo).where(PlateInfo.detection_id == record.id)
            ).all()
            if not any(plate_query.lower() in p.plate_string.lower() for p in matching_plates):
                continue
        filtered_sessions.append(record)

    if not filtered_sessions:
        raise HTTPException(status_code=404, detail="No matching results found.")

    # Create a temporary zip file on disk
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(tmp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for record in filtered_sessions:
            # Add annotated image
            if record.annotated_image and os.path.exists(record.annotated_image):
                zipf.write(record.annotated_image, arcname=os.path.basename(record.annotated_image))

            # Add all cropped plates
            with Session(engine) as session:
                plates = session.exec(
                    select(PlateInfo).where(PlateInfo.detection_id == record.id)
                ).all()
                for p in plates:
                    if p.plate_crop_path and os.path.exists(p.plate_crop_path):
                        zipf.write(p.plate_crop_path, arcname=os.path.basename(p.plate_crop_path))

    zip_filename = f"all_results_{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return FileResponse(tmp_zip.name, media_type="application/zip", filename=zip_filename)
