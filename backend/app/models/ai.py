from pydantic import BaseModel
from typing import Optional


class GenerateNoteRequest(BaseModel):
    topic: str
    keyword: Optional[str] = None


class SummarizeNoteRequest(BaseModel):
    content: str


class AIResponse(BaseModel):
    code: int = 200
    message: str
    data: str
