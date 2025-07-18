from sqlmodel import Session
from models import DetectionRecord, PlateInfo, CharacterBox
from datetime import datetime


def save_detection_to_db(session: Session, filename: str, result: dict):
    detection = DetectionRecord(
        filename=filename,
        timestamp=datetime.now().isoformat(),
        annotated_image=result["annotated_image"]
    )
    session.add(detection)
    session.commit()
    session.refresh(detection)

    for d in result["detections"]:
        plate = PlateInfo(
            detection_id=detection.id,
            plate_crop_path=d["plate_crop_path"],
            plate_string=d["plate_string"],
            plate_confidence=d["plate_confidence"]
        )
        session.add(plate)
        session.commit()

        for char in d["characters"]:
            cb = CharacterBox(
                detection_id=detection.id,
                class_id=char["class_id"],
                confidence=char["confidence"],
                x1=char["box"][0],
                y1=char["box"][1],
                x2=char["box"][2],
                y2=char["box"][3],
            )
            session.add(cb)
    session.commit()
    return detection
