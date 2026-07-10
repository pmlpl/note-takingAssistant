"""Coordinator 调度员

负责：
1. 直接使用统一的 NoteAssistant（唯一的主 Agent）
2. NoteAssistant 包含所有工具，LLM 通过 Function Calling 选择调用
3. 工具调用时触发 sub_agent_start/sub_agent_end 事件通知前端

架构：
- 主 Agent：Note助手（始终显示）
- 子 Agent：搜索/总结/生成/翻译/思维导图（工具调用时显示）
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDB
from app.services.agent.note_assistant import NoteAssistant
from app.services.agent.base import sse_event

logger = logging.getLogger(__name__)


async def coordinator_run(
    message: str,
    history: Optional[List[Any]] = None,
    *,
    db: AsyncSession,
    db_user: UserDB,
    enable_multi_agent: bool = True,
) -> AsyncIterator[str]:
    """Coordinator 主流程：直接使用 NoteAssistant

    事件类型：
    - agent_start: Note助手开始工作
    - sub_agent_start: 调用某个子 Agent 的工具（搜索/总结/生成/翻译/思维导图）
    - sub_agent_end: 子 Agent 工具调用结束
    - thinking / tool_start / tool_end / delta / done / error: 与原事件一致
    - agent_end: Note助手结束工作
    """
    agent = NoteAssistant()

    final_text = ""
    async for evt in agent.run(message, history, db=db, db_user=db_user):
        try:
            payload = json.loads(evt[len("data: "):].strip())
            if payload.get("type") == "delta":
                final_text += payload.get("text", "")
        except Exception:
            pass
        yield evt
