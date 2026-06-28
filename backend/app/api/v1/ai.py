from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.services import (
    generate_note_stream,
    analyze_note,
    chat_with_ai,
    chat_with_ai_stream,
    translate_note_stream,
)
from app.core.field_crypto import SecretCryptoError
from app.core.security import get_current_user
from app.core.rate_limit import rate_limit_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.crud import user as crud_user
from app.crud import ai_usage as crud_ai_usage
from app.models.ai import (
    GenerateNoteRequest,
    SummarizeNoteRequest,
    TranslateNoteRequest,
    ChatRequest,
)

router = APIRouter()

# 共享依赖：所有 AI 接口都用同一 rate_limit_user("ai") 策略
_ai_rate_limit = Depends(rate_limit_user("ai"))


@router.post("/generate-note", summary="AI生成笔记")
async def generate_note_endpoint(
    req: GenerateNoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """AI生成笔记接口，支持参考笔记和图片"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 仅保留流式实现：在服务端聚合为完整正文后返回 JSON（与现有前端契约一致）
        parts: list[str] = []
        async for chunk in generate_note_stream(
            topic=req.topic,
            keyword=req.keywords,
            reference_notes=req.referenceNotes,
            images=req.images,
            word_count=req.wordCount or 600,
            db_user=db_user,
        ):
            parts.append(chunk)
        note_content = "".join(parts).strip()
        
        # 记录AI使用
        await crud_ai_usage.log_ai_usage(db, db_user.id, "generate")
        
        return {"code": 200, "message": "生成成功", "data": {"content": note_content}}
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")


@router.post("/generate-note-stream", summary="流式生成笔记")
async def generate_note_stream_endpoint(
    req: GenerateNoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """流式生成笔记：响应体为 Markdown 纯文本增量，与翻译流式接口用法一致。"""
    try:
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        async def stream_generator():
            async for chunk in generate_note_stream(
                topic=req.topic,
                keyword=req.keywords,
                reference_notes=req.referenceNotes,
                images=req.images,
                word_count=req.wordCount or 600,
                db_user=db_user,
            ):
                yield chunk
            await crud_ai_usage.log_ai_usage(db, db_user.id, "generate")

        return StreamingResponse(stream_generator(), media_type="text/plain")
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
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """AI总结笔记接口，返回内容总结、优缺点和建议"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
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


@router.post("/translate-note-stream", summary="流式翻译笔记")
async def translate_note_stream_endpoint(
    req: TranslateNoteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """流式翻译笔记：HTML/富文本会先转为 Markdown 再翻译，响应体为纯文本流。"""
    try:
        db_user = await crud_user.get_user_by_email(
            db, email=current_user["email"]
        )
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        async def stream_generator():
            async for chunk in translate_note_stream(
                req.content, req.targetLang, db_user=db_user
            ):
                yield chunk
            
            # 记录AI使用
            await crud_ai_usage.log_ai_usage(db, db_user.id, "translate")

        return StreamingResponse(stream_generator(), media_type="text/plain")
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败：{str(e)}") from e


@router.post("/chat", summary="AI对话")
async def chat_endpoint(
    req: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """AI 对话接口，支持上下文聊天"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
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


@router.post("/chat-stream", summary="AI对话流式")
async def chat_stream_endpoint(
    req: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """流式对话：响应体为纯文本增量（assistant 全文），与翻译/生成笔记流式用法一致。"""
    try:
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        async def stream_generator():
            async for chunk in chat_with_ai_stream(
                req.message, req.history, db_user=db_user
            ):
                yield chunk
            await crud_ai_usage.log_ai_usage(db, db_user.id, "chat")

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}")