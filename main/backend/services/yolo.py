from ultralytics import YOLO
import cv2
import os
import uuid
from pathlib import Path

plate_model = YOLO("/Users/rajirajeev/Documents/Karthika/NUS/Y2/internship/LLM Integration/traffic-intelligence-hub/models/License Plate Detection v4/runs/detect/train/weights/best.pt")
char_model = YOLO("/Users/rajirajeev/Documents/Karthika/NUS/Y2/internship/LLM Integration/traffic-intelligence-hub/models/License Plate Characters v5/weights.pt") 

BASE_DIR   = Path(__file__).resolve().parent.parent   
RESULTS_DIR = BASE_DIR / "runs" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

char_map = "0123456789ABCDEFGHJKLMNOPQRSTUVWXYZ"

def group_and_sort_characters(chars, row_thresh=0.15):
    if not chars:
        return []

    # Sort initially by vertical center
    chars_sorted = sorted(chars, key=lambda c: (c["box"][1] + c["box"][3]) / 2)

    rows = []
    current_row = [chars_sorted[0]]
    for ch in chars_sorted[1:]:
        prev_y_center = (current_row[-1]["box"][1] + current_row[-1]["box"][3]) / 2
        curr_y_center = (ch["box"][1] + ch["box"][3]) / 2

        # Same row if vertically close
        if abs(curr_y_center - prev_y_center) < row_thresh * (ch["box"][3] - ch["box"][1]):
            current_row.append(ch)
        else:
            rows.append(current_row)
            current_row = [ch]
    rows.append(current_row)

    # Sort characters in each row horizontally
    for r in rows:
        r.sort(key=lambda c: c["box"][0])

    # Flatten: top-to-bottom, left-to-right
    return [c for row in rows for c in row]


def detect_plates_and_characters(image_path: str,
                                  plate_conf_thresh=0.5,
                                  char_conf_thresh=0.5):
    """
    Detects plates, crops them, detects characters, and returns annotated results.
    """
    result_id = uuid.uuid4().hex[:8]
    plate_results = plate_model(image_path)[0]
    orig_image = plate_results.orig_img
    detections = []

    for i, (box, conf, cls) in enumerate(zip(
            plate_results.boxes.xyxy,
            plate_results.boxes.conf,
            plate_results.boxes.cls)):

        plate_confidence = float(conf)
        if plate_confidence < plate_conf_thresh:
            continue  # Skip low-confidence plates

        x1, y1, x2, y2 = map(int, box.tolist())
        crop = orig_image[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        # Save original crop for debugging
        crop_filename = f"plate_{result_id}_{i}.jpg"
        crop_path = RESULTS_DIR / crop_filename
        cv2.imwrite(str(crop_path), crop)

        # Resize crop for character detection
        crop_resized = cv2.resize(crop, (640, 640))

        # Run char detection
        char_results = char_model(
            crop_resized,
            conf=char_conf_thresh,
            iou=0.5,
            max_det=50
        )[0]

        chars = []
        for j, cbox in enumerate(char_results.boxes.xyxy):
            cx1, cy1, cx2, cy2 = map(int, cbox.tolist())
            class_id = int(char_results.boxes.cls[j])
            char_conf = float(char_results.boxes.conf[j])

            if char_conf < char_conf_thresh:
                continue

            chars.append({
                "box": [cx1, cy1, cx2, cy2],
                "class_id": class_id,
                "confidence": char_conf
            })

        # Group and sort characters
        sorted_chars = group_and_sort_characters(chars, row_thresh=0.15)

        plate_string = (
            "".join([char_map[c["class_id"]] for c in sorted_chars])
            if sorted_chars else None
        )

        # Annotate characters on the resized crop
        for char in sorted_chars:
            cx1, cy1, cx2, cy2 = char["box"]
            label = char_map[char["class_id"]]
            cv2.rectangle(crop_resized, (cx1, cy1), (cx2, cy2), (0, 255, 0), 1)
            cv2.putText(crop_resized, label, (cx1, cy1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

        # Save annotated character crop
        annotated_crop_filename = f"plate_annotated_{result_id}_{i}.jpg"
        annotated_crop_path = RESULTS_DIR / annotated_crop_filename
        cv2.imwrite(str(annotated_crop_path), crop_resized)

        # Store detection
        detections.append({
            "plate_box": [x1, y1, x2, y2],
            "plate_crop_path": f"/static/results/{crop_filename}",
            "annotated_crop_path": f"/static/results/{annotated_crop_filename}",
            "plate_string": plate_string or "UNKNOWN",
            "plate_confidence": plate_confidence,
            "characters": sorted_chars
        })

    # Save annotated full image with plate detections
    annotated_filename = f"annotated_{result_id}.jpg"
    annotated_path = RESULTS_DIR / annotated_filename
    plate_results.save(filename=str(annotated_path))

    return {
        "annotated_image": f"/static/results/{annotated_filename}",
        "detections": detections
    }