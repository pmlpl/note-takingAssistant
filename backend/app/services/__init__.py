"""
AI 服务模块
提供 AI 相关的功能服务（异步协程，须在 async 上下文中 await）
"""
from .prompts import NOTE_GENERATION_SYSTEM_PROMPT, NOTE_ANALYSIS_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT
from .note_generator import generate_note_stream, generate_note
from .note_analyzer import analyze_note
from .note_translator import translate_note
from .chat_service import chat_with_ai

__all__ = [
    'generate_note_stream',
    'generate_note',
    'analyze_note',
    'translate_note',
    'chat_with_ai'
]
