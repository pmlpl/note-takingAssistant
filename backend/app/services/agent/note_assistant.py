"""NoteAssistant：统一的笔记助手

这是唯一的主 Agent，包含所有工具。LLM 通过 Function Calling 直接选择调用哪个工具。
每个工具标注所属的子 Agent，前端显示时展示当前使用的是哪个子 Agent 的工具。

架构：
- 主 Agent：Note助手（显示在聊天界面）
- 子 Agent：搜索/总结/生成/翻译/思维导图（通过工具调用时显示）
- 工具：search_notes, get_note_content, summarize_note, generate_note, translate_note, create_note
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDB
from app.services.agent.base import BaseAgent, sse_event

logger = logging.getLogger(__name__)

CONVERSATION_TITLE_MAX_LEN = 50


SUB_AGENTS = {
    "search": {"name": "搜索", "emoji": "🔍", "display_name": "搜索专家"},
    "summarize": {"name": "总结", "emoji": "📝", "display_name": "总结专家"},
    "generate": {"name": "生成", "emoji": "✍️", "display_name": "生成专家"},
    "translate": {"name": "翻译", "emoji": "🌐", "display_name": "翻译专家"},
    "mindmap": {"name": "思维导图", "emoji": "🧠", "display_name": "思维导图专家"},
}

TOOL_TO_SUB_AGENT = {
    "search_notes": "search",
    "get_note_content": None,
    "summarize_note": "summarize",
    "generate_note": "generate",
    "translate_note": "translate",
    "create_note": "generate",
}


NOTE_ASSISTANT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "搜索用户的笔记，返回匹配的笔记列表（仅含 id、标题和内容预览）。支持标题/正文关键词与语义检索。当用户想找某主题的笔记、回忆写过什么时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词（标题/正文模糊匹配 + 语义检索）"},
                    "limit": {"type": "integer", "description": "返回数量上限，默认 5", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_note_content",
            "description": "按笔记 ID 获取笔记的完整内容（含 title、content、tags）。用户提到某篇笔记但未提供内容时调用。",
            "parameters": {
                "type": "object",
                "properties": {"note_id": {"type": "integer", "description": "笔记ID"}},
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
                "properties": {"content": {"type": "string", "description": "笔记全文内容"}},
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
                    "keywords": {"type": "string", "description": "重点关注的关键词（可选）"},
                    "word_count": {"type": "integer", "description": "字数要求，默认 600", "default": 600},
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
                    "target_lang": {"type": "string", "description": "目标语言代码：zh/en/ja/ko/fr/es"},
                },
                "required": ["content", "target_lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "创建新笔记并保存到数据库。用户希望「保存为笔记」「加入我的笔记」「保存到我的笔记」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "笔记标题"},
                    "content": {"type": "string", "description": "笔记内容（Markdown 或 HTML）"},
                    "tags": {"type": "string", "description": "标签（逗号分隔，可选）"},
                },
                "required": ["title", "content"],
            },
        },
    },
]


NOTE_ASSISTANT_SYSTEM_PROMPT = """你是 NoteMind「笔记助手」，一个帮助用户管理和处理学习笔记的智能助手。

## 你的职责
- 理解用户的需求，选择合适的工具完成任务
- 搜索笔记、总结笔记、生成笔记、翻译笔记、创建思维导图
- 将工具执行结果整理成友好的回答呈现给用户

## 可用工具

| 工具 | 功能 | 适用场景 |
|------|------|---------|
| search_notes | 搜索笔记 | 用户想找某主题的笔记、回忆写过什么 |
| get_note_content | 获取笔记完整内容 | 用户提到某篇笔记但未提供内容 |
| summarize_note | 总结笔记 | 用户要求总结、概括、提炼要点 |
| generate_note | 生成笔记 | 用户要求写一篇、创作、生成新笔记 |
| translate_note | 翻译笔记 | 用户要求翻译、翻译成其他语言 |
| create_note | 保存笔记 | 用户要求保存到我的笔记、加入我的笔记 |

## 工作原则
1. 分析用户意图，选择最合适的工具
2. 先搜索再获取：需要全文时先用 search_notes 找到笔记，再用 get_note_content 获取
3. 先获取再处理：总结、翻译、思维导图需要先获取笔记内容
4. 用户确认原则：在调用工具前，先向用户说明你要做什么，等待用户确认后再执行。例如："我将搜索关键词'机器学习'的笔记，确认搜索吗？"
5. 格式保真：翻译和总结时保留 Markdown 格式
6. 清晰输出：工具执行结果用清晰的格式呈现给用户
7. 诚实告知：没有找到匹配笔记时直接说明

## 回答风格
- 亲切、耐心、有鼓励性
- 使用清晰的 Markdown 格式
- 适当使用表情符号增加亲和力
- 简洁明了，不要废话
"""


# ============== 工具实现（唯一一份） ==============
async def _tool_search_notes(db: AsyncSession, user_id: int, args: dict[str, Any], db_user: UserDB) -> dict[str, Any]:
    from app.services import note_rag

    query = str(args.get("query") or "")
    limit = int(args.get("limit") or 5)
    limit = max(1, min(limit, 20))
    notes, _ = await note_rag.hybrid_search_notes(db, db_user=db_user, keyword=query, skip=0, limit=limit)
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
    db: AsyncSession, user_id: int, args: dict[str, Any], db_user: UserDB
) -> dict[str, Any]:
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


async def _tool_summarize_note(db: AsyncSession, user_id: int, args: dict[str, Any], db_user: UserDB) -> dict[str, Any]:
    content = str(args.get("content") or "")
    if not content.strip():
        return {"error": "content 不能为空"}
    from app.services.note_analyzer import analyze_note

    result = await analyze_note(content, db_user=db_user)
    return result


async def _tool_generate_note(db: AsyncSession, user_id: int, args: dict[str, Any], db_user: UserDB) -> dict[str, Any]:
    topic = str(args.get("topic") or "")
    if not topic.strip():
        return {"error": "topic 不能为空"}
    keywords = args.get("keywords")
    word_count = int(args.get("word_count") or 600)
    from app.services.note_generator import generate_note_stream

    parts: list[str] = []
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


async def _tool_translate_note(db: AsyncSession, user_id: int, args: dict[str, Any], db_user: UserDB) -> dict[str, Any]:
    content = str(args.get("content") or "")
    target_lang = str(args.get("target_lang") or "").strip().lower()
    if not content.strip():
        return {"error": "content 不能为空"}
    if not target_lang:
        return {"error": "target_lang 不能为空"}
    from app.services.note_translator import translate_note_stream

    parts: list[str] = []
    async for chunk in translate_note_stream(content, target_lang, db_user=db_user):
        parts.append(chunk)
    return {"content": "".join(parts)}


async def _tool_create_note(db: AsyncSession, user_id: int, args: dict[str, Any], db_user: UserDB) -> dict[str, Any]:
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


TOOL_HANDLERS = {
    "search_notes": _tool_search_notes,
    "get_note_content": _tool_get_note_content,
    "summarize_note": _tool_summarize_note,
    "generate_note": _tool_generate_note,
    "translate_note": _tool_translate_note,
    "create_note": _tool_create_note,
}


class NoteAssistant(BaseAgent):
    name = "note_assistant"
    display_name = "Note助手"
    emoji = "📒"
    system_prompt = NOTE_ASSISTANT_SYSTEM_PROMPT
    tools_definition = NOTE_ASSISTANT_TOOLS
    tool_handlers = TOOL_HANDLERS

    async def run(
        self,
        message: str,
        history: Optional[list[Any]] = None,
        *,
        db: AsyncSession,
        db_user: UserDB,
    ) -> AsyncIterator[str]:
        yield sse_event(
            "agent_start",
            {
                "agent": self.name,
                "display_name": self.display_name,
                "emoji": self.emoji,
                "reason": "开始处理您的请求",
            },
        )

        async for evt in super().run(message, history, db=db, db_user=db_user):
            try:
                payload = json.loads(evt[len("data: ") :].strip())
                event_type = payload.get("type")

                if event_type == "tool_start":
                    tool_name = payload.get("name", "")
                    sub_agent_key = TOOL_TO_SUB_AGENT.get(tool_name)
                    if sub_agent_key and SUB_AGENTS.get(sub_agent_key):
                        sub_agent = SUB_AGENTS[sub_agent_key]
                        yield sse_event(
                            "sub_agent_start",
                            {
                                "agent": sub_agent_key,
                                "display_name": sub_agent["display_name"],
                                "emoji": sub_agent["emoji"],
                                "tool": tool_name,
                            },
                        )
                elif event_type == "tool_end":
                    tool_name = payload.get("name", "")
                    sub_agent_key = TOOL_TO_SUB_AGENT.get(tool_name)
                    if sub_agent_key and SUB_AGENTS.get(sub_agent_key):
                        sub_agent = SUB_AGENTS[sub_agent_key]
                        yield sse_event(
                            "sub_agent_end",
                            {
                                "agent": sub_agent_key,
                                "display_name": sub_agent["display_name"],
                                "emoji": sub_agent["emoji"],
                                "tool": tool_name,
                            },
                        )
            except Exception:
                pass

            yield evt

        yield sse_event("agent_end", {"agent": self.name, "display_name": self.display_name})


# ============== 持久化与对外入口 ==============
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

    返回持久化后的 conversation_id（失败时返回 None），出错不阻断主流程。
    """
    from sqlalchemy import update
    from sqlalchemy.sql import func

    from app.models.ai_conversation import AIConversationDB, AIMessageDB

    try:
        if conversation_id is None:
            conv = AIConversationDB(
                user_id=user_id,
                title=_make_conversation_title(first_message),
            )
            db.add(conv)
            await db.flush()
            conversation_id = conv.id
        else:
            await db.execute(
                update(AIConversationDB)
                .where(
                    AIConversationDB.id == conversation_id,
                    AIConversationDB.user_id == user_id,
                )
                .values(updated_at=func.now())
            )

        db.add(
            AIMessageDB(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
            )
        )
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


async def agent_chat_stream(
    message: str,
    history: Optional[list[Any]] = None,
    *,
    db: AsyncSession,
    db_user: UserDB,
    conversation_id: Optional[int] = None,
    persist: bool = True,
) -> AsyncIterator[str]:
    """Agent 流式对话：单 Agent（NoteAssistant）+ Function Calling 工具链。

    输出 SSE 事件流（每个事件为 `data: {json}\n\n`）：
    - agent_start / agent_end：主 Agent 开始/结束
    - sub_agent_start / sub_agent_end：工具对应子 Agent 开始/结束
    - thinking / tool_start / tool_end：思考与工具调用
    - delta / done / error：最终回答增量、完成（携带 conversation_id）、错误

    持久化：persist=True 时在 done 前将 user/assistant 消息写入 ai_messages 表。
    """
    final_answer_parts: list[str] = []

    agent = NoteAssistant()
    async for evt in agent.run(message, history, db=db, db_user=db_user):
        try:
            payload = json.loads(evt[len("data: ") :].strip())
        except Exception:
            payload = {}

        if payload.get("type") == "delta":
            final_answer_parts.append(payload.get("text", ""))
        elif payload.get("type") == "done" and persist:
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
