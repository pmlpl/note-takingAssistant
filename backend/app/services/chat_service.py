"""
AI 聊天服务
负责 AI 对话功能（异步 OpenAI 客户端）
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from .openai_client import async_openai_client
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


async def chat_with_ai(message: str, history: Optional[List[Any]] = None) -> str:
    """
    AI 对话功能，支持上下文聊天。

    将 history 中多条 system 合并进唯一一条 system，避免 LM Studio 等
    OpenAI 兼容端点对「多个 system」返回错误。
    """
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

    try:
        response = await async_openai_client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        if not response.choices:
            raise RuntimeError("LLM 返回空 choices")
        text = response.choices[0].message.content
        return (text or "").strip()
    except Exception as e:
        logger.exception("chat_with_ai 调用失败")
        raise Exception(f"AI对话失败：{str(e)}") from e
