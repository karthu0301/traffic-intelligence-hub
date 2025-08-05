from collections import Counter, defaultdict
from fastapi import APIRouter, Query
from services.llm import (
    generate_daily_summary,
    generate_weekly_summary,
    generate_monthly_summary,
    generate_yearly_summary,
    generate_trend_summary,
)
from models import PlateInfo, DetectionRecord
from sqlmodel import Session, select
from db import engine

router = APIRouter()

@router.get("/report")
def get_report(
    range: str = Query("daily", regex="^(daily|weekly|monthly|yearly)$"),
    rich: bool = False
):

    if range == "weekly":
        base_summary = generate_weekly_summary()
    elif range == "monthly":
        base_summary = generate_monthly_summary()
    elif range == "yearly":
        base_summary = generate_yearly_summary()
    else:
        base_summary = generate_daily_summary()

    response = {"summary": base_summary}

    if rich:
        trends = generate_trend_summary(range)
        response["trends"] = trends

        # Extra analytics: plate frequency and accuracy trends
        with Session(engine) as session:
            plates = session.exec(select(PlateInfo.plate_string)).all()
            counter = Counter(plates)
            response["plate_frequency"] = [
                {"plate": plate, "count": count} for plate, count in counter.items()
            ]

            # Accuracy trends
            records = session.exec(
                select(PlateInfo, DetectionRecord)
                .join(DetectionRecord, PlateInfo.detection_id == DetectionRecord.id)
            ).all()
            trends_map = defaultdict(list)
            for plate, record in records:
                day = str(record.timestamp).split("T")[0]
                trends_map[day].append(plate.plate_confidence)

            response["accuracy_trends"] = [
                {"date": date, "avg_confidence": round(sum(confs) / len(confs), 4)}
                for date, confs in sorted(trends_map.items())
            ]

    return response
