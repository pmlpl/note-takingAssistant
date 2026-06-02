"""
笔记翻译：先将正文统一转为 Markdown（HTML 富文本先转换，避免截断 HTML 导致结构错乱），
再对 Markdown 做流式翻译；输出为 Markdown，由前端渲染。
"""
from __future__ import annotations

import re
from typing import Any, AsyncIterator, Dict

import html2text
from bs4 import BeautifulSoup

from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.services.prompts import NOTE_TRANSLATION_SYSTEM_PROMPT
from app.utils.llm_errors import format_llm_error

MAX_INPUT_CHARS = 8000

TARGET_LANGUAGE_LABELS: Dict[str, str] = {
    "zh": "Simplified Chinese (简体中文)",
    "en": "English",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "fr": "French (français)",
    "es": "Spanish (español)",
}

WATERMARK_MD = "\n\n---\n\n*由 笔记助手 翻译*"
WATERMARK_SNIPPET = "由 笔记助手 翻译"

_HTML_DETECTION = re.compile(
    r"<\s*/?\s*"
    r"(?:p|div|span|table|tr|td|th|img|br|h[1-6]|ul|ol|li|section|article|blockquote|"
    r"tbody|thead|tfoot|caption|colgroup|col|figure|figcaption|html|body)\b",
    re.IGNORECASE,
)


def looks_like_html_note(content: str) -> bool:
    s = (content or "").strip()
    if "<" not in s:
        return False
    return bool(_HTML_DETECTION.search(s))


def html_to_markdown(html: str) -> str:
    """将富文本 / Word 导入等 HTML 转为 Markdown，便于整篇流式翻译。"""
    raw = (html or "").strip()
    if not raw:
        return ""
    try:
        conv = html2text.HTML2Text()
        conv.body_width = 0
        conv.ignore_links = False
        conv.ignore_images = False
        conv.unicode_snob = True
        conv.mark_code = True
        out = conv.handle(raw).strip()
        if out:
            return out
    except Exception:
        pass
    soup = BeautifulSoup(raw, "html.parser")
    return soup.get_text("\n", strip=True)


def prepare_markdown_for_translation(content: str) -> tuple[str, bool, bool]:
    """
    返回 (送入模型的 Markdown, 是否由 HTML 转换而来, 是否因超长截断)。
    截断在「Markdown 化之后」进行，避免截断 HTML 破坏标签配对。
    """
    raw = (content or "").strip()
    if not raw:
        raise ValueError("内容为空")

    from_html = looks_like_html_note(raw)
    if from_html:
        md = html_to_markdown(raw)
    else:
        md = raw

    if not md.strip():
        raise ValueError("转换后内容为空")

    truncated = len(md) > MAX_INPUT_CHARS
    if truncated:
        md = md[:MAX_INPUT_CHARS]

    return md, from_html, truncated


async def translate_note_stream(
    content: str,
    target_lang: str,
    *,
    db_user: UserDB,
) -> AsyncIterator[str]:
    """
    流式翻译：输入可为 HTML 或 Markdown/纯文本；内部统一为 Markdown 再调用模型；
    产出为 Markdown 片段（最后含水印），供前端 `renderMarkdownToSafeHtml` 等渲染。
    """
    text, _from_html, _truncated = prepare_markdown_for_translation(content)

    lang_label = TARGET_LANGUAGE_LABELS.get(
        (target_lang or "").strip().lower(), target_lang
    )

    client, model = openai_client_and_model_for_user(db_user)

    user_prompt = f"""目标语言：{lang_label}

请翻译以下笔记全文（保持 Markdown 与代码块规则见系统说明）：

---
{text}
---"""

    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": NOTE_TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=8192,
        stream=True,
    )

    acc = ""
    try:
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content is not None:
                piece = delta.content
                acc += piece
                yield piece
    except Exception as e:
        raise RuntimeError(format_llm_error("AI翻译", e)) from e

    if WATERMARK_SNIPPET not in acc:
        yield WATERMARK_MD
