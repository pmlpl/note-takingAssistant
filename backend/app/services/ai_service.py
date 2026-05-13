"""
兼容层：保留历史命名 ai_* 与提示词导出，实现委托给异步服务模块。

新代码请使用：
- app.services.note_generator（generate_note / generate_note_stream）
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
from .note_generator import generate_note, generate_note_stream

# 异步别名（与实现相同对象，调用方须 await）
ai_generate_note = generate_note
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
