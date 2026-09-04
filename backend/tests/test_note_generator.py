"""app.services.note_generator 测试

覆盖 _normalize_reference_notes、_build_generation_prompt 纯函数，
以及 mock OpenAI 客户端测试 generate_note_stream。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import UserDB
from app.services.note_generator import (
    _build_generation_prompt,
    _normalize_reference_notes,
    generate_note_stream,
)


# ============== _normalize_reference_notes ==============

def test_normalize_reference_notes_none():
    assert _normalize_reference_notes(None) == []


def test_normalize_reference_notes_empty():
    assert _normalize_reference_notes([]) == []


def test_normalize_reference_notes_dict_list():
    notes = [{"filename": "a.md", "content": "content a"}, {"filename": "b.md", "content": "content b"}]
    result = _normalize_reference_notes(notes)
    assert len(result) == 2
    assert result[0]["filename"] == "a.md"
    assert result[1]["content"] == "content b"


def test_normalize_reference_notes_pydantic_model():
    class FakeModel:
        def model_dump(self):
            return {"filename": "model.md", "content": "model content"}

    result = _normalize_reference_notes([FakeModel()])
    assert len(result) == 1
    assert result[0]["filename"] == "model.md"


def test_normalize_reference_notes_generic_object():
    class FakeObj:
        filename = "obj.md"
        content = "obj content"

    result = _normalize_reference_notes([FakeObj()])
    assert len(result) == 1
    assert result[0]["filename"] == "obj.md"
    assert result[0]["content"] == "obj content"


def test_normalize_reference_notes_generic_object_missing_attrs():
    class EmptyObj:
        pass

    result = _normalize_reference_notes([EmptyObj()])
    assert len(result) == 1
    assert result[0]["filename"] == "未知文件"
    assert result[0]["content"] == ""


def test_normalize_reference_notes_mixed_types():
    class FakeModel:
        def model_dump(self):
            return {"filename": "m.md", "content": "m"}

    class FakeObj:
        filename = "o.md"
        content = "o"

    result = _normalize_reference_notes([
        {"filename": "d.md", "content": "d"},
        FakeModel(),
        FakeObj(),
    ])
    assert len(result) == 3
    assert result[0]["filename"] == "d.md"
    assert result[1]["filename"] == "m.md"
    assert result[2]["filename"] == "o.md"


# ============== _build_generation_prompt ==============

def test_build_generation_prompt_basic():
    prompt = _build_generation_prompt("Python 基础")
    assert "Python 基础" in prompt
    assert "核心概念介绍" in prompt
    assert "关键知识点详解" in prompt
    assert "实际应用或示例" in prompt
    assert "总结与复习要点" in prompt
    assert "500-700字" in prompt  # default word_count=600 → 500-700


def test_build_generation_prompt_with_keyword():
    prompt = _build_generation_prompt("机器学习", keyword="神经网络")
    assert "机器学习" in prompt
    assert "神经网络" in prompt
    assert "重点关注的关键词" in prompt


def test_build_generation_prompt_with_reference_notes():
    notes = [{"filename": "ref.md", "content": "这是参考内容"}]
    prompt = _build_generation_prompt("测试主题", reference_notes=notes)
    assert "参考材料" in prompt
    assert "ref.md" in prompt
    assert "这是参考内容" in prompt


def test_build_generation_prompt_long_reference_truncated():
    long_content = "x" * 3000
    notes = [{"filename": "long.md", "content": long_content}]
    prompt = _build_generation_prompt("测试", reference_notes=notes)
    assert "内容过长，已截断" in prompt
    assert "x" * 2000 in prompt


def test_build_generation_prompt_custom_word_count():
    prompt = _build_generation_prompt("测试", word_count=1000)
    assert "900-1100字" in prompt


def test_build_generation_prompt_custom_word_count_small():
    prompt = _build_generation_prompt("测试", word_count=500)
    # min_words = max(300, 500-100) = 400, max_words = 600
    assert "400-600字" in prompt


def test_build_generation_prompt_empty_reference_notes():
    prompt = _build_generation_prompt("测试", reference_notes=[])
    assert "参考材料" not in prompt


# ============== generate_note_stream ==============

def _make_mock_user():
    return UserDB(id=1, email="test@example.com", hashed_password="hash", nickname="tester")


def _make_mock_stream(chunks):
    """创建一个模拟的异步流式响应"""
    async def async_iter():
        for chunk in chunks:
            yield chunk
    mock = MagicMock()
    mock.__aiter__ = lambda self: async_iter()
    return mock


@pytest.mark.asyncio
async def test_generate_note_stream_success():
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="你好"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="，世界"))]),
        MagicMock(choices=[]),  # 空 choices 应被跳过
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),  # content None 应被跳过
        MagicMock(choices=[MagicMock(delta=MagicMock(content="！"))]),
    ]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_generator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in generate_note_stream("测试主题", db_user=_make_mock_user()):
            result.append(text)
        assert "".join(result) == "你好，世界！"


@pytest.mark.asyncio
async def test_generate_note_stream_with_all_params():
    chunks = [MagicMock(choices=[MagicMock(delta=MagicMock(content="生成内容"))])]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.note_generator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in generate_note_stream(
            "Python",
            keyword="装饰器",
            reference_notes=[{"filename": "ref.md", "content": "ref"}],
            images=["img1.png"],
            word_count=800,
            db_user=_make_mock_user(),
        ):
            result.append(text)
        assert "".join(result) == "生成内容"
        # 验证调用参数
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "test-model"
        assert call_kwargs.kwargs["stream"] is True
        assert call_kwargs.kwargs["max_tokens"] == 2400  # 800 * 3


@pytest.mark.asyncio
async def test_generate_note_stream_llm_exception():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API rate limit"))

    with patch("app.services.note_generator.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        with pytest.raises(Exception, match="AI生成笔记"):
            async for _ in generate_note_stream("测试", db_user=_make_mock_user()):
                pass
