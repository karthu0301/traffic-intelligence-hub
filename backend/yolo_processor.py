# yolo_processor.py

from ultralytics import YOLO
import cv2
import os

# Load the model once (outside function)
model = YOLO('yolov11n.pt')  

def detect_plates(image_path: str, save_dir: str = "runs/detect"):
    results = model(image_path, save=True, save_txt=True, project=save_dir, name="results", exist_ok=True)
    return results[0]  # Return result object
