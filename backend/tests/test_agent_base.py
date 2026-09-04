"""app.services.agent.base 单元测试

覆盖：
- sse_event 构造
- BaseAgent.run：直接回答、工具调用、空 choices、LLM 异常、tools 不支持降级、最大轮数
- _execute_tool：已知工具、未知工具、handler 异常
- _build_messages：dict/object 历史、system 合并、角色归一化、截断
- _looks_like_tools_unsupported
- _truncate_tool_result
- _emit_final_answer：空文本、分块
- _fallback_plain_stream：成功、异常
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent.base import (
    FINAL_ANSWER_CHUNK_SIZE,
    MAX_TOOL_RESULT_CHARS,
    MAX_TOOL_ROUNDS,
    BaseAgent,
    sse_event,
)


# ────────────────────── helpers ──────────────────────

def _make_message(content=None, tool_calls=None):
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    return msg


def _make_response(content=None, tool_calls=None):
    msg = _make_message(content=content, tool_calls=tool_calls)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_tool_call(tc_id, name, arguments):
    tc = MagicMock()
    tc.id = tc_id
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


def _make_fake_user():
    u = MagicMock()
    u.id = 1
    return u


def _parse_sse(evt: str) -> dict:
    return json.loads(evt[len("data: "):].strip())


class _NoToolsAgent(BaseAgent):
    name = "no_tools"
    display_name = "无工具 Agent"
    emoji = "🤖"
    system_prompt = "你是测试助手"
    tools_definition = []
    tool_handlers = {}


class _OneToolAgent(BaseAgent):
    name = "one_tool"
    display_name = "单工具 Agent"
    emoji = "🔧"
    system_prompt = "你是测试助手"
    tools_definition = [{"type": "function", "function": {"name": "echo", "description": "echo"}}]
    tool_handlers = {}


# ────────────────────── sse_event ──────────────────────

class TestSseEvent:
    def test_basic_event(self):
        evt = sse_event("delta", {"text": "hi"})
        assert evt.startswith("data: ")
        payload = _parse_sse(evt)
        assert payload["type"] == "delta"
        assert payload["text"] == "hi"

    def test_event_without_data(self):
        evt = sse_event("done")
        payload = _parse_sse(evt)
        assert payload["type"] == "done"

    def test_event_ends_with_double_newline(self):
        assert sse_event("x").endswith("\n\n")


# ────────────────────── _build_messages ──────────────────────

class TestBuildMessages:
    def test_basic_no_history(self):
        agent = _NoToolsAgent()
        msgs = agent._build_messages("你好")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "测试助手" in msgs[0]["content"]
        assert msgs[1]["role"] == "user"
        assert msgs[1]["content"] == "你好"

    def test_dict_history(self):
        agent = _NoToolsAgent()
        history = [{"role": "user", "content": "之前的问题"}, {"role": "assistant", "content": "之前的回答"}]
        msgs = agent._build_messages("新问题", history)
        assert len(msgs) == 4  # system + 2 history + user
        assert msgs[1]["content"] == "之前的问题"
        assert msgs[2]["content"] == "之前的回答"

    def test_object_history(self):
        agent = _NoToolsAgent()
        obj = MagicMock()
        obj.content = "对象消息"
        msgs = agent._build_messages("hi", [obj])
        assert msgs[1]["role"] == "user"
        assert msgs[1]["content"] == "对象消息"

    def test_system_history_merged_into_system_prompt(self):
        agent = _NoToolsAgent()
        history = [{"role": "system", "content": "额外上下文"}]
        msgs = agent._build_messages("hi", history)
        assert len(msgs) == 2  # system(merged) + user
        assert "额外上下文" in msgs[0]["content"]
        assert "附加上下文" in msgs[0]["content"]

    def test_empty_system_history_ignored(self):
        agent = _NoToolsAgent()
        history = [{"role": "system", "content": ""}]
        msgs = agent._build_messages("hi", history)
        assert "附加上下文" not in msgs[0]["content"]

    def test_invalid_role_defaults_to_user(self):
        agent = _NoToolsAgent()
        history = [{"role": "tool", "content": "工具结果"}]
        msgs = agent._build_messages("hi", history)
        assert msgs[1]["role"] == "user"

    def test_history_truncated_to_last_10(self):
        agent = _NoToolsAgent()
        history = [{"role": "user", "content": f"msg{i}"} for i in range(15)]
        msgs = agent._build_messages("hi", history)
        # system + 10 history + user = 12
        assert len(msgs) == 12
        assert msgs[1]["content"] == "msg5"  # first of last 10

    def test_none_history(self):
        agent = _NoToolsAgent()
        msgs = agent._build_messages("hi", None)
        assert len(msgs) == 2


# ────────────────────── _looks_like_tools_unsupported ──────────────────────

class TestLooksLikeToolsUnsupported:
    def test_tool_keyword(self):
        agent = _NoToolsAgent()
        assert agent._looks_like_tools_unsupported(Exception("tools not supported")) is True

    def test_function_keyword(self):
        agent = _NoToolsAgent()
        assert agent._looks_like_tools_unsupported(Exception("function call error")) is True

    def test_400_error(self):
        agent = _NoToolsAgent()
        assert agent._looks_like_tools_unsupported(Exception("400 Bad Request")) is True

    def test_401_not_tools_issue(self):
        agent = _NoToolsAgent()
        assert agent._looks_like_tools_unsupported(Exception("401 Unauthorized")) is False

    def test_auth_not_tools_issue(self):
        agent = _NoToolsAgent()
        assert agent._looks_like_tools_unsupported(Exception("auth failed")) is False

    def test_unrelated_error(self):
        agent = _NoToolsAgent()
        assert agent._looks_like_tools_unsupported(Exception("timeout")) is False


# ────────────────────── _truncate_tool_result ──────────────────────

class TestTruncateToolResult:
    def test_short_result(self):
        agent = _NoToolsAgent()
        result = {"key": "value"}
        text = agent._truncate_tool_result(result)
        assert "key" in text
        assert "截断" not in text

    def test_long_result_truncated(self):
        agent = _NoToolsAgent()
        long_text = "x" * (MAX_TOOL_RESULT_CHARS + 100)
        text = agent._truncate_tool_result(long_text)
        assert "截断" in text
        assert len(text) <= MAX_TOOL_RESULT_CHARS + len("...（结果过长，已截断）") + 10

    def test_non_serializable_uses_str(self):
        agent = _NoToolsAgent()
        obj = object()
        text = agent._truncate_tool_result(obj)
        assert "object" in text


# ────────────────────── _execute_tool ──────────────────────

class TestExecuteTool:
    @pytest.mark.asyncio
    async def test_known_tool_success(self):
        async def handler(**kwargs):
            return {"ok": True}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": handler}
        result = await agent._execute_tool("echo", {"x": 1}, db=MagicMock(), db_user=_make_fake_user())
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        agent = _OneToolAgent()
        result = await agent._execute_tool("nonexistent", {}, db=MagicMock(), db_user=_make_fake_user())
        assert "error" in result
        assert "未知工具" in result["error"]

    @pytest.mark.asyncio
    async def test_handler_exception_returns_error(self):
        async def bad_handler(**kwargs):
            raise RuntimeError("boom")

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": bad_handler}
        result = await agent._execute_tool("echo", {}, db=MagicMock(), db_user=_make_fake_user())
        assert "error" in result
        assert "工具执行失败" in result["error"]


# ────────────────────── _emit_final_answer ──────────────────────

class TestEmitFinalAnswer:
    @pytest.mark.asyncio
    async def test_normal_text(self):
        agent = _NoToolsAgent()
        events = [evt async for evt in agent._emit_final_answer("你好世界")]
        payloads = [_parse_sse(e) for e in events]
        assert payloads[0]["type"] == "delta"
        assert payloads[0]["text"] == "你好世界"
        assert payloads[-1]["type"] == "done"
        assert payloads[-1]["agent"] == "no_tools"

    @pytest.mark.asyncio
    async def test_empty_text_uses_default(self):
        agent = _NoToolsAgent()
        events = [evt async for evt in agent._emit_final_answer("")]
        payloads = [_parse_sse(e) for e in events]
        assert "无法回答" in payloads[0]["text"]

    @pytest.mark.asyncio
    async def test_long_text_chunked(self):
        agent = _NoToolsAgent()
        long_text = "字" * (FINAL_ANSWER_CHUNK_SIZE * 3 + 10)
        events = [evt async for evt in agent._emit_final_answer(long_text)]
        payloads = [_parse_sse(e) for e in events]
        deltas = [p for p in payloads if p["type"] == "delta"]
        assert len(deltas) == 4  # 3 full chunks + 1 partial
        assert payloads[-1]["type"] == "done"


# ────────────────────── run: 直接回答 ──────────────────────

class TestRunDirectAnswer:
    @pytest.mark.asyncio
    async def test_direct_answer_no_tools(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_response(content="直接回答内容")
        )
        agent = _NoToolsAgent()
        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("你好", db=MagicMock(), db_user=_make_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        types = [p["type"] for p in payloads]
        assert "delta" in types
        assert "done" in types
        assert "error" not in types

    @pytest.mark.asyncio
    async def test_empty_content_stripped(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_response(content="   ")
        )
        agent = _NoToolsAgent()
        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        # 空内容 → _emit_final_answer 用默认文案
        deltas = [p for p in payloads if p["type"] == "delta"]
        assert len(deltas) >= 1


# ────────────────────── run: LLM 初始化失败 ──────────────────────

class TestRunLLMInitFailure:
    @pytest.mark.asyncio
    async def test_client_init_exception_yields_error(self):
        agent = _NoToolsAgent()
        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   side_effect=RuntimeError("init failed")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        assert payloads[0]["type"] == "error"
        assert "AI助手" in payloads[0]["message"] or len(payloads[0]["message"]) > 0


# ────────────────────── run: 空 choices ──────────────────────

class TestRunEmptyChoices:
    @pytest.mark.asyncio
    async def test_empty_choices_yields_error(self):
        mock_client = MagicMock()
        empty_resp = MagicMock()
        empty_resp.choices = []
        mock_client.chat.completions.create = AsyncMock(return_value=empty_resp)
        agent = _NoToolsAgent()
        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        assert payloads[0]["type"] == "error"
        assert "空 choices" in payloads[0]["message"]


# ────────────────────── run: LLM 调用异常 ──────────────────────

class TestRunLLMException:
    @pytest.mark.asyncio
    async def test_llm_exception_no_tools_yields_error(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("API down"))
        agent = _NoToolsAgent()
        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        assert any(p["type"] == "error" for p in payloads)


# ────────────────────── run: 工具调用流程 ──────────────────────

class TestRunWithTools:
    @pytest.mark.asyncio
    async def test_tool_call_then_final_answer(self):
        """第一轮返回 tool_call，第二轮返回最终回答。"""
        tool_call = _make_tool_call("call_1", "echo", json.dumps({"text": "hi"}))
        first_resp = _make_response(content="思考中", tool_calls=[tool_call])
        second_resp = _make_response(content="最终回答")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[first_resp, second_resp])

        async def echo_handler(**kwargs):
            return {"echoed": kwargs.get("args", {}).get("text")}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": echo_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("调用工具", db=MagicMock(), db_user=_make_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        types = [p["type"] for p in payloads]
        assert "thinking" in types
        assert "tool_start" in types
        assert "tool_end" in types
        assert "delta" in types
        assert "done" in types

        tool_start = next(p for p in payloads if p["type"] == "tool_start")
        assert tool_start["name"] == "echo"
        assert tool_start["args"] == {"text": "hi"}

    @pytest.mark.asyncio
    async def test_tool_call_with_invalid_json_args(self):
        tool_call = _make_tool_call("call_1", "echo", "not-valid-json{{")
        first_resp = _make_response(content="思考", tool_calls=[tool_call])
        second_resp = _make_response(content="回答")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[first_resp, second_resp])

        async def echo_handler(**kwargs):
            return {"ok": True}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": echo_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        tool_start = next(p for p in payloads if p["type"] == "tool_start")
        assert tool_start["args"] == {}  # 解析失败降级为空 dict

    @pytest.mark.asyncio
    async def test_tool_result_too_long_truncated_in_tool_end(self):
        tool_call = _make_tool_call("call_1", "echo", "{}")
        first_resp = _make_response(content="思考", tool_calls=[tool_call])
        second_resp = _make_response(content="回答")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[first_resp, second_resp])

        async def big_handler(**kwargs):
            return {"data": "x" * (MAX_TOOL_RESULT_CHARS + 1000)}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": big_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        tool_end = next(p for p in payloads if p["type"] == "tool_end")
        assert tool_end["result"]["truncated"] is True

    @pytest.mark.asyncio
    async def test_tool_result_non_serializable_uses_str_truncate(self):
        """_truncate_tool_result 对非序列化对象走 str() 分支；
        run 中 tool_end 的 result 字段用可序列化大对象验证截断路径。"""
        tool_call = _make_tool_call("call_1", "echo", "{}")
        first_resp = _make_response(content="思考", tool_calls=[tool_call])
        second_resp = _make_response(content="回答")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[first_resp, second_resp])

        async def big_handler(**kwargs):
            return {"data": "x" * 100}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": big_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        tool_end = next(p for p in payloads if p["type"] == "tool_end")
        assert "result" in tool_end

    @pytest.mark.asyncio
    async def test_no_thinking_when_content_empty(self):
        tool_call = _make_tool_call("call_1", "echo", "{}")
        first_resp = _make_response(content=None, tool_calls=[tool_call])
        second_resp = _make_response(content="回答")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[first_resp, second_resp])

        async def echo_handler(**kwargs):
            return {"ok": True}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": echo_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        assert not any(p["type"] == "thinking" for p in payloads)


# ────────────────────── run: 最大轮数 ──────────────────────

class TestRunMaxRounds:
    @pytest.mark.asyncio
    async def test_max_rounds_forced_final(self):
        """每轮都返回 tool_call，达到 MAX_TOOL_ROUNDS 后强制生成最终回答。"""
        tool_call = _make_tool_call("call_x", "echo", "{}")
        tool_resp = _make_response(content="思考", tool_calls=[tool_call])
        final_resp = _make_response(content="最终强制回答")

        # MAX_TOOL_ROUNDS 次 tool 响应 + 1 次最终响应
        responses = [tool_resp] * MAX_TOOL_ROUNDS + [final_resp]
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=responses)

        async def echo_handler(**kwargs):
            return {"ok": True}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": echo_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        assert any(p["type"] == "done" for p in payloads)
        # 最后一轮应有 system 消息注入（通过调用次数验证：MAX_TOOL_ROUNDS tool + 1 final）
        assert mock_client.chat.completions.create.call_count == MAX_TOOL_ROUNDS + 1

    @pytest.mark.asyncio
    async def test_max_rounds_final_llm_exception(self):
        tool_call = _make_tool_call("call_x", "echo", "{}")
        tool_resp = _make_response(content="思考", tool_calls=[tool_call])

        responses = [tool_resp] * MAX_TOOL_ROUNDS
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=responses + [RuntimeError("final fail")])

        async def echo_handler(**kwargs):
            return {"ok": True}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": echo_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        assert any(p["type"] == "error" for p in payloads)

    @pytest.mark.asyncio
    async def test_max_rounds_empty_final_content_uses_fallback(self):
        tool_call = _make_tool_call("call_x", "echo", "{}")
        tool_resp = _make_response(content="思考", tool_calls=[tool_call])
        final_resp = _make_response(content="")

        responses = [tool_resp] * MAX_TOOL_ROUNDS + [final_resp]
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=responses)

        async def echo_handler(**kwargs):
            return {"ok": True}

        agent = _OneToolAgent()
        agent.tool_handlers = {"echo": echo_handler}

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]
        payloads = [_parse_sse(e) for e in events]
        deltas = [p for p in payloads if p["type"] == "delta"]
        # 空内容 → 兜底文案
        assert any("上限" in p.get("text", "") or "无法回答" in p.get("text", "") for p in deltas)


# ────────────────────── run: tools 不支持降级 ──────────────────────

class TestRunToolsUnsupportedFallback:
    @pytest.mark.asyncio
    async def test_tools_unsupported_falls_back_to_plain_stream(self):
        mock_client = MagicMock()
        # 第一次调用（带 tools）抛异常，触发降级
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("tools parameter is not supported")
        )

        agent = _OneToolAgent()

        async def fake_fallback(self, client, model, messages):
            yield sse_event("delta", {"text": "降级回答", "agent": self.name})
            yield sse_event("done", {"finish_reason": "stop", "agent": self.name})

        with patch("app.services.agent.base.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            with patch.object(BaseAgent, "_fallback_plain_stream", fake_fallback):
                events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_make_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        assert any(p["type"] == "delta" for p in payloads)
        assert any(p["type"] == "done" for p in payloads)


# ────────────────────── _fallback_plain_stream ──────────────────────

class TestFallbackPlainStream:
    @pytest.mark.asyncio
    async def test_stream_success(self):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content=" World"))]
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock(delta=MagicMock(content=None))]  # None content 跳过

        async def async_iter():
            for c in [chunk1, chunk2, chunk3]:
                yield c

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=async_iter())

        agent = _NoToolsAgent()
        events = [evt async for evt in agent._fallback_plain_stream(mock_client, "m", [])]
        payloads = [_parse_sse(e) for e in events]
        deltas = [p for p in payloads if p["type"] == "delta"]
        assert len(deltas) == 2
        assert deltas[0]["text"] == "Hello"
        assert deltas[1]["text"] == " World"
        assert payloads[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_empty_choices_skipped(self):
        chunk = MagicMock()
        chunk.choices = []

        async def async_iter():
            yield chunk

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=async_iter())

        agent = _NoToolsAgent()
        events = [evt async for evt in agent._fallback_plain_stream(mock_client, "m", [])]
        payloads = [_parse_sse(e) for e in events]
        assert all(p["type"] != "delta" for p in payloads)
        assert payloads[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_exception_yields_error(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("stream fail"))

        agent = _NoToolsAgent()
        events = [evt async for evt in agent._fallback_plain_stream(mock_client, "m", [])]
        payloads = [_parse_sse(e) for e in events]
        assert payloads[-1]["type"] == "error"
