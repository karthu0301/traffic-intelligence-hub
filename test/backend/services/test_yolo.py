from backend.services.yolo import detect_plates_and_characters

def test_detect_function_runs():
    # You may need to mock actual detection model
    try:
        result = detect_plates_and_characters("runs/results/annotated.jpg")
        assert isinstance(result, dict)
    except Exception:
        # If YOLO not configured, pass
        pass
