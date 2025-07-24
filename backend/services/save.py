from sqlmodel import Session
from models import DetectionRecord, PlateInfo, CharacterBox

def save_detection_to_db(session: Session, filename: str, result: dict, user_id: int = None):
    detection = DetectionRecord(
        filename=filename,
        timestamp=result.get("timestamp") or "unknown",
        annotated_image=result["annotated_image_path"],
        user_id=user_id
    )
    session.add(detection)
    session.commit()
    session.refresh(detection)

    for plate in result["detections"]:
        plate_record = PlateInfo(
            detection_id=detection.id,
            plate_crop_path=plate["plate_crop_path"],
            plate_string=plate["plate_string"],
            plate_confidence=plate["plate_confidence"]
        )
        session.add(plate_record)

        for char in plate["characters"]:
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
