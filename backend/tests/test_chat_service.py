"""app.services.chat_service 测试

覆盖 _message_as_dict、_build_chat_messages 纯函数，
以及 mock OpenAI 客户端测试 chat_with_ai 和 chat_with_ai_stream。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import UserDB
from app.services.chat_service import (
    _build_chat_messages,
    _message_as_dict,
    chat_with_ai,
    chat_with_ai_stream,
)


# ============== _message_as_dict ==============

def test_message_as_dict_with_dict():
    msg = {"role": "user", "content": "hello"}
    result = _message_as_dict(msg)
    assert result == {"role": "user", "content": "hello"}


def test_message_as_dict_with_dict_missing_fields():
    msg = {}
    result = _message_as_dict(msg)
    assert result == {"role": "user", "content": ""}


def test_message_as_dict_with_dict_none_fields():
    msg = {"role": None, "content": None}
    result = _message_as_dict(msg)
    assert result == {"role": "user", "content": ""}


def test_message_as_dict_with_pydantic_model():
    class FakeModel:
        def model_dump(self):
            return {"role": "assistant", "content": "hi there"}

    result = _message_as_dict(FakeModel())
    assert result == {"role": "assistant", "content": "hi there"}


def test_message_as_dict_with_pydantic_model_missing():
    class FakeModel:
        def model_dump(self):
            return {}

    result = _message_as_dict(FakeModel())
    assert result == {"role": "user", "content": ""}


def test_message_as_dict_with_generic_object():
    class FakeObj:
        role = "user"
        content = "obj content"

    result = _message_as_dict(FakeObj())
    assert result == {"role": "user", "content": "obj content"}


def test_message_as_dict_with_generic_object_missing():
    class EmptyObj:
        pass

    result = _message_as_dict(EmptyObj())
    assert result == {"role": "user", "content": ""}


# ============== _build_chat_messages ==============

def test_build_chat_messages_basic():
    messages = _build_chat_messages("你好")
    assert len(messages) == 2  # system + user
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "你好"


def test_build_chat_messages_with_history():
    history = [
        {"role": "user", "content": "第一个问题"},
        {"role": "assistant", "content": "第一个回答"},
    ]
    messages = _build_chat_messages("第二个问题", history=history)
    assert len(messages) == 4  # system + 2 history + user
    assert messages[1]["content"] == "第一个问题"
    assert messages[2]["content"] == "第一个回答"
    assert messages[3]["content"] == "第二个问题"


def test_build_chat_messages_history_truncated_to_10():
    history = [{"role": "user", "content": f"msg{i}"} for i in range(15)]
    messages = _build_chat_messages("最新问题", history=history)
    # system + 10 history + 1 user = 12
    assert len(messages) == 12
    # 应该只保留最后10条
    assert messages[1]["content"] == "msg5"
    assert messages[10]["content"] == "msg14"


def test_build_chat_messages_system_messages_merged():
    history = [
        {"role": "system", "content": "自定义上下文1"},
        {"role": "user", "content": "用户问题"},
        {"role": "system", "content": "自定义上下文2"},
        {"role": "assistant", "content": "助手回答"},
    ]
    messages = _build_chat_messages("新问题", history=history)
    # system 消息被合并到第一条 system，不单独出现在 conversation 中
    assert len(messages) == 4  # system(合并) + user + assistant + user
    assert "附加上下文" in messages[0]["content"]
    assert "自定义上下文1" in messages[0]["content"]
    assert "自定义上下文2" in messages[0]["content"]


def test_build_chat_messages_system_empty_content_ignored():
    from app.services.chat_service import CHAT_SYSTEM_PROMPT
    history = [
        {"role": "system", "content": ""},
        {"role": "user", "content": "问题"},
    ]
    messages = _build_chat_messages("新问题", history=history)
    # 空 content 的 system 消息不应被追加，system 内容应等于原始 prompt
    assert messages[0]["content"] == CHAT_SYSTEM_PROMPT


def test_build_chat_messages_unknown_role_converted_to_user():
    history = [
        {"role": "unknown_role", "content": "未知角色消息"},
    ]
    messages = _build_chat_messages("问题", history=history)
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "未知角色消息"


def test_build_chat_messages_none_history():
    messages = _build_chat_messages("问题", history=None)
    assert len(messages) == 2


# ============== chat_with_ai ==============

def _make_mock_user():
    return UserDB(id=1, email="test@example.com", hashed_password="hash", nickname="tester")


@pytest.mark.asyncio
async def test_chat_with_ai_success():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="  你好，有什么可以帮你？  "))]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await chat_with_ai("你好", db_user=_make_mock_user())
        assert result == "你好，有什么可以帮你？"
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_chat_with_ai_empty_choices():
    mock_response = MagicMock()
    mock_response.choices = []

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        with pytest.raises(Exception, match="AI对话"):
            await chat_with_ai("你好", db_user=_make_mock_user())


@pytest.mark.asyncio
async def test_chat_with_ai_none_content():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=None))]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await chat_with_ai("你好", db_user=_make_mock_user())
        assert result == ""


@pytest.mark.asyncio
async def test_chat_with_ai_with_history():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="回答"))]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    history = [{"role": "user", "content": "之前的问题"}]
    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = await chat_with_ai("新问题", history=history, db_user=_make_mock_user())
        assert result == "回答"
        # 验证传入的 messages 包含历史
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 3  # system + history user + new user


@pytest.mark.asyncio
async def test_chat_with_ai_exception():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Connection error"))

    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        with pytest.raises(Exception, match="AI对话"):
            await chat_with_ai("你好", db_user=_make_mock_user())


# ============== chat_with_ai_stream ==============

def _make_mock_stream(chunks):
    async def async_iter():
        for chunk in chunks:
            yield chunk
    mock = MagicMock()
    mock.__aiter__ = lambda self: async_iter()
    return mock


@pytest.mark.asyncio
async def test_chat_with_ai_stream_success():
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="你"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="好"))]),
        MagicMock(choices=[]),  # 空 choices 跳过
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),  # None 跳过
        MagicMock(choices=[MagicMock(delta=MagicMock(content="！"))]),
    ]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in chat_with_ai_stream("你好", db_user=_make_mock_user()):
            result.append(text)
        assert "".join(result) == "你好！"


@pytest.mark.asyncio
async def test_chat_with_ai_stream_with_history():
    chunks = [MagicMock(choices=[MagicMock(delta=MagicMock(content="回答"))])]
    mock_stream = _make_mock_stream(chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

    history = [{"role": "assistant", "content": "之前的回答"}]
    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        result = []
        async for text in chat_with_ai_stream("问题", history=history, db_user=_make_mock_user()):
            result.append(text)
        assert "".join(result) == "回答"
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["stream"] is True


@pytest.mark.asyncio
async def test_chat_with_ai_stream_exception():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Timeout"))

    with patch("app.services.chat_service.openai_client_and_model_for_user", return_value=(mock_client, "test-model")):
        with pytest.raises(Exception, match="AI对话"):
            async for _ in chat_with_ai_stream("你好", db_user=_make_mock_user()):
                pass
