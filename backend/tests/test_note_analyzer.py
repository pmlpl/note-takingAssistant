"""app.services.note_analyzer 测试

通过 mock OpenAI 客户端测试 analyze_note 的各种场景：
成功返回 JSON、JSON 带代码块、JSON 解析失败降级、LLM 异常。
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import UserDB
from app.services.note_analyzer import analyze_note


def _make_mock_user():
    return UserDB(id=1, email="test@example.com", hashed_password="hash", nickname="tester")


def _make_mock_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    return mock_response


# ============== analyze_note 成功场景 ==============

@pytest.mark.asyncio
async def test_analyze_note_success_valid_json():
    valid_json = json.dumps({
        "summary": "这是一篇关于Python的笔记",
        "strengths": ["结构清晰", "示例丰富"],
        "weaknesses": ["缺少高级主题"],
        "suggestions": ["补充装饰器内容"],
    })
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(valid_json))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("Python 基础笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "这是一篇关于Python的笔记"
        assert len(result["strengths"]) == 2
        assert result["strengths"][0] == "结构清晰"
        assert len(result["weaknesses"]) == 1
        assert len(result["suggestions"]) == 1


@pytest.mark.asyncio
async def test_analyze_note_json_with_code_block():
    content_with_block = f"```json\n{json.dumps({'summary': '带代码块的总结', 'strengths': ['好'], 'weaknesses': ['差'], 'suggestions': ['改']})}\n```"
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(content_with_block))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "带代码块的总结"


@pytest.mark.asyncio
async def test_analyze_note_json_with_generic_code_block():
    content_with_block = f"```\n{json.dumps({'summary': '通用代码块', 'strengths': ['s'], 'weaknesses': ['w'], 'suggestions': ['g']})}\n```"
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(content_with_block))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "通用代码块"


@pytest.mark.asyncio
async def test_analyze_note_json_with_trailing_comma():
    # JSON 末尾带逗号，测试 rstrip(",") 处理
    content = '{"summary": "带逗号", "strengths": ["a"], "weaknesses": ["b"], "suggestions": ["c"]},'
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(content))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "带逗号"


# ============== analyze_note 部分字段缺失 ==============

@pytest.mark.asyncio
async def test_analyze_note_missing_fields_use_defaults():
    partial_json = json.dumps({"summary": "只有总结"})
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(partial_json))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "只有总结"
        assert result["strengths"] == ["笔记结构清晰"]
        assert result["weaknesses"] == ["可以增加更多实例"]
        assert result["suggestions"] == ["建议补充相关案例"]


@pytest.mark.asyncio
async def test_analyze_note_empty_response():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(""))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        # 空字符串 JSON 解析失败，走降级
        assert result["summary"] == "AI 分析完成，但返回格式有误"
        assert len(result["strengths"]) == 2
        assert len(result["weaknesses"]) == 2
        assert len(result["suggestions"]) == 2


# ============== analyze_note JSON 解析失败降级 ==============

@pytest.mark.asyncio
async def test_analyze_note_invalid_json_fallback():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response("这不是JSON，是一段普通文本"))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "AI 分析完成，但返回格式有误"
        assert "笔记结构清晰" in result["strengths"]
        assert "可以增加更多实例" in result["weaknesses"]
        assert "建议补充相关案例" in result["suggestions"]


@pytest.mark.asyncio
async def test_analyze_note_none_content():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=None))]
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await analyze_note("笔记内容", db_user=_make_mock_user())
        assert result["summary"] == "AI 分析完成，但返回格式有误"


# ============== analyze_note LLM 异常 ==============

@pytest.mark.asyncio
async def test_analyze_note_llm_exception():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API rate limit exceeded"))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        with pytest.raises(Exception, match="AI分析"):
            await analyze_note("笔记内容", db_user=_make_mock_user())


# ============== analyze_note 调用参数验证 ==============

@pytest.mark.asyncio
async def test_analyze_note_passes_correct_params():
    valid_json = json.dumps({"summary": "test", "strengths": [], "weaknesses": [], "suggestions": []})
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_mock_response(valid_json))

    with patch("app.services.note_analyzer.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        await analyze_note("测试笔记内容", db_user=_make_mock_user())
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "test-model"
        assert call_kwargs.kwargs["temperature"] == 0.3
        assert call_kwargs.kwargs["max_tokens"] == 1000
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "测试笔记内容" in messages[1]["content"]
        assert "内容完整性" in messages[1]["content"]
        assert "结构清晰度" in messages[1]["content"]
