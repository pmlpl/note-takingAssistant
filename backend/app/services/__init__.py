"""
AI 服务模块
提供 AI 相关的功能服务（异步协程，须在 async 上下文中 await）
"""

from .agent.note_assistant import agent_chat_stream
from .chat_service import chat_with_ai, chat_with_ai_stream
from .note_analyzer import analyze_note
from .note_generator import generate_note_stream
from .note_translator import translate_note_stream

__all__ = [
    "agent_chat_stream",
    "analyze_note",
    "chat_with_ai",
    "chat_with_ai_stream",
    "generate_note_stream",
    "translate_note_stream",
]
