from pydantic import BaseModel, Field
from typing import Optional, List


class ReferenceNote(BaseModel):
    """参考笔记模型"""
    filename: str
    content: str


class GenerateNoteRequest(BaseModel):
    """生成笔记请求模型"""
    topic: str
    keywords: Optional[str] = None
    referenceNotes: Optional[List[ReferenceNote]] = Field(default_factory=list)
    images: Optional[List[str]] = Field(default_factory=list)
    wordCount: Optional[int] = 600


class SummarizeNoteRequest(BaseModel):
    """总结笔记请求模型"""
    content: str


class TranslateNoteRequest(BaseModel):
    """翻译笔记请求模型"""
    content: str
    targetLang: str = Field(..., min_length=2, max_length=12)


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """AI对话请求模型"""
    message: str
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
