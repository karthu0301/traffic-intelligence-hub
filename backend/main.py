from fastapi import FastAPI, UploadFile, File, Query, APIRouter, Path, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select, delete
from collections import Counter
from models import DetectionRecord, PlateInfo, CharacterBox
from datetime import datetime
import shutil, os, io
from typing import List
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
def search(
    plate_query: str = Query(None),
    filename_query: str = Query(None),
    limit: int = Query(10),
    offset: int = Query(0)
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

        all_results = session.exec(query).all()
        total = len(all_results)
        results = all_results[offset : offset + limit]

        return {
            "results": results,
            "total": total
        }

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

@app.delete("/delete/{record_id}")
def delete_record(record_id: int = Path(...)):
    with Session(engine) as session:
        record = session.get(DetectionRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        session.exec(delete(PlateInfo).where(PlateInfo.detection_id == record_id))
        session.exec(delete(CharacterBox).where(CharacterBox.detection_id == record_id))
        session.delete(record)
        session.commit()
    return {"message": "Record deleted"}

@app.get("/plate-frequency")
def plate_frequency():
    with Session(engine) as session:
        plates = session.exec(select(PlateInfo.plate_string)).all()
        counter = Counter(plates)
        return [{"plate": plate, "count": count} for plate, count in counter.items()]
