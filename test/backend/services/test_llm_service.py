import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from main.backend.services import llm
from main.backend.models import DetectionRecord, PlateInfo

def mock_exec_results(items):
    m = MagicMock()
    m.all.return_value = items
    return m


def test_build_prompt_with_metadata():
    metadata = {
        "filename": "test.jpg",
        "detections": [
            {"plate_string": "ABC123", "plate_confidence": 0.95},
            {"plate_string": "XYZ789", "plate_confidence": 0.88}
        ]
    }
    question = "Why is confidence low?"
    prompt = llm.build_prompt(question, metadata)

    assert "test.jpg" in prompt
    assert "Plate 1: ABC123" in prompt
    assert "Plate 2: XYZ789" in prompt
    assert question in prompt

def test_build_prompt_no_metadata():
    prompt = llm.build_prompt("Hello?", None)
    assert "No metadata provided" in prompt
    assert "Hello?" in prompt


@patch("main.backend.services.llm.Session")
def test_generate_context_from_db(mock_session_class):
    now = datetime.utcnow()
    record = DetectionRecord(id=1, filename="test.jpg", timestamp=now)
    plate = PlateInfo(detection_id=1, plate_string="ABC123", plate_confidence=0.95)

    # Mock for session.exec().all()
    mock_results = MagicMock()
    mock_results.all.return_value = [record]

    mock_plates = MagicMock()
    mock_plates.all.return_value = [plate]

    mock_session = MagicMock()
    mock_session.exec.side_effect = [mock_results, mock_plates]
    mock_session_class.return_value.__enter__.return_value = mock_session

    result = llm.generate_context_from_db("test question")
    assert "test.jpg" in result
    assert "ABC123" in result




@patch("main.backend.services.llm.Session")
def test_generate_daily_summary(mock_session_class):
    now = datetime.utcnow()
    record = DetectionRecord(id=1, filename="daily.jpg", timestamp=now)
    plate = PlateInfo(detection_id=1, plate_string="DAILY123", plate_confidence=0.91)

    mock_results = MagicMock()
    mock_results.all.return_value = [record]

    mock_plates = MagicMock()
    mock_plates.all.return_value = [plate]

    mock_session = MagicMock()
    mock_session.exec.side_effect = [mock_results, mock_plates]
    mock_session_class.return_value.__enter__.return_value = mock_session

    summary = llm.generate_daily_summary()
    assert "daily.jpg" in summary
    assert "DAILY123" in summary


@patch("main.backend.services.llm.Session")
def test_generate_trend_summary(mock_session_class):
    now = datetime.utcnow()
    record = DetectionRecord(id=1, filename="trend.jpg", timestamp=now)
    plates = [
        PlateInfo(detection_id=1, plate_string="ABC123", plate_confidence=0.9),
        PlateInfo(detection_id=1, plate_string="ABC123", plate_confidence=0.92),
        PlateInfo(detection_id=1, plate_string="XYZ789", plate_confidence=0.85),
    ]

    mock_session = MagicMock()
    mock_session.exec.side_effect = [
        mock_exec_results([record]),
        mock_exec_results(plates),
    ]
    mock_session_class.return_value.__enter__.return_value = mock_session

    summary = llm.generate_trend_summary("weekly")
    assert summary["top_plates"][0]["plate"] == "ABC123"
    assert summary["top_plates"][0]["count"] == 2
    assert any("date" in d and "count" in d for d in summary["daily_counts"])

