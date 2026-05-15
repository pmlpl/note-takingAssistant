from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.services import generate_note, analyze_note, chat_with_ai, translate_note
from app.core.field_crypto import SecretCryptoError
from typing import Optional, List
from app.core.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.crud import user as crud_user
from app.crud import ai_usage as crud_ai_usage

router = APIRouter()


class ReferenceNote(BaseModel):
    """参考笔记模型"""
    filename: str
    content: str


class GenerateNoteRequest(BaseModel):
    topic: str
    keywords: Optional[str] = None
    referenceNotes: Optional[List[ReferenceNote]] = Field(default_factory=list)
    images: Optional[List[str]] = Field(default_factory=list)  # base64 编码的图片
    wordCount: Optional[int] = 600  # 期望字数，默认600字


class SummarizeNoteRequest(BaseModel):
    content: str


class TranslateNoteRequest(BaseModel):
    content: str
    targetLang: str = Field(..., min_length=2, max_length=12)


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


@router.post("/generate-note", summary="AI生成笔记")
async def generate_note_endpoint(
    req: GenerateNoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """AI生成笔记接口，支持参考笔记和图片"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 调用 AI 服务（异步 HTTP，不阻塞事件循环）
        note_content = await generate_note(
            topic=req.topic,
            keyword=req.keywords,
            reference_notes=req.referenceNotes,
            images=req.images,
            word_count=req.wordCount,
            db_user=db_user,
        )
        
        # 记录AI使用
        await crud_ai_usage.log_ai_usage(db, db_user.id, "generate")
        
        return {"code": 200, "message": "生成成功", "data": {"content": note_content}}
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")


@router.post("/summarize-note", summary="AI总结笔记")
async def summarize_note_endpoint(
    req: SummarizeNoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """AI总结笔记接口，返回内容总结、优缺点和建议"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        result = await analyze_note(req.content, db_user=db_user)
        
        # 记录AI使用
        await crud_ai_usage.log_ai_usage(db, db_user.id, "summarize")
        
        return {"code": 200, "message": "分析成功", "data": result}
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败：{str(e)}")


@router.post("/translate-note", summary="翻译笔记")
async def translate_note_endpoint(
    req: TranslateNoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """将笔记正文译为目标语言（Markdown 全文翻译或 HTML 仅译文本节点保留 DOM），返回带水印。"""
    try:
        db_user = await crud_user.get_user_by_username(
            db, username=current_user["username"]
        )
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        result = await translate_note(
            req.content, req.targetLang, db_user=db_user
        )
        await crud_ai_usage.log_ai_usage(db, db_user.id, "translate")
        return {"code": 200, "message": "翻译成功", "data": result}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败：{str(e)}") from e


@router.post("/chat", summary="AI对话")
async def chat_endpoint(
    req: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """AI 对话接口，支持上下文聊天"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        reply = await chat_with_ai(req.message, req.history, db_user=db_user)
        
        # 记录AI使用
        await crud_ai_usage.log_ai_usage(db, db_user.id, "chat")
        
        return {"code": 200, "message": "回复成功", "data": {"reply": reply}}
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}")