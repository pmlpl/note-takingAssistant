"""
笔记翻译：复用用户 LLM 配置（OpenAI 兼容）。
- Markdown：整篇翻译，保留 MD 结构。
- HTML（WangEditor / Word 导入等）：BeautifulSoup 仅替换文本节点，保留 img/table 等 DOM。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup, Comment, NavigableString

from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.services.prompts import (
    NOTE_HTML_SEGMENT_TRANSLATION_SYSTEM_PROMPT,
    NOTE_TRANSLATION_SYSTEM_PROMPT,
)

MAX_INPUT_CHARS = 8000
MAX_BATCH_CHARS = 3200
MAX_SEGMENTS_PER_BATCH = 45

TARGET_LANGUAGE_LABELS: Dict[str, str] = {
    "zh": "Simplified Chinese (简体中文)",
    "en": "English",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "fr": "French (français)",
    "es": "Spanish (español)",
}

WATERMARK_MD = "\n\n---\n\n*由 笔记助手 翻译*"
WATERMARK_HTML = '<hr/><p><em>由 笔记助手 翻译</em></p>'
WATERMARK_SNIPPET = "由 笔记助手 翻译"

SKIP_TRANSLATE_ANCESTOR_TAGS = frozenset(
    {"script", "style", "pre", "code", "noscript", "kbd", "samp", "textarea"}
)

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


def _skipped_for_translation(node: NavigableString) -> bool:
    p = node.parent
    while p is not None:
        if getattr(p, "name", None) in SKIP_TRANSLATE_ANCESTOR_TAGS:
            return True
        p = getattr(p, "parent", None)
    return False


def _collect_text_nodes(root: Any) -> List[NavigableString]:
    out: List[NavigableString] = []
    for el in root.descendants:
        if isinstance(el, NavigableString) and not isinstance(el, Comment):
            if not str(el).strip():
                continue
            if _skipped_for_translation(el):
                continue
            out.append(el)
    return out


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", t)
        t = re.sub(r"\n?\s*```\s*$", "", t)
    return t.strip()


def _parse_json_string_array(raw: str) -> List[str]:
    data = json.loads(_strip_json_fence(raw))
    if not isinstance(data, list):
        raise ValueError("expected JSON array")
    for x in data:
        if not isinstance(x, str):
            raise ValueError("expected array of strings")
    return data


def _build_segment_batches(segments: List[str]) -> List[List[str]]:
    batches: List[List[str]] = []
    idx = 0
    n = len(segments)
    while idx < n:
        batch: List[str] = []
        total = 0
        while idx < n:
            s = segments[idx]
            if batch and (
                total + len(s) > MAX_BATCH_CHARS or len(batch) >= MAX_SEGMENTS_PER_BATCH
            ):
                break
            batch.append(s)
            total += len(s)
            idx += 1
            if len(s) > MAX_BATCH_CHARS:
                break
        batches.append(batch)
    return batches


async def _llm_translate_segment_batch(
    client: Any,
    model: str,
    batch: List[str],
    lang_label: str,
) -> List[str]:
    user_prompt = (
        f"目标语言：{lang_label}\n"
        "将下方 JSON 数组中的每条字符串译为目标语言。\n"
        "仅输出合法 JSON 数组（元素均为字符串），长度与顺序必须与输入完全一致，不要输出解释或 Markdown。\n\n"
        f"{json.dumps(batch, ensure_ascii=False)}"
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": NOTE_HTML_SEGMENT_TRANSLATION_SYSTEM_PROMPT,
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.15,
        max_tokens=8192,
    )
    body = (response.choices[0].message.content or "").strip()
    if not body:
        raise RuntimeError("模型返回空内容")
    return _parse_json_string_array(body)


async def _translate_batch_with_retry(
    client: Any,
    model: str,
    batch: List[str],
    lang_label: str,
) -> List[str]:
    if not batch:
        return []
    try:
        out = await _llm_translate_segment_batch(client, model, batch, lang_label)
        if len(out) != len(batch):
            raise ValueError(f"segment count mismatch: {len(out)} != {len(batch)}")
        return out
    except Exception:
        if len(batch) <= 1:
            raise
        mid = len(batch) // 2
        left = await _translate_batch_with_retry(client, model, batch[:mid], lang_label)
        right = await _translate_batch_with_retry(client, model, batch[mid:], lang_label)
        return left + right


async def _translate_all_segments(
    client: Any,
    model: str,
    segments: List[str],
    lang_label: str,
) -> List[str]:
    if not segments:
        return []
    merged: List[str] = []
    for batch in _build_segment_batches(segments):
        merged.extend(await _translate_batch_with_retry(client, model, batch, lang_label))
    if len(merged) != len(segments):
        raise RuntimeError("HTML segment translation failed: length mismatch")
    return merged


def _parse_fragment_root(html: str) -> tuple[Any, Any]:
    frag = BeautifulSoup(html, "html.parser")
    soup = BeautifulSoup("", "html.parser")
    root = soup.new_tag("div")
    root["id"] = "__nt_translate_root"
    for child in list(frag.contents):
        root.append(child)
    soup.append(root)
    return soup, root


def _serialize_root_contents(root: Any) -> str:
    return "".join(str(c) for c in root.contents)


async def _translate_note_html(
    text: str,
    lang_label: str,
    truncated: bool,
    client: Any,
    model: str,
) -> Dict[str, Any]:
    _, root = _parse_fragment_root(text)
    nodes = _collect_text_nodes(root)
    originals = [str(n) for n in nodes]

    if originals:
        translated = await _translate_all_segments(client, model, originals, lang_label)
        for node, new_text in zip(nodes, translated):
            node.replace_with(NavigableString(new_text))

    out_html = _serialize_root_contents(root)
    if WATERMARK_SNIPPET not in out_html:
        wm = BeautifulSoup(WATERMARK_HTML, "html.parser")
        for ch in list(wm.contents):
            root.append(ch)
        out_html = _serialize_root_contents(root)

    return {
        "content": out_html,
        "truncated": truncated,
        "contentFormat": "html",
    }


async def translate_note(
    content: str, target_lang: str, *, db_user: UserDB
) -> Dict[str, Any]:
    raw = (content or "").strip()
    if not raw:
        raise ValueError("内容为空")

    truncated = len(raw) > MAX_INPUT_CHARS
    text = raw[:MAX_INPUT_CHARS]

    lang_label = TARGET_LANGUAGE_LABELS.get(
        (target_lang or "").strip().lower(), target_lang
    )

    client, model = openai_client_and_model_for_user(db_user)

    if looks_like_html_note(text):
        return await _translate_note_html(text, lang_label, truncated, client, model)

    user_prompt = f"""目标语言：{lang_label}

请翻译以下笔记全文（保持 Markdown 与代码块规则见系统说明）：

---
{text}
---"""

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": NOTE_TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=8192,
    )
    body = (response.choices[0].message.content or "").strip()
    if not body:
        raise RuntimeError("模型返回空内容")

    out = body.rstrip()
    if WATERMARK_SNIPPET not in out:
        out = out + WATERMARK_MD

    return {"content": out, "truncated": truncated, "contentFormat": "markdown"}
