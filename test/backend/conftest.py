import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

# Mock YOLO
@pytest.fixture(autouse=True)
def mock_yolo(monkeypatch):
    def fake_detect(path):
        return {
            "annotated_image": "runs/results/fake.jpg",
            "detections": [
                {
                    "plate_string": "FAKE123",
                    "plate_confidence": 0.95,
                    "plate_crop_path": "runs/results/crop.jpg",
                    "characters": []
                }
            ]
        }
    monkeypatch.setattr("backend.services.yolo.detect_plates_and_characters", fake_detect)

# Mock LLM
@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    def fake_llm(question, metadata=None):
        return "This is a mocked LLM response."
    monkeypatch.setattr("backend.services.llm.query_llm", fake_llm)
