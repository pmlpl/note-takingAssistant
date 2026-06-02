"""
AI 聊天服务
负责 AI 对话功能（异步 OpenAI 客户端）
"""
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.utils.llm_errors import format_llm_error
from .prompts import CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _message_as_dict(msg: Any) -> Dict[str, str]:
    """将 Pydantic 模型或 dict 规范为 {role, content}。"""
    if isinstance(msg, dict):
        return {
            "role": str(msg.get("role") or "user"),
            "content": str(msg.get("content") or ""),
        }
    if hasattr(msg, "model_dump"):
        d = msg.model_dump()
        return {
            "role": str(d.get("role") or "user"),
            "content": str(d.get("content") or ""),
        }
    return {
        "role": str(getattr(msg, "role", None) or "user"),
        "content": str(getattr(msg, "content", None) or ""),
    }


def _build_chat_messages(message: str, history: Optional[List[Any]] = None) -> List[Dict[str, str]]:
    """合并 system、整理 history，得到发给模型的 messages（含末尾 user）。"""
    system_extras: List[str] = []
    conversation: List[Dict[str, str]] = []

    for msg in (history or [])[-10:]:
        row = _message_as_dict(msg)
        role, content = row["role"], row["content"]
        if role == "system":
            if content:
                system_extras.append(content)
            continue
        if role not in ("user", "assistant"):
            role = "user"
        conversation.append({"role": role, "content": content})

    system_content = CHAT_SYSTEM_PROMPT
    if system_extras:
        system_content += "\n\n# 附加上下文\n" + "\n\n".join(system_extras)

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": message})
    return messages


async def chat_with_ai(
    message: str,
    history: Optional[List[Any]] = None,
    *,
    db_user: UserDB,
) -> str:
    """
    AI 对话功能，支持上下文聊天。

    将 history 中多条 system 合并进唯一一条 system，避免 LM Studio 等
    OpenAI 兼容端点对「多个 system」返回错误。
    """
    messages = _build_chat_messages(message, history)

    try:
        client, model = openai_client_and_model_for_user(db_user)
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        if not response.choices:
            raise RuntimeError("LLM 返回空 choices")
        text = response.choices[0].message.content
        return (text or "").strip()
    except Exception as e:
        logger.exception("chat_with_ai 调用失败")
        raise Exception(format_llm_error("AI对话", e)) from e


async def chat_with_ai_stream(
    message: str,
    history: Optional[List[Any]] = None,
    *,
    db_user: UserDB,
) -> AsyncIterator[str]:
    """流式对话：与 chat_with_ai 相同的 messages 拼装，增量产出 assistant 文本。"""
    messages = _build_chat_messages(message, history)

    try:
        client, model = openai_client_and_model_for_user(db_user)
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
                yield delta.content
    except Exception as e:
        logger.exception("chat_with_ai_stream 调用失败")
        raise Exception(format_llm_error("AI对话", e)) from e
