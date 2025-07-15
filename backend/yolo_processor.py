from ultralytics import YOLO
import cv2
import os
import uuid

model = YOLO("/Users/rajirajeev/Documents/Karthika/NUS/Y2/internship/old/License Plate Detection v4/runs/detect/train/weights/best.pt") 

def detect_plates(image_path: str, save_dir: str = "runs/results"):
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.basename(image_path)
    result_id = str(uuid.uuid4())[:8]
    
    # Run detection
    results = model(image_path)[0]

    # Load original image
    img = cv2.imread(image_path)
    detections = []

    for i, box in enumerate(results.boxes.xyxy):
        x1, y1, x2, y2 = map(int, box)
        plate_crop = img[y1:y2, x1:x2]
        crop_path = os.path.join(save_dir, f"plate_{result_id}_{i}.jpg")
        cv2.imwrite(crop_path, plate_crop)

        detections.append({
            "box": [x1, y1, x2, y2],
            "confidence": float(results.boxes.conf[i]),
            "class_id": int(results.boxes.cls[i]),
            "crop_path": crop_path
        })

    # Save annotated image
    annotated_path = os.path.join(save_dir, f"annotated_{result_id}.jpg")
    results.save(filename=annotated_path)

    return {
        "annotated_image": annotated_path,
        "detections": detections
    }
