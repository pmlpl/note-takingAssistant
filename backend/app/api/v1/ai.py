from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services import generate_note, analyze_note, chat_with_ai
from typing import Optional, List
import json

router = APIRouter()


class ReferenceNote(BaseModel):
    """参考笔记模型"""
    filename: str
    content: str


class GenerateNoteRequest(BaseModel):
    topic: str
    keywords: Optional[str] = None
    referenceNotes: Optional[List[ReferenceNote]] = []
    images: Optional[List[str]] = []  # base64 编码的图片
    wordCount: Optional[int] = 600  # 期望字数，默认600字


class SummarizeNoteRequest(BaseModel):
    content: str


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


@router.post("/generate-note", summary="AI生成笔记")
async def generate_note_endpoint(req: GenerateNoteRequest):
    """AI生成笔记接口，支持参考笔记和图片"""
    try:
        # 调用 AI 服务
        note_content = generate_note(
            topic=req.topic,
            keyword=req.keywords,
            reference_notes=req.referenceNotes,
            images=req.images,
            word_count=req.wordCount
        )
        return {"code": 200, "message": "生成成功", "data": {"content": note_content}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")


@router.post("/summarize-note", summary="AI总结笔记")
async def summarize_note_endpoint(req: SummarizeNoteRequest):
    """AI总结笔记接口，返回内容总结、优缺点和建议"""
    try:
        result = analyze_note(req.content)
        return {"code": 200, "message": "分析成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败：{str(e)}")


@router.post("/chat", summary="AI对话")
async def chat_endpoint(req: ChatRequest):
    """AI 对话接口，支持上下文聊天"""
    try:
        reply = chat_with_ai(req.message, req.history)
        return {"code": 200, "message": "回复成功", "data": {"reply": reply}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}")