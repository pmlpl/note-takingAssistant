from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.field_crypto import SecretCryptoError
from app.core.rate_limit import rate_limit_user
from app.core.security import get_current_user
from app.crud import ai_conversation as crud_ai_conversation
from app.crud import ai_usage as crud_ai_usage
from app.crud import user as crud_user
from app.models.ai import (
    AgentChatRequest,
    ChatRequest,
    GenerateNoteRequest,
    SummarizeNoteRequest,
    TranslateNoteRequest,
)
from app.models.ai_conversation import (
    AIConversationCreateRequest,
    AIConversationDetailOut,
    AIConversationOut,
    AIMessageOut,
)
from app.services import (
    agent_chat_stream,
    analyze_note,
    chat_with_ai,
    chat_with_ai_stream,
    generate_note_stream,
    note_rag,
    translate_note_stream,
)

router = APIRouter()

# 共享依赖：所有 AI 接口都用同一 rate_limit_user("ai") 策略
_ai_rate_limit = Depends(rate_limit_user("ai"))

# RAG 自动上下文注入上限
_RAG_CONTEXT_CHUNKS = 5


async def _inject_note_context(db, db_user, message: str, history):
    """后端检索用户笔记相关片段，注入对话上下文（替代前端整篇塞入）。

    检索失败或无相关片段时不注入，保持对话可用。
    """
    try:
        items = await note_rag.retrieve_context(db, db_user=db_user, query=message, limit=_RAG_CONTEXT_CHUNKS)
    except Exception:
        return history
    if not items:
        return history
    lines = [f"- 【{it['note_title']}】{it['content']}" for it in items]
    context = "\n".join(lines)
    system_extra = (
        "以下内容来自用户笔记的自动检索结果，仅在回答相关问题时参考，不要声称是用户直接提供的原文：\n" + context
    )
    return list(history or []) + [{"role": "system", "content": system_extra}]


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
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        async def stream_generator():
            async for chunk in translate_note_stream(req.content, req.targetLang, db_user=db_user):
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
    """AI 对话接口，支持上下文聊天；自动注入用户笔记的相关片段（RAG）"""
    try:
        # 获取用户ID
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        history = await _inject_note_context(db, db_user, req.message, req.history)
        reply = await chat_with_ai(req.message, history, db_user=db_user)

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
    """流式对话：响应体为纯文本增量（assistant 全文），与翻译/生成笔记流式用法一致；自动注入用户笔记的相关片段（RAG）"""
    try:
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        history = await _inject_note_context(db, db_user, req.message, req.history)

        async def stream_generator():
            async for chunk in chat_with_ai_stream(req.message, history, db_user=db_user):
                yield chunk
            await crud_ai_usage.log_ai_usage(db, db_user.id, "chat")

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}")


@router.post("/agent-chat-stream", summary="Agent对话流式（带工具调用）")
async def agent_chat_stream_endpoint(
    req: AgentChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """Agent 流式对话：基于 Function Calling 主动调用工具（搜索/获取/总结/生成/翻译/创建笔记）。

    响应体为 SSE 事件流（`text/event-stream`），每个事件为 `data: {json}\\n\\n`，事件类型：
    - thinking：模型在调用工具前的思考说明
    - tool_start：开始执行工具（含工具名和参数）
    - tool_end：工具执行结束（含结果或摘要）
    - delta：最终回答的文本增量
    - done：完成（携带 conversation_id 便于前端刷新对话列表）
    - error：错误

    持久化：传入 conversation_id 则追加消息到指定对话；不传则自动创建新对话并返回其 id。
    """
    try:
        db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        async def stream_generator():
            try:
                async for event in agent_chat_stream(
                    req.message,
                    req.history,
                    db=db,
                    db_user=db_user,
                    conversation_id=req.conversation_id,
                    persist=True,
                ):
                    yield event
            finally:
                await crud_ai_usage.log_ai_usage(db, db_user.id, "chat")

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except SecretCryptoError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}") from e


# ============== 对话历史持久化接口 ==============
async def _get_db_user_or_404(db: AsyncSession, current_user: dict):
    """获取当前登录的数据库用户（统一封装，避免重复代码）"""
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user


@router.get("/conversations", summary="获取对话列表", response_model=list[AIConversationOut])
async def list_conversations_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """获取当前用户的全部 AI 对话列表，按最近更新倒序。"""
    db_user = await _get_db_user_or_404(db, current_user)
    items = await crud_ai_conversation.list_conversations(db, db_user.id, limit=100)
    return items


@router.post("/conversations", summary="新建对话", response_model=AIConversationOut)
async def create_conversation_endpoint(
    req: AIConversationCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """新建空对话；title 可选，不传则使用「新对话」。"""
    db_user = await _get_db_user_or_404(db, current_user)
    title = (req.title or "").strip() or "新对话"
    conv = await crud_ai_conversation.create_conversation(db, db_user.id, title)
    return conv


@router.get(
    "/conversations/{conversation_id}",
    summary="获取对话详情（含全部消息）",
    response_model=AIConversationDetailOut,
)
async def get_conversation_endpoint(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """获取指定对话的元信息和全部消息（按时间正序）。"""
    db_user = await _get_db_user_or_404(db, current_user)
    conv = await crud_ai_conversation.get_conversation(db, conversation_id, db_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = await crud_ai_conversation.list_messages(db, conversation_id, db_user.id)
    return AIConversationDetailOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[AIMessageOut.model_validate(m) for m in messages],
    )


@router.patch(
    "/conversations/{conversation_id}",
    summary="重命名对话标题",
    response_model=AIConversationOut,
)
async def rename_conversation_endpoint(
    conversation_id: int,
    req: AIConversationCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """重命名对话标题；title 为空时返回 400。"""
    db_user = await _get_db_user_or_404(db, current_user)
    title = (req.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    conv = await crud_ai_conversation.rename_conversation(db, conversation_id, db_user.id, title)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conv


@router.delete(
    "/conversations/{conversation_id}",
    summary="删除对话（级联删除消息）",
)
async def delete_conversation_endpoint(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _ai_rate_limit,
):
    """删除指定对话及其全部消息。"""
    db_user = await _get_db_user_or_404(db, current_user)
    ok = await crud_ai_conversation.delete_conversation(db, conversation_id, db_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "删除成功", "id": conversation_id}
