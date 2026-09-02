"""Agent 清理后的回归检查：sub_agent 事件必须读取顶层 tool name。"""

import json

import pytest

from app.services.agent.base import BaseAgent, sse_event
from app.services.agent.note_assistant import NoteAssistant


class _FakeDBUser:
    id = 1


@pytest.mark.asyncio
async def test_sub_agent_events_use_top_level_tool_name(monkeypatch):
    events = [
        sse_event(
            "tool_start",
            {"id": "1", "name": "search_notes", "args": {"query": "机器学习"}},
        ),
        sse_event(
            "tool_end",
            {"id": "1", "name": "search_notes", "result": {"count": 0}},
        ),
    ]

    async def fake_run(self, message, history=None, *, db, db_user):
        for evt in events:
            yield evt

    monkeypatch.setattr(BaseAgent, "run", fake_run)

    agent = NoteAssistant()
    seen = []
    async for evt in agent.run("帮我搜索", db=object(), db_user=_FakeDBUser()):
        payload = json.loads(evt[len("data: ") :].strip())
        seen.append((payload["type"], payload.get("agent")))

    assert ("sub_agent_start", "search") in seen
    assert ("sub_agent_end", "search") in seen
