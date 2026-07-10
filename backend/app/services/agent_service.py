"""
Agent 服务：基于 OpenAI Function Calling 的多工具智能助手

特点：
1. 工具调用：search_notes / get_note_content / summarize_note / generate_note / translate_note / create_note
2. 流式输出：以 SSE 事件流形式输出 thinking / tool_start / tool_end / delta / done / error 事件
3. 多轮工具调用：最多 MAX_TOOL_ROUNDS 轮，避免死循环
4. 复用现有 note_generator / note_analyzer / note_translator / crud.note 中的逻辑
5. 兼容性：若模型不支持 tools 参数（部分本地模型），自动降级为普通流式对话
6. 持久化：传入 conversation_id 时，在 done 事件前将 user/assistant 消息写入数据库

SSE 事件格式：
    data: {"type": "thinking", "text": "..."}\n\n
    data: {"type": "tool_start", "id": "...", "name": "...", "args": {...}}\n\n
    data: {"type": "tool_end", "id": "...", "name": "...", "result": {...}}\n\n
    data: {"type": "delta", "text": "..."}\n\n
    data: {"type": "done", "finish_reason": "stop", "conversation_id": 123}\n\n
    data: {"type": "error", "message": "..."}\n\n
"""
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.services.prompts import AGENT_SYSTEM_PROMPT
from app.utils.llm_errors import format_llm_error

logger = logging.getLogger(__name__)

# 最大工具调用轮数（避免死循环）
MAX_TOOL_ROUNDS = 5
# 工具结果字符上限（避免上下文爆炸）
MAX_TOOL_RESULT_CHARS = 4000
# 最终回答切片大小（模拟流式输出）
FINAL_ANSWER_CHUNK_SIZE = 80
# 持久化的对话标题最大长度
CONVERSATION_TITLE_MAX_LEN = 50


# ============== SSE 事件辅助 ==============
def sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """构造 SSE 事件字符串"""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ============== 工具定义（OpenAI Function Calling 格式）==============
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "搜索用户的笔记，返回匹配的笔记列表（仅含 id、标题和内容预览）。当用户想找某主题的笔记、回忆写过什么时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词（按笔记标题模糊匹配）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量上限，默认 5",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_note_content",
            "description": "按笔记 ID 获取笔记的完整内容（含 title、content、tags）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "笔记ID"}
                },
                "required": ["note_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_note",
            "description": "对一篇笔记做总结分析，返回 summary、strengths、weaknesses、suggestions。需要传入笔记全文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "笔记全文内容"}
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_note",
            "description": "根据主题生成新的学习笔记，返回 Markdown 格式的笔记内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "笔记主题"},
                    "keywords": {
                        "type": "string",
                        "description": "重点关注的关键词（可选）",
                    },
                    "word_count": {
                        "type": "integer",
                        "description": "字数要求，默认 600",
                        "default": 600,
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_note",
            "description": "将笔记内容翻译为指定语言，保留 Markdown 结构。需要传入笔记全文和目标语言代码。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "笔记全文内容"},
                    "target_lang": {
                        "type": "string",
                        "description": "目标语言代码：zh/en/ja/ko/fr/es",
                    },
                },
                "required": ["content", "target_lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "创建新笔记并保存到数据库。用户希望「保存为笔记」「加入我的笔记」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "笔记标题"},
                    "content": {
                        "type": "string",
                        "description": "笔记内容（Markdown 或 HTML）",
                    },
                    "tags": {
                        "type": "string",
                        "description": "标签（逗号分隔，可选）",
                    },
                },
                "required": ["title", "content"],
            },
        },
    },
]


# ============== 工具实现 ==============
async def _tool_search_notes(
    db: AsyncSession, user_id: int, args: Dict[str, Any]
) -> Dict[str, Any]:
    from app.crud import note as crud_note

    query = str(args.get("query") or "")
    limit = int(args.get("limit") or 5)
    limit = max(1, min(limit, 20))
    notes = await crud_note.search_notes(
        db, user_id=user_id, keyword=query, skip=0, limit=limit
    )
    return {
        "count": len(notes),
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "preview": (n.content or "")[:120],
                "tags": n.tags,
            }
            for n in notes
        ],
    }


async def _tool_get_note_content(
    db: AsyncSession, user_id: int, args: Dict[str, Any]
) -> Dict[str, Any]:
    from app.crud import note as crud_note

    note_id = int(args.get("note_id") or 0)
    if note_id <= 0:
        return {"error": "note_id 必须为正整数"}
    note = await crud_note.get_note(db, note_id=note_id, user_id=user_id)
    if not note:
        return {"error": f"笔记 {note_id} 不存在"}
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
    }


async def _tool_summarize_note(
    db_user: UserDB, args: Dict[str, Any]
) -> Dict[str, Any]:
    content = str(args.get("content") or "")
    if not content.strip():
        return {"error": "content 不能为空"}
    from app.services.note_analyzer import analyze_note

    result = await analyze_note(content, db_user=db_user)
    return result


async def _tool_generate_note(
    db_user: UserDB, args: Dict[str, Any]
) -> Dict[str, Any]:
    topic = str(args.get("topic") or "")
    if not topic.strip():
        return {"error": "topic 不能为空"}
    keywords = args.get("keywords")
    word_count = int(args.get("word_count") or 600)
    from app.services.note_generator import generate_note_stream

    parts: List[str] = []
    async for chunk in generate_note_stream(
        topic=topic,
        keyword=keywords if isinstance(keywords, str) else None,
        reference_notes=None,
        images=None,
        word_count=word_count,
        db_user=db_user,
    ):
        parts.append(chunk)
    return {"content": "".join(parts)}


async def _tool_translate_note(
    db_user: UserDB, args: Dict[str, Any]
) -> Dict[str, Any]:
    content = str(args.get("content") or "")
    target_lang = str(args.get("target_lang") or "").strip().lower()
    if not content.strip():
        return {"error": "content 不能为空"}
    if not target_lang:
        return {"error": "target_lang 不能为空"}
    from app.services.note_translator import translate_note_stream

    parts: List[str] = []
    async for chunk in translate_note_stream(content, target_lang, db_user=db_user):
        parts.append(chunk)
    return {"content": "".join(parts)}


async def _tool_create_note(
    db: AsyncSession, user_id: int, args: Dict[str, Any]
) -> Dict[str, Any]:
    from app.crud import note as crud_note

    title = str(args.get("title") or "").strip()
    content = str(args.get("content") or "")
    tags = args.get("tags")
    if not title or not content:
        return {"error": "title 和 content 不能为空"}
    existing = await crud_note.get_note_by_title(db, user_id=user_id, title=title)
    if existing:
        return {"error": f"标题「{title}」已存在，请换一个标题"}
    note = await crud_note.create_note(
        db,
        user_id=user_id,
        title=title,
        content=content,
        tags=tags if isinstance(tags, str) else None,
        is_favorite=True,
    )
    return {"id": note.id, "title": note.title, "created": True}


# ============== 工具调度 ==============
async def _execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    *,
    db: AsyncSession,
    db_user: UserDB,
) -> Dict[str, Any]:
    """执行工具调用，返回字典结果"""
    try:
        if tool_name == "search_notes":
            return await _tool_search_notes(db, db_user.id, args)
        if tool_name == "get_note_content":
            return await _tool_get_note_content(db, db_user.id, args)
        if tool_name == "summarize_note":
            return await _tool_summarize_note(db_user, args)
        if tool_name == "generate_note":
            return await _tool_generate_note(db_user, args)
        if tool_name == "translate_note":
            return await _tool_translate_note(db_user, args)
        if tool_name == "create_note":
            return await _tool_create_note(db, db_user.id, args)
        return {"error": f"未知工具：{tool_name}"}
    except Exception as e:
        logger.exception(f"工具 {tool_name} 执行失败")
        return {"error": f"工具执行失败：{str(e)}"}


def _truncate_tool_result(result: Any) -> str:
    """工具结果转 JSON 字符串，过长则截断"""
    try:
        text = json.dumps(result, ensure_ascii=False)
    except Exception:
        text = str(result)
    if len(text) > MAX_TOOL_RESULT_CHARS:
        text = text[:MAX_TOOL_RESULT_CHARS] + "...（结果过长，已截断）"
    return text


def _build_messages(
    message: str, history: Optional[List[Any]] = None
) -> List[Dict[str, Any]]:
    """合并 system、整理 history，得到发给模型的 messages（含末尾 user）"""
    system_extras: List[str] = []
    conversation: List[Dict[str, Any]] = []

    for msg in (history or [])[-10:]:
        if isinstance(msg, dict):
            role = str(msg.get("role") or "user")
            content = str(msg.get("content") or "")
        elif hasattr(msg, "model_dump"):
            d = msg.model_dump()
            role = str(d.get("role") or "user")
            content = str(d.get("content") or "")
        else:
            role = "user"
            content = str(getattr(msg, "content", "") or "")
        if role == "system":
            if content:
                system_extras.append(content)
            continue
        if role not in ("user", "assistant"):
            role = "user"
        conversation.append({"role": role, "content": content})

    system_content = AGENT_SYSTEM_PROMPT
    if system_extras:
        system_content += "\n\n# 附加上下文\n" + "\n\n".join(system_extras)

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_content}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": message})
    return messages


def _looks_like_tools_unsupported(exc: Exception) -> bool:
    """判断异常是否表明模型不支持 tools 参数"""
    s = str(exc).lower()
    keywords = (
        "tool",
        "function",
        "not support",
        "unsupported",
        "unrecognized",
        "unknown argument",
        "unknown parameter",
        "400",
    )
    return any(k in s for k in keywords) and "401" not in s and "auth" not in s


async def _fallback_plain_stream(
    client, model: str, messages: List[Dict[str, Any]]
) -> AsyncIterator[str]:
    """降级：模型不支持 tools 时，普通流式对话（不持久化，仅用于无 conversation_id 场景）"""
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content is not None:
                yield sse_event("delta", {"text": delta.content})
        yield sse_event("done", {"finish_reason": "stop"})
    except Exception as e:
        logger.exception("降级流式对话失败")
        yield sse_event("error", {"message": format_llm_error("AI助手", e)})


def _emit_final_answer(text: str) -> AsyncIterator[str]:
    """将完整回答按切片模拟流式输出"""
    if not text:
        text = "抱歉，我暂时无法回答这个问题。"
    # 按段落切片，每段最多 FINAL_ANSWER_CHUNK_SIZE 字符
    chunks = []
    for i in range(0, len(text), FINAL_ANSWER_CHUNK_SIZE):
        chunks.append(text[i : i + FINAL_ANSWER_CHUNK_SIZE])

    async def _gen():
        for chunk in chunks:
            yield sse_event("delta", {"text": chunk})
        yield sse_event("done", {"finish_reason": "stop"})

    return _gen()


# ============== 持久化辅助 ==============
def _make_conversation_title(message: str) -> str:
    """从用户首条消息生成对话标题（取前若干字符，去除多余空白）"""
    text = (message or "").strip().replace("\n", " ")
    if not text:
        return "新对话"
    if len(text) <= CONVERSATION_TITLE_MAX_LEN:
        return text
    return text[:CONVERSATION_TITLE_MAX_LEN] + "…"


async def _persist_messages(
    *,
    db: AsyncSession,
    user_id: int,
    conversation_id: Optional[int],
    user_message: str,
    assistant_message: str,
    first_message: str,
) -> Optional[int]:
    """将 user 消息和 assistant 回复持久化到 ai_messages 表。

    - 若 conversation_id 为空，则先用首条消息创建对话，再写入两条消息。
    - 若 conversation_id 已存在，则仅追加两条消息，并刷新对话的 updated_at。
    - 出错时仅记录日志并返回 None，不阻断主流程。

    返回持久化后的 conversation_id（失败时返回 None）。
    """
    from sqlalchemy import update
    from sqlalchemy.sql import func
    from app.models.ai_conversation import AIConversationDB, AIMessageDB

    try:
        if conversation_id is None:
            # 创建新对话
            conv = AIConversationDB(
                user_id=user_id,
                title=_make_conversation_title(first_message),
            )
            db.add(conv)
            await db.flush()
            conversation_id = conv.id
        else:
            # 已存在对话：刷新 updated_at
            await db.execute(
                update(AIConversationDB)
                .where(
                    AIConversationDB.id == conversation_id,
                    AIConversationDB.user_id == user_id,
                )
                .values(updated_at=func.now())
            )

        # 写入 user 消息
        db.add(
            AIMessageDB(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
            )
        )
        # 写入 assistant 回复
        db.add(
            AIMessageDB(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_message,
            )
        )
        await db.commit()
        return conversation_id
    except Exception as e:
        logger.exception(f"持久化对话消息失败 conversation_id={conversation_id}: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        return None


# ============== 主流程 ==============
async def agent_chat_stream(
    message: str,
    history: Optional[List[Any]] = None,
    *,
    db: AsyncSession,
    db_user: UserDB,
    conversation_id: Optional[int] = None,
    persist: bool = True,
    use_multi_agent: bool = True,
) -> AsyncIterator[str]:
    """
    Agent 流式对话：基于多 Agent 协作架构 + Function Calling 工具调用。

    架构：
    - Coordinator 调度员分析用户意图，决定调用哪个专业 Agent
    - 各专业 Agent（搜索/总结/生成/翻译/思维导图/通用）用自己的 prompt 和工具集执行任务
    - use_multi_agent=False 时走旧的单 Agent 模式（向后兼容）

    输出 SSE 事件流（每个事件为 `data: {json}\\n\\n`）：
    - agent_start：某个 Agent 开始工作
    - agent_end：某个 Agent 结束工作
    - thinking：模型决定调用工具前的思考过程
    - tool_start：开始执行工具
    - tool_end：工具执行结束（含结果）
    - delta：最终回答的文本增量
    - done：完成（携带 conversation_id 便于前端刷新）
    - error：错误

    持久化：
    - 当 persist=True 且 conversation_id 不为空时，将 user/assistant 消息写入 ai_messages 表。
    - 当 persist=True 且 conversation_id 为空时，会自动创建新对话并返回其 id。
    - 当 persist=False 时，不进行任何数据库写入（兼容旧用法）。
    """
    # 收集最终回答文本（用于持久化）
    final_answer_parts: List[str] = []
    error_occurred = False

    if use_multi_agent:
        # 多 Agent 模式：走 Coordinator
        from app.services.agent.coordinator import coordinator_run

        async for evt in coordinator_run(
            message, history,
            db=db, db_user=db_user,
            enable_multi_agent=True,
        ):
            # 解析事件，收集最终回答
            try:
                payload = json.loads(evt[len("data: "):].strip())
            except Exception:
                payload = {}

            evt_type = payload.get("type")

            if evt_type == "delta":
                final_answer_parts.append(payload.get("text", ""))
            elif evt_type == "error":
                error_occurred = True
            elif evt_type == "done" and persist:
                # 拦截 done 事件，先持久化再带上 conversation_id
                final_text = "".join(final_answer_parts).strip()
                cid = await _persist_messages(
                    db=db,
                    user_id=db_user.id,
                    conversation_id=conversation_id,
                    user_message=message,
                    assistant_message=final_text,
                    first_message=message,
                )
                yield sse_event(
                    "done",
                    {
                        "finish_reason": payload.get("finish_reason", "stop"),
                        "conversation_id": cid,
                    },
                )
                continue

            yield evt
        return

    # ========== 以下为旧的单 Agent 模式（向后兼容，use_multi_agent=False 时走这里）==========
    messages = _build_messages(message, history)

    try:
        client, model = openai_client_and_model_for_user(db_user)
    except Exception as e:
        yield sse_event("error", {"message": format_llm_error("AI助手", e)})
        return

    use_tools = True

    # 包装 delta/done 事件，便于在结束时持久化
    async def _wrap_final_stream(final_text: str) -> AsyncIterator[str]:
        """输出最终回答切片，并在结束时持久化（若启用）"""
        # 复用 _emit_final_answer 的切片逻辑
        async for evt in _emit_final_answer(final_text):
            # 拦截 done 事件，先持久化再带上 conversation_id
            try:
                payload = json.loads(evt[len("data: "):].strip())
            except Exception:
                payload = {}
            if payload.get("type") == "done" and persist:
                cid = await _persist_messages(
                    db=db,
                    user_id=db_user.id,
                    conversation_id=conversation_id,
                    user_message=message,
                    assistant_message=final_text,
                    first_message=message,
                )
                yield sse_event(
                    "done",
                    {
                        "finish_reason": payload.get("finish_reason", "stop"),
                        "conversation_id": cid,
                    },
                )
            else:
                yield evt

    for round_idx in range(MAX_TOOL_ROUNDS):
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 2048,
            }
            if use_tools:
                kwargs["tools"] = TOOLS_DEFINITION
                kwargs["tool_choice"] = "required"  # 强制调用工具，提高工具调用成功率
            response = await client.chat.completions.create(**kwargs)
        except Exception as e:
            # 模型可能不支持 tools 参数，降级为普通流式对话
            if use_tools and _looks_like_tools_unsupported(e):
                logger.warning(
                    f"模型 {model} 不支持 tools 参数，降级为普通流式对话：{e}"
                )
                use_tools = False
                # 降级流式也需要持久化最终回答
                async for evt in _fallback_plain_stream_with_persist(
                    client, model, messages,
                    db=db, user_id=db_user.id,
                    conversation_id=conversation_id,
                    user_message=message,
                ):
                    yield evt
                return
            logger.exception("agent_chat_stream 调用模型失败")
            yield sse_event("error", {"message": format_llm_error("AI助手", e)})
            return

        if not response.choices:
            yield sse_event("error", {"message": "LLM 返回空 choices"})
            return

        choice = response.choices[0]
        msg = choice.message

        # 没有工具调用：msg.content 就是最终回答，直接输出（不要作为 thinking 推）
        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            final_text = (msg.content or "").strip()
            async for evt in _wrap_final_stream(final_text):
                yield evt
            return

        # 有工具调用：msg.content 是思考过程
        if msg.content and msg.content.strip():
            yield sse_event("thinking", {"text": msg.content.strip()})

        # 有工具调用，将 assistant 消息（含 tool_calls）追加到 messages
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )

        # 逐个执行工具
        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}

            yield sse_event(
                "tool_start",
                {"id": tc.id, "name": tool_name, "args": args},
            )

            result = await _execute_tool(
                tool_name, args, db=db, db_user=db_user
            )
            result_text = _truncate_tool_result(result)

            # 推送 tool_end（事件中只携带不超过上限的结果摘要）
            try:
                result_json = json.dumps(result, ensure_ascii=False)
            except Exception:
                result_json = str(result)
            if len(result_json) <= MAX_TOOL_RESULT_CHARS:
                tool_end_data = {"id": tc.id, "name": tool_name, "result": result}
            else:
                tool_end_data = {
                    "id": tc.id,
                    "name": tool_name,
                    "result": {
                        "truncated": True,
                        "preview": result_text[:200],
                    },
                }
            yield sse_event("tool_end", tool_end_data)

            # 将工具结果追加到 messages（用截断后的文本，避免上下文爆炸）
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                }
            )

        # 进入下一轮：让模型基于工具结果继续判断（可能再调工具，也可能直接回答）
        # 最后一轮强制要求模型不再调用工具，直接生成最终回答
        if round_idx == MAX_TOOL_ROUNDS - 1:
            messages.append(
                {
                    "role": "system",
                    "content": "已经达到工具调用上限，请直接基于现有信息给出最终回答，不要再调用工具。",
                }
            )

    # 循环正常结束（模型在 MAX_TOOL_ROUNDS 内未输出最终回答），强制生成最终回答
    try:
        final_response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
        )
        final_text = (
            (final_response.choices[0].message.content or "").strip()
            or "抱歉，工具调用次数已达上限，未能给出最终回答。"
        )
        async for evt in _wrap_final_stream(final_text):
            yield evt
    except Exception as e:
        logger.exception("最终回答生成失败")
        yield sse_event("error", {"message": format_llm_error("AI助手", e)})


async def _fallback_plain_stream_with_persist(
    client,
    model: str,
    messages: List[Dict[str, Any]],
    *,
    db: AsyncSession,
    user_id: int,
    conversation_id: Optional[int],
    user_message: str,
) -> AsyncIterator[str]:
    """降级流式对话的持久化版本：边流式输出边积累最终文本，结束时持久化"""
    parts: List[str] = []
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content is not None:
                parts.append(delta.content)
                yield sse_event("delta", {"text": delta.content})
        final_text = "".join(parts).strip()
        cid = await _persist_messages(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_message=final_text,
            first_message=user_message,
        )
        yield sse_event("done", {"finish_reason": "stop", "conversation_id": cid})
    except Exception as e:
        logger.exception("降级流式对话失败")
        yield sse_event("error", {"message": format_llm_error("AI助手", e)})
