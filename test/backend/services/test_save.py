import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from datetime import datetime

from main.backend.models import DetectionRecord, PlateInfo, CharacterBox
from main.backend.services.save import save_detection_to_db  

# SQLite in-memory test engine
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def session():
    with Session(test_engine) as s:
        yield s

def test_save_detection_basic(session):
    result = {
        "annotated_image_path": "runs/results/annotated.jpg",
        "timestamp": datetime.utcnow().isoformat(),
        "detections": [
            {
                "plate_crop_path": "runs/results/crop1.jpg",
                "annotated_crop_path": "runs/results/annotated_crop1.jpg",
                "plate_string": "ABC123",
                "plate_confidence": 0.91,
                "characters": [
                    {
                        "box": [10, 20, 30, 40],
                        "class_id": 1,
                        "confidence": 0.99
                    }
                ]
            }
        ]
    }

    detection = save_detection_to_db(
        session=session,
        filename="test.jpg",
        result=result,
        user_id=1,
        model_version="v1.0",
        confidence_threshold=0.8
    )

    # Check detection saved
    db_detection = session.get(DetectionRecord, detection.id)
    assert db_detection is not None
    assert db_detection.filename == "test.jpg"
    assert db_detection.user_id == 1
    assert db_detection.model_version == "v1.0"
    assert db_detection.confidence_threshold == 0.8

    # Check plate info
    plates = session.exec(select(PlateInfo).where(PlateInfo.detection_id == detection.id)).all()
    assert len(plates) == 1
    assert plates[0].plate_string == "ABC123"
    assert plates[0].plate_confidence == 0.91

    # Check character box
    chars = session.exec(select(CharacterBox).where(CharacterBox.detection_id == detection.id)).all()
    assert len(chars) == 1
    assert chars[0].class_id == 1
    assert chars[0].confidence == 0.99

def test_save_detection_no_characters(session):
    result = {
        "annotated_image_path": "runs/results/annotated.jpg",
        "timestamp": None,
        "detections": [
            {
                "plate_crop_path": "runs/results/crop1.jpg",
                "annotated_crop_path": "runs/results/annotated_crop1.jpg",
                "plate_string": None,
                "plate_confidence": None,
                "characters": []
            }
        ]
    }

    detection = save_detection_to_db(session, "empty.jpg", result)

    # Plate string should default to "UNKNOWN"
    plates = session.exec(select(PlateInfo).where(PlateInfo.detection_id == detection.id)).all()
    assert plates[0].plate_string == "UNKNOWN"
    assert plates[0].plate_confidence == 0.0

    chars = session.exec(select(CharacterBox).where(CharacterBox.detection_id == detection.id)).all()
    assert len(chars) == 0
