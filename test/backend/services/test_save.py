from backend.services.save import save_detection_to_db
from backend.models import DetectionRecord
from sqlmodel import Session
from backend.db import engine

def test_save_detection_to_db():
    dummy_result = {
        "timestamp": "2024-07-01T12:00:00",
        "annotated_image_path": "runs/results/annotated.jpg",
        "detections": []
    }
    with Session(engine) as session:
        record = save_detection_to_db(session, "test.jpg", dummy_result)
        assert isinstance(record, DetectionRecord)
        assert record.filename == "test.jpg"
