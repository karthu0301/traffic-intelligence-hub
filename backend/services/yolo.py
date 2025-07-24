from ultralytics import YOLO
import cv2
import os
import uuid

plate_model = YOLO("/Users/rajirajeev/Documents/Karthika/NUS/Y2/internship/LLM Integration/traffic-intelligence-hub/License Plate Detection v4/runs/detect/train/weights/best.pt")
char_model = YOLO("/Users/rajirajeev/Documents/Karthika/NUS/Y2/internship/LLM Integration/traffic-intelligence-hub/License Plate Characters v5/weights.pt") 

char_map = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def detect_plates_and_characters(image_path: str, save_dir: str = "../runs/results"):
    os.makedirs(save_dir, exist_ok=True)
    result_id = str(uuid.uuid4())[:8]

    image = cv2.imread(image_path)
    plate_results = plate_model(image_path)[0]
    detections = []

    for i, (box, conf, cls) in enumerate(zip(plate_results.boxes.xyxy, plate_results.boxes.conf, plate_results.boxes.cls)):
        x1, y1, x2, y2 = map(int, box.tolist())
        plate_confidence = float(conf)

        crop = image[y1:y2, x1:x2]
        crop_filename = f"plate_{result_id}_{i}.jpg"
        crop_path = os.path.join(save_dir, crop_filename)
        cv2.imwrite(crop_path, crop)

        # Character detection
        char_results = char_model(crop)[0]
        chars = []

        for j, cbox in enumerate(char_results.boxes.xyxy):
            cx1, cy1, cx2, cy2 = map(int, cbox.tolist())
            class_id = int(char_results.boxes.cls[j])
            char_conf = float(char_results.boxes.conf[j])

            if char_conf < 0.4:
                continue  # Filter low confidence detections

            chars.append({
                "box": [cx1, cy1, cx2, cy2],
                "class_id": class_id,
                "confidence": char_conf
            })

        # Sort from left to right
        sorted_chars = sorted(chars, key=lambda c: c["box"][0])

        if sorted_chars:
            plate_string = "".join([char_map[c["class_id"]] for c in sorted_chars])
        else:
            plate_string = "N/A"

        # Annotate char boxes
        for char in sorted_chars:
            cx1, cy1, cx2, cy2 = char["box"]
            label = char_map[char["class_id"]]
            conf_text = f"{char['confidence']:.2f}"
            cv2.rectangle(crop, (cx1, cy1), (cx2, cy2), (0, 255, 0), 1)
            cv2.putText(crop, label, (cx1, cy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            cv2.putText(crop, conf_text, (cx1, cy2 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (100, 100, 255), 1)

        # Save annotated plate crop
        cv2.imwrite(crop_path, crop)

        detections.append({
            "plate_box": [x1, y1, x2, y2],
            "plate_crop_path": f"/static/results/{crop_filename}",
            "plate_string": plate_string,
            "plate_confidence": plate_confidence,
            "characters": sorted_chars
        })

    # Save annotated full image
    annotated_filename = f"annotated_{result_id}.jpg"
    annotated_path = os.path.join(save_dir, annotated_filename)
    plate_results.save(filename=annotated_path)

    return {
        "annotated_image": f"/static/results/{annotated_filename}",
        "detections": detections
    }
