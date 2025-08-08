import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from main.backend.services.yolo import detect_plates_and_characters, group_and_sort_characters

def test_group_and_sort_characters_single_row():
    chars = [
        {"box": [10, 10, 20, 20], "class_id": 1, "confidence": 0.9},
        {"box": [30, 10, 40, 20], "class_id": 2, "confidence": 0.8}
    ]
    sorted_chars = group_and_sort_characters(chars)
    assert sorted_chars[0]["box"][0] < sorted_chars[1]["box"][0] 

def test_group_and_sort_characters_multiple_rows():
    chars = [
        {"box": [10, 10, 20, 20], "class_id": 1, "confidence": 0.9},
        {"box": [12, 30, 22, 40], "class_id": 2, "confidence": 0.8} 
    ]
    sorted_chars = group_and_sort_characters(chars)
    assert len(sorted_chars) == 2  
    assert sorted_chars[0]["box"][1] < sorted_chars[1]["box"][1] 

@patch("main.backend.services.yolo.plate_model")
@patch("main.backend.services.yolo.char_model")
@patch("main.backend.services.yolo.cv2.imwrite")
@patch("main.backend.services.yolo.cv2.resize")
def test_detect_plates_and_characters(mock_resize, mock_imwrite, mock_char_model, mock_plate_model):
    fake_image = MagicMock()
    fake_image.__getitem__.return_value = MagicMock(size=1)  

    mock_plate_result = MagicMock()
    mock_plate_result.orig_img = fake_image
    fake_plate_box = MagicMock()
    fake_plate_box.tolist.return_value = [10, 10, 50, 50]
    mock_plate_result.boxes.xyxy = [fake_plate_box]
    mock_plate_result.boxes.conf = [0.9]
    mock_plate_result.boxes.cls = [0]
    mock_plate_result.save = MagicMock()
    mock_plate_model.return_value = [mock_plate_result]

    mock_char_result = MagicMock()
    fake_char_box = MagicMock()
    fake_char_box.tolist.return_value = [5, 5, 15, 15]
    mock_char_result.boxes.xyxy = [fake_char_box]
    mock_char_result.boxes.cls = [1]
    mock_char_result.boxes.conf = [0.95]
    mock_char_model.return_value = [mock_char_result]
    mock_resize.return_value = np.zeros((640, 640, 3), dtype=np.uint8)

    result = detect_plates_and_characters("dummy.jpg")

    assert "annotated_image" in result
    assert isinstance(result["detections"], list)
    assert result["detections"][0]["plate_string"] != "UNKNOWN"
    assert "plate_crop_path" in result["detections"][0]
    assert "annotated_crop_path" in result["detections"][0]
    assert result["detections"][0]["characters"][0]["class_id"] == 1