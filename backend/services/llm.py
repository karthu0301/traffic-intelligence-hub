import redis
from ollama import Client
from backend.celery_worker import celery_app

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

@celery_app.task(bind=True)
def run_llm_task(self, question: str, metadata: dict = None):
    """
    This Celery task runs the LLM and streams chunks to Redis.
    When finished, it stores a final END marker.
    """
    prompt = build_prompt(question, metadata)
    key = f"llm_stream:{self.request.id}"

    # Clear old data
    r.delete(key)

    response_text = ""
    # Stream tokens as they arrive
    for part in client.chat(
        model="gemma:2b",  # smaller and faster model
        messages=[{"role": "user", "content": prompt}],
        stream=True
    ):
        chunk = part["message"]["content"]
        response_text += chunk
        r.rpush(key, chunk)  # store token in Redis

    # Mark completion
    r.rpush(key, "[[END]]")
    return response_text
