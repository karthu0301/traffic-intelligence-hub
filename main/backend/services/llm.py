import redis
from ollama import Client
from main.backend.celery_worker import celery_app

from sqlmodel import Session, select
from main.backend.db import engine
from main.backend.models import DetectionRecord, PlateInfo
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Literal

# Ollama client
client = Client()
# Redis client (same DB as Celery broker)
r = redis.Redis(host="localhost", port=6379, db=0)

def build_prompt(question, metadata):
    detection_summary = "No metadata provided."
    if metadata:
        detection_summary = f"Filename: {metadata.get('filename')}\n"
        if 'detections' in metadata and metadata['detections']:
            detection_summary += f"Detected plates: {len(metadata['detections'])}\n"
            for i, d in enumerate(metadata['detections']):
                detection_summary += (
                    f"- Plate {i+1}: {d.get('plate_string','N/A')} "
                    f"(conf: {d.get('plate_confidence','?')})\n"
                )
        else:
            detection_summary += "No plates detected.\n"

    return (
        "You are an AI assistant that helps developers debug issues with a license plate "
        "detection and character recognition pipeline.\n\n"
        f"Question: {question}\n\n"
        f"Metadata:\n{detection_summary}\n\n"
        "Explain what might be happening and suggest improvements."
    )


def generate_context_from_db(question: str) -> str:
    with Session(engine) as session:
        # Get detections from the last 7 days (can adjust)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        results = session.exec(
            select(DetectionRecord)
            .where(DetectionRecord.timestamp >= seven_days_ago)
            .order_by(DetectionRecord.timestamp.desc())
            .limit(200)
        ).all()

        lines = []
        for record in results:
            plates = session.exec(
                select(PlateInfo).where(PlateInfo.detection_id == record.id)
            ).all()
            plate_list = ", ".join([f"{p.plate_string} ({p.plate_confidence:.2f})" for p in plates])
            lines.append(f"{record.timestamp}: {record.filename} => {plate_list}")

        if not lines:
            return "No detections found in the database."

        return "\n".join(lines)


def generate_daily_summary():
    today = datetime.utcnow().date()
    with Session(engine) as session:
        results = session.exec(
            select(DetectionRecord).where(DetectionRecord.timestamp >= today)
        ).all()
        return _summarize_records(results, session)

def generate_weekly_summary():
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    with Session(engine) as session:
        results = session.exec(
            select(DetectionRecord).where(DetectionRecord.timestamp >= one_week_ago)
        ).all()
        return _summarize_records(results, session)

def generate_monthly_summary():
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    with Session(engine) as session:
        results = session.exec(
            select(DetectionRecord).where(DetectionRecord.timestamp >= one_month_ago)
        ).all()
        return _summarize_records(results, session)
    
def generate_yearly_summary():
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    with Session(engine) as session:
        results = session.exec(
            select(DetectionRecord).where(DetectionRecord.timestamp >= one_year_ago)
        ).all()
        return _summarize_records(results, session)

def _summarize_records(records, session: Session) -> str:
    lines = []
    for record in records:
        plates = session.exec(
            select(PlateInfo).where(PlateInfo.detection_id == record.id)
        ).all()
        plate_list = ", ".join([p.plate_string for p in plates]) or "No plates"
        lines.append(f"{record.timestamp.date()} - {record.filename} -> {plate_list}")

    return "\n".join(lines) if lines else "No detections for this period."

def generate_trend_summary(range: Literal["daily", "weekly", "monthly", "yearly"]):
    now = datetime.utcnow()
    if range == "weekly":
        start_date = now - timedelta(days=7)
    elif range == "monthly":
        start_date = now - timedelta(days=30)
    elif range == "yearly":
        start_date = now - timedelta(days=365)
    else:
        start_date = now.date()

    with Session(engine) as session:
        results = session.exec(
            select(DetectionRecord).where(DetectionRecord.timestamp >= start_date)
        ).all()

        plate_counter = Counter()
        detections_per_day = defaultdict(int)

        for record in results:
            plates = session.exec(
                select(PlateInfo).where(PlateInfo.detection_id == record.id)
            ).all()
            for p in plates:
                plate_counter[p.plate_string] += 1

            # Count detections by day
            day = record.timestamp.date()
            detections_per_day[day] += len(plates)

        top_plates = plate_counter.most_common(5)
        daily_counts = [
            {"date": str(day), "count": count}
            for day, count in sorted(detections_per_day.items())
        ]

    return {
        "top_plates": [{"plate": plate, "count": count} for plate, count in top_plates],
        "daily_counts": daily_counts,
    }

@celery_app.task(bind=True)
def run_llm_task(self, question: str, metadata: dict = None):
    if metadata:
        # Developer assistant prompt
        prompt = build_prompt(question, metadata)
    else:
        # Analytics assistant
        lower_q = question.lower()

        # Map keywords to summary functions
        summary_map = {
            "daily summary": generate_daily_summary,
            "weekly summary": generate_weekly_summary,
            "monthly summary": generate_monthly_summary,
            "yearly summary": generate_yearly_summary,
        }

        # Check for summary keywords
        matched = None
        for key, func in summary_map.items():
            if lower_q.startswith(key):
                matched = func
                break

        if matched:
            context = matched()
            prompt = f"Summarize the {key} detection log:\n{context}"
        else:
            # General analytics
            context = generate_context_from_db(question)
            prompt = (
                "You are a traffic analytics assistant. Use the following detection data to answer the question.\n\n"
                f"Detections log:\n{context}\n\n"
                f"Question: {question}\n\n"
                "Base your answer strictly on the log data above. If the data is insufficient, say so."
            )

    key = f"llm_stream:{self.request.id}"
    r.delete(key)

    response_text = ""
    for part in client.chat(
        model="gemma:2b",  # can change model
        messages=[{"role": "user", "content": prompt}],
        stream=True
    ):
        chunk = part["message"]["content"]
        response_text += chunk
        r.rpush(key, chunk)

    r.rpush(key, "[[END]]")
    return response_text

