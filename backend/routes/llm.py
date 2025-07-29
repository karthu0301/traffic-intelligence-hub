from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
import redis

from backend.celery_worker import celery_app
from backend.services.llm import run_llm_task

router = APIRouter()
r = redis.Redis(host="localhost", port=6379, db=0)

@router.post("/ask")
def ask_llm(question: str, metadata: dict = None):
    task = run_llm_task.delay(question, metadata)
    return {"task_id": task.id}

@router.get("/result/{task_id}")
def get_llm_result(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.ready():
        return {"status": "done", "result": task_result.get()}
    return {"status": "pending"}

@router.get("/stream/{task_id}")
def stream_llm_result(task_id: str):
    key = f"llm_stream:{task_id}"

    def event_stream():
        last_index = 0
        while True:
            chunks = r.lrange(key, last_index, -1)
            if not chunks:
                # wait a short time to avoid busy-looping
                import time
                time.sleep(0.5)
                continue
            for c in chunks:
                text = c.decode()
                if text == "[[END]]":
                    return
                yield text
            last_index += len(chunks)

    return StreamingResponse(event_stream(), media_type="text/plain")
