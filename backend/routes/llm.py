from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any
from services.llm import query_llm

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    metadata: Optional[Any] = None

@router.post("/llm-query")
async def ask_llm(req: QueryRequest):
    answer = query_llm(req.question, req.metadata)
    return {"answer": answer}
