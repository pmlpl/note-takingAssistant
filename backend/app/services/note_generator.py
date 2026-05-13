"""
笔记生成服务
负责 AI 生成笔记内容（异步 OpenAI 客户端，避免阻塞事件循环）
"""
from typing import Any, AsyncIterator, List, Optional

from app.core.config import settings
from .openai_client import async_openai_client
from .prompts import NOTE_GENERATION_SYSTEM_PROMPT


def _normalize_reference_notes(reference_notes: Optional[List[Any]]) -> List[dict]:
    if not reference_notes:
        return []
    out: List[dict] = []
    for note in reference_notes:
        if isinstance(note, dict):
            out.append(note)
        elif hasattr(note, "model_dump"):
            out.append(note.model_dump())
        else:
            out.append({
                "filename": getattr(note, "filename", "未知文件"),
                "content": getattr(note, "content", ""),
            })
    return out


def _build_generation_prompt(
    topic: str,
    keyword: Optional[str] = None,
    reference_notes: Optional[List[dict]] = None,
    word_count: int = 600,
) -> str:
    user_prompt = f"请为主题「{topic}」生成一篇学习笔记。"

    if keyword:
        user_prompt += f"\n\n重点关注的关键词：{keyword}"

    if reference_notes and len(reference_notes) > 0:
        user_prompt += "\n\n以下是参考材料，请结合这些内容生成笔记：\n"
        for i, note in enumerate(reference_notes, 1):
            user_prompt += f"\n【参考资料{i} - {note.get('filename', '未知文件')}】\n"
            content = note.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "...（内容过长，已截断）"
            user_prompt += content

    user_prompt += "\n\n请按照以下结构生成笔记：\n"
    user_prompt += "1. 核心概念介绍\n"
    user_prompt += "2. 关键知识点详解（分点阐述）\n"
    user_prompt += "3. 实际应用或示例\n"
    user_prompt += "4. 总结与复习要点\n"

    min_words = max(300, word_count - 100)
    max_words = word_count + 100
    user_prompt += f"\n字数要求：{min_words}-{max_words}字左右\n"

    return user_prompt


async def generate_note_stream(
    topic: str,
    keyword: Optional[str] = None,
    reference_notes: Optional[List[Any]] = None,
    images: Optional[list] = None,
    word_count: int = 600,
) -> AsyncIterator[str]:
    """流式生成笔记内容（异步生成器）。"""
    normalized = _normalize_reference_notes(reference_notes)
    user_prompt = _build_generation_prompt(topic, keyword, normalized, word_count)

    try:
        stream = await async_openai_client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": NOTE_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=word_count * 3,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content is not None:
                yield delta.content
    except Exception as e:
        raise Exception(f"AI生成笔记失败：{str(e)}") from e


async def generate_note(
    topic: str,
    keyword: Optional[str] = None,
    reference_notes: Optional[List[Any]] = None,
    images: Optional[list] = None,
    word_count: int = 600,
) -> str:
    """根据主题、关键词、参考笔记等生成笔记正文。"""
    normalized = _normalize_reference_notes(reference_notes)
    user_prompt = _build_generation_prompt(topic, keyword, normalized, word_count)

    try:
        response = await async_openai_client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": NOTE_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=word_count * 3,
        )
        text = response.choices[0].message.content
        return (text or "").strip()
    except Exception as e:
        raise Exception(f"AI生成笔记失败：{str(e)}") from e
