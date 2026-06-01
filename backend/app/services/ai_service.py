"""
兼容层：保留历史命名 ai_* 与提示词导出，实现委托给异步服务模块。

新代码请使用：
- app.services.note_generator（generate_note_stream）
- app.services.note_analyzer（analyze_note）
- app.services.chat_service（chat_with_ai）
"""
from .prompts import (
    CHAT_SYSTEM_PROMPT,
    NOTE_ANALYSIS_SYSTEM_PROMPT,
    NOTE_GENERATION_SYSTEM_PROMPT,
)
from .chat_service import chat_with_ai
from .note_analyzer import analyze_note
from .note_generator import generate_note_stream


async def ai_generate_note(**kwargs):
    """聚合流式生成结果为单字符串（与旧 generate_note 返回形态一致）。"""
    parts: list[str] = []
    async for chunk in generate_note_stream(**kwargs):
        parts.append(chunk)
    return "".join(parts).strip()


ai_generate_note_stream = generate_note_stream
ai_summarize_note = analyze_note
ai_chat = chat_with_ai

__all__ = [
    "CHAT_SYSTEM_PROMPT",
    "NOTE_ANALYSIS_SYSTEM_PROMPT",
    "NOTE_GENERATION_SYSTEM_PROMPT",
    "ai_chat",
    "ai_generate_note",
    "ai_generate_note_stream",
    "ai_summarize_note",
]
