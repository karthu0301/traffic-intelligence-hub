from sqlmodel import Session
from models import DetectionRecord, PlateInfo, CharacterBox
from datetime import datetime

def save_detection_to_db(session: Session,
    filename: str,
    result: dict,
    user_id: int = None,
    model_version: str = None,
    confidence_threshold: float = None,
):
    
    ts = result.get("timestamp")
    if ts:
        try:
            # Allow string timestamps
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
        except Exception:
            ts = datetime.utcnow()
    else:
        ts = datetime.utcnow()
    
    detection = DetectionRecord(
        filename=filename,
        timestamp=ts,
        annotated_image=result["annotated_image_path"],
        user_id=user_id,
        model_version=model_version,
        confidence_threshold=confidence_threshold,
    )
    session.add(detection)
    session.commit()
    session.refresh(detection)

    for plate in result["detections"]:
        plate_record = PlateInfo(
            detection_id=detection.id,
            plate_crop_path=plate["plate_crop_path"],
            annotated_crop_path=plate["annotated_crop_path"],
            plate_string=plate.get("plate_string") or "UNKNOWN",
            plate_confidence=plate.get("plate_confidence", 0.0)
        )
        session.add(plate_record)

        for char in plate.get("characters", []):
            char_record = CharacterBox(
                detection_id=detection.id,
                x1=char["box"][0],
                y1=char["box"][1],
                x2=char["box"][2],
                y2=char["box"][3],
                class_id=char["class_id"],
                confidence=char["confidence"]
            )
            session.add(char_record)

    session.commit()
    return detection
