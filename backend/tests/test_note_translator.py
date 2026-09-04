"""app.services.note_translator 测试

覆盖纯函数 looks_like_html_note、html_to_markdown、prepare_markdown_for_translation，
以及 mock LLM 测试 translate_note_stream。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import UserDB
from app.services.note_translator import (
    html_to_markdown,
    looks_like_html_note,
    prepare_markdown_for_translation,
    translate_note_stream,
)


# ============== looks_like_html_note ==============

def test_looks_like_html_with_p_tag():
    assert looks_like_html_note("<p>Hello World</p>") is True


def test_looks_like_html_with_div():
    assert looks_like_html_note("<div>Content</div>") is True


def test_looks_like_html_with_heading():
    assert looks_like_html_note("<h1>Title</h1>") is True


def test_looks_like_html_with_br():
    assert looks_like_html_note("Line 1<br>Line 2") is True


def test_looks_like_html_plain_text():
    assert looks_like_html_note("This is plain text without tags") is False


def test_looks_like_html_markdown():
    assert looks_like_html_note("# Title\n\nThis is **markdown**") is False


def test_looks_like_html_empty():
    assert looks_like_html_note("") is False
    assert looks_like_html_note(None) is False


def test_looks_like_html_whitespace():
    assert looks_like_html_note("   ") is False


def test_looks_like_html_angle_bracket_but_not_tag():
    # 有 < 但不是 HTML 标签
    assert looks_like_html_note("a < b and b > c") is False


def test_looks_like_html_table_tags():
    assert looks_like_html_note("<table><tr><td>data</td></tr></table>") is True


def test_looks_like_html_img_tag():
    assert looks_like_html_note('<img src="test.png" alt="test">') is True


def test_looks_like_html_ul_li():
    assert looks_like_html_note("<ul><li>item1</li><li>item2</li></ul>") is True


def test_looks_like_html_case_insensitive():
    assert looks_like_html_note("<DIV>Content</DIV>") is True
    assert looks_like_html_note("<P>Content</P>") is True


# ============== html_to_markdown ==============

def test_html_to_markdown_empty():
    assert html_to_markdown("") == ""
    assert html_to_markdown(None) == ""


def test_html_to_markdown_whitespace():
    assert html_to_markdown("   ") == ""


def test_html_to_markdown_paragraph():
    result = html_to_markdown("<p>Hello World</p>")
    assert "Hello World" in result


def test_html_to_markdown_heading():
    result = html_to_markdown("<h1>Title</h1>")
    assert "# Title" in result or "Title" in result


def test_html_to_markdown_link():
    result = html_to_markdown('<a href="http://example.com">Link</a>')
    assert "Link" in result


def test_html_to_markdown_bold():
    result = html_to_markdown("<strong>Bold text</strong>")
    assert "Bold text" in result


def test_html_to_markdown_list():
    result = html_to_markdown("<ul><li>Item 1</li><li>Item 2</li></ul>")
    assert "Item 1" in result
    assert "Item 2" in result


def test_html_to_markdown_complex():
    html = """
    <div>
        <h1>Main Title</h1>
        <p>First paragraph with <strong>bold</strong> text.</p>
        <p>Second paragraph with <a href="http://link.com">a link</a>.</p>
        <ul>
            <li>Point one</li>
            <li>Point two</li>
        </ul>
    </div>
    """
    result = html_to_markdown(html)
    assert "Main Title" in result
    assert "First paragraph" in result
    assert "bold" in result
    assert "Point one" in result


def test_html_to_markdown_invalid_html_fallback():
    # 无效的 HTML 应该走 BeautifulSoup 降级
    result = html_to_markdown("<div>Unclosed tag content")
    assert "Unclosed tag content" in result


# ============== prepare_markdown_for_translation ==============

def test_prepare_markdown_plain_text():
    md, from_html, truncated = prepare_markdown_for_translation("Hello World")
    assert md == "Hello World"
    assert from_html is False
    assert truncated is False


def test_prepare_markdown_markdown_content():
    content = "# Title\n\nThis is **markdown** content."
    md, from_html, truncated = prepare_markdown_for_translation(content)
    assert md == content
    assert from_html is False
    assert truncated is False


def test_prepare_markdown_html_content():
    html = "<p>Hello <strong>World</strong></p>"
    md, from_html, truncated = prepare_markdown_for_translation(html)
    assert from_html is True
    assert "Hello" in md
    assert "World" in md
    assert truncated is False


def test_prepare_markdown_empty_raises():
    with pytest.raises(ValueError, match="内容为空"):
        prepare_markdown_for_translation("")


def test_prepare_markdown_none_raises():
    with pytest.raises(ValueError, match="内容为空"):
        prepare_markdown_for_translation(None)


def test_prepare_markdown_whitespace_raises():
    with pytest.raises(ValueError, match="内容为空"):
        prepare_markdown_for_translation("   ")


def test_prepare_markdown_long_content_truncated():
    long_content = "x" * 9000
    md, from_html, truncated = prepare_markdown_for_translation(long_content)
    assert truncated is True
    assert len(md) == 8000  # MAX_INPUT_CHARS


def test_prepare_markdown_exactly_max_chars():
    content = "x" * 8000
    md, from_html, truncated = prepare_markdown_for_translation(content)
    assert truncated is False
    assert len(md) == 8000


def test_prepare_markdown_html_converted_empty_raises():
    # HTML 转换后内容为空应该报错
    with pytest.raises(ValueError, match="转换后内容为空"):
        prepare_markdown_for_translation("<p></p>")


# ============== translate_note_stream ==============

def _make_mock_user():
    return UserDB(id=1, email="test@example.com", hashed_password="hash", nickname="tester")


def _make_mock_stream(chunks):
    async def async_iter():
        for chunk in chunks:
            yield chunk
    mock = MagicMock()
    mock.__aiter__ = lambda self: async_iter()
    return mock


@pytest.mark.asyncio
async def test_translate_note_stream_success():
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="翻译"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="结果"))]),
        MagicMock(choices=[]),  # 空 choices 跳过
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),  # None 跳过
        MagicMock(choices=[MagicMock(delta=MagicMock(content="！"))]),
    ]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in translate_note_stream("Hello World", "en", db_user=_make_mock_user()):
            result.append(text)
        # 应该包含翻译内容 + 水印
        full = "".join(result)
        assert "翻译结果！" in full
        assert "由 笔记助手 翻译" in full


@pytest.mark.asyncio
async def test_translate_note_stream_html_input():
    chunks = [MagicMock(choices=[MagicMock(delta=MagicMock(content="翻译后的HTML"))])]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in translate_note_stream("<p>Hello</p>", "zh", db_user=_make_mock_user()):
            result.append(text)
        full = "".join(result)
        assert "翻译后的HTML" in full
        # 验证调用参数中包含目标语言
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert "Simplified Chinese" in messages[1]["content"] or "简体中文" in messages[1]["content"]


@pytest.mark.asyncio
async def test_translate_note_stream_unknown_language():
    chunks = [MagicMock(choices=[MagicMock(delta=MagicMock(content="内容"))])]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in translate_note_stream("Hello", "xx", db_user=_make_mock_user()):
            result.append(text)
        # 未知语言直接使用原始值
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert "xx" in messages[1]["content"]


@pytest.mark.asyncio
async def test_translate_note_stream_watermark_already_present():
    # 如果模型输出已经包含水印，不应重复添加
    chunks = [MagicMock(choices=[MagicMock(delta=MagicMock(content="翻译内容\n\n---\n\n*由 笔记助手 翻译*"))])]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in translate_note_stream("Hello", "en", db_user=_make_mock_user()):
            result.append(text)
        full = "".join(result)
        # 水印只出现一次
        assert full.count("由 笔记助手 翻译") == 1


@pytest.mark.asyncio
async def test_translate_note_stream_llm_exception():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Connection error"))

    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        # client.chat.completions.create 在 try 块外面，异常直接抛出
        with pytest.raises(Exception, match="Connection error"):
            async for _ in translate_note_stream("Hello", "en", db_user=_make_mock_user()):
                pass


@pytest.mark.asyncio
async def test_translate_note_stream_empty_content_raises():
    mock_client = MagicMock()
    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        with pytest.raises(ValueError):
            async for _ in translate_note_stream("", "en", db_user=_make_mock_user()):
                pass


@pytest.mark.asyncio
async def test_translate_note_stream_passes_correct_params():
    chunks = [MagicMock(choices=[MagicMock(delta=MagicMock(content="ok"))])]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_translator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        async for _ in translate_note_stream("Hello", "ja", db_user=_make_mock_user()):
            pass

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "test-model"
        assert call_kwargs.kwargs["stream"] is True
        assert call_kwargs.kwargs["temperature"] == 0.2
        assert call_kwargs.kwargs["max_tokens"] == 8192
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Japanese" in messages[1]["content"] or "日本語" in messages[1]["content"]
