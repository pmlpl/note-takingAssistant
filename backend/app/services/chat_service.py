"""
AI 聊天服务
负责 AI 对话功能（异步 OpenAI 客户端）
"""
from typing import Any, List, Optional

from app.core.config import settings
from .openai_client import async_openai_client
from .prompts import CHAT_SYSTEM_PROMPT


async def chat_with_ai(message: str, history: Optional[List[Any]] = None) -> str:
    """
    AI 对话功能，支持上下文聊天。
    """
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

    if history:
        for msg in history[-10:]:
            if isinstance(msg, dict):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
            else:
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

    messages.append({"role": "user", "content": message})

    try:
        response = await async_openai_client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        text = response.choices[0].message.content
        return (text or "").strip()
    except Exception as e:
        raise Exception(f"AI对话失败：{str(e)}") from e
