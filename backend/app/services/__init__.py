"""
AI 服务模块
提供 AI 相关的功能服务（异步协程，须在 async 上下文中 await）
"""
from .note_generator import generate_note_stream
from .note_analyzer import analyze_note
from .note_translator import translate_note_stream
from .chat_service import chat_with_ai, chat_with_ai_stream

__all__ = [
    'generate_note_stream',
    'analyze_note',
    'translate_note_stream',
    'chat_with_ai',
    'chat_with_ai_stream',
]
