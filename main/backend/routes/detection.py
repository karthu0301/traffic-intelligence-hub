from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlmodel import Session, select, delete
from datetime import datetime
from typing import List, Optional
from collections import defaultdict, Counter
import shutil, os, tempfile, zipfile

from db import engine, get_session
from models import DetectionRecord, PlateInfo, CharacterBox, User
from services.yolo import detect_plates_and_characters
from services.save import save_detection_to_db
from auth.utils import get_current_user_optional
from services.llm import query_llm

router = APIRouter()
UPLOAD_DIR = "../data/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def to_static_path(local_path: str) -> str:
    # local_path like 'runs/results/annotated_x.jpg' → '/static/results/annotated_x.jpg'
    rel = os.path.relpath(local_path, "runs")        # strip the leading 'runs/'
    return f"/static/{rel}"

@router.post("/upload")
async def upload(files: List[UploadFile] = File(...), user: Optional[User] = Depends(get_current_user_optional)):
    results = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = detect_plates_and_characters(file_path)

        static_annotated = to_static_path(result["annotated_image"])
        result["annotated_image"] = static_annotated
        result["annotated_image_path"] = static_annotated
        for det in result["detections"]:
            det["plate_crop_path"] = to_static_path(det["plate_crop_path"])
            
        if user:
            with Session(engine) as session:
                record = save_detection_to_db(session, file.filename, result, user_id=user.id)
        else:
            record = None

        results.append({
            "filename": file.filename,
            "timestamp": datetime.now().isoformat(),
            "annotated_image": result["annotated_image"],
            "detections": result["detections"],
            "saved": user is not None
        })

    return results


@router.get("/history")
def get_history():
    with Session(engine) as session:
        records = session.exec(select(DetectionRecord).order_by(DetectionRecord.id.desc())).all()
        return records

@router.get("/search")
def search(
    plate_query: str = Query(None),
    filename_query: str = Query(None),
    limit: int = Query(10),
    offset: int = Query(0),
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

        sort_column = DetectionRecord.timestamp if sort_by != "filename" else DetectionRecord.filename
        query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc())

        all_results = session.exec(query).all()
        total = len(all_results)
        results = all_results[offset : offset + limit]

        return {"results": results, "total": total}

@router.get("/result/{detection_id}")
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

@router.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join("runs", "results", filename)
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')

@router.get("/download-all")
def download_all_results(plate_query: str = "", filename_query: str = ""):
    with Session(engine) as session:
        statement = select(DetectionRecord).order_by(DetectionRecord.timestamp.desc())
        all_sessions = session.exec(statement).all()

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

    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(tmp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for record in filtered_sessions:
            if record.annotated_image and os.path.exists(record.annotated_image):
                zipf.write(record.annotated_image, arcname=os.path.basename(record.annotated_image))

            with Session(engine) as session:
                plates = session.exec(select(PlateInfo).where(PlateInfo.detection_id == record.id)).all()
                for p in plates:
                    if p.plate_crop_path and os.path.exists(p.plate_crop_path):
                        zipf.write(p.plate_crop_path, arcname=os.path.basename(p.plate_crop_path))

    zip_filename = f"all_results_{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return FileResponse(tmp_zip.name, media_type="application/zip", filename=zip_filename)

@router.delete("/delete/{record_id}")
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

@router.get("/plate-frequency")
def plate_frequency():
    with Session(engine) as session:
        plates = session.exec(select(PlateInfo.plate_string)).all()
        counter = Counter(plates)
        return [{"plate": plate, "count": count} for plate, count in counter.items()]

@router.get("/detection-accuracy-trends")
def detection_accuracy_trends():
    with Session(engine) as session:
        records = session.exec(
            select(PlateInfo, DetectionRecord)
            .join(DetectionRecord, PlateInfo.detection_id == DetectionRecord.id)
        ).all()

        trends = defaultdict(list)
        for plate, record in records:
            day = record.timestamp.split("T")[0]
            trends[day].append(plate.plate_confidence)

        return JSONResponse(content=[
            {"date": date, "avg_confidence": round(sum(confs) / len(confs), 4)}
            for date, confs in sorted(trends.items())
        ])

@router.post("/ask")
async def ask_question(req: Request):
    body = await req.json()
    question = body.get("question")

    with get_session() as session:
        detections = session.exec(select(DetectionRecord)).all()
        # Convert to dicts
        records = [d.model_dump() for d in detections]

    answer = query_llm(question, records)
    return {"answer": answer}

@router.post("/feedback/{upload_id}")
def save_feedback(upload_id: int, feedback: str, session: Session = Depends(get_session)):
    upload = session.get(UploadFile, upload_id)
    if not upload:
        return {"error": "Not found"}
    upload.feedback = feedback
    session.add(upload)
    session.commit()
    return {"status": "saved"}