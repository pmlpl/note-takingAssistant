"""NoteAssistant：统一的笔记助手

这是唯一的主 Agent，包含所有工具。LLM 通过 Function Calling 直接选择调用哪个工具。
每个工具标注所属的子 Agent，前端显示时展示当前使用的是哪个子 Agent 的工具。

架构：
- 主 Agent：Note助手（显示在聊天界面）
- 子 Agent：搜索/总结/生成/翻译/思维导图（通过工具调用时显示）
- 工具：search_notes, get_note_content, summarize_note, generate_note, translate_note, create_note
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDB
from app.services.agent.base import BaseAgent, sse_event
from app.services.llm_runtime import openai_client_and_model_for_user
from app.utils.llm_errors import format_llm_error

logger = logging.getLogger(__name__)


SUB_AGENTS = {
    "search": {"name": "搜索", "emoji": "🔍", "display_name": "搜索专家"},
    "summarize": {"name": "总结", "emoji": "📝", "display_name": "总结专家"},
    "generate": {"name": "生成", "emoji": "✍️", "display_name": "生成专家"},
    "translate": {"name": "翻译", "emoji": "🌐", "display_name": "翻译专家"},
    "mindmap": {"name": "思维导图", "emoji": "🧠", "display_name": "思维导图专家"},
}

TOOL_TO_SUB_AGENT = {
    "search_notes": "search",
    "get_note_content": None,
    "summarize_note": "summarize",
    "generate_note": "generate",
    "translate_note": "translate",
    "create_note": "generate",
}


NOTE_ASSISTANT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "搜索用户的笔记，返回匹配的笔记列表（仅含 id、标题和内容预览）。当用户想找某主题的笔记、回忆写过什么时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词（按笔记标题模糊匹配）"},
                    "limit": {"type": "integer", "description": "返回数量上限，默认 5", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_note_content",
            "description": "按笔记 ID 获取笔记的完整内容（含 title、content、tags）。用户提到某篇笔记但未提供内容时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "笔记ID"}
                },
                "required": ["note_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_note",
            "description": "对一篇笔记做总结分析，返回 summary、strengths、weaknesses、suggestions。需要传入笔记全文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "笔记全文内容"}
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_note",
            "description": "根据主题生成新的学习笔记，返回 Markdown 格式的笔记内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "笔记主题"},
                    "keywords": {"type": "string", "description": "重点关注的关键词（可选）"},
                    "word_count": {"type": "integer", "description": "字数要求，默认 600", "default": 600},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_note",
            "description": "将笔记内容翻译为指定语言，保留 Markdown 结构。需要传入笔记全文和目标语言代码。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "笔记全文内容"},
                    "target_lang": {"type": "string", "description": "目标语言代码：zh/en/ja/ko/fr/es"},
                },
                "required": ["content", "target_lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "创建新笔记并保存到数据库。用户希望「保存为笔记」「加入我的笔记」「保存到我的笔记」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "笔记标题"},
                    "content": {"type": "string", "description": "笔记内容（Markdown 或 HTML）"},
                    "tags": {"type": "string", "description": "标签（逗号分隔，可选）"},
                },
                "required": ["title", "content"],
            },
        },
    },
]


NOTE_ASSISTANT_SYSTEM_PROMPT = """你是 NoteMind「笔记助手」，一个帮助用户管理和处理学习笔记的智能助手。

## 你的职责
- 理解用户的需求，选择合适的工具完成任务
- 搜索笔记、总结笔记、生成笔记、翻译笔记、创建思维导图
- 将工具执行结果整理成友好的回答呈现给用户

## 可用工具

| 工具 | 功能 | 适用场景 |
|------|------|---------|
| search_notes | 搜索笔记 | 用户想找某主题的笔记、回忆写过什么 |
| get_note_content | 获取笔记完整内容 | 用户提到某篇笔记但未提供内容 |
| summarize_note | 总结笔记 | 用户要求总结、概括、提炼要点 |
| generate_note | 生成笔记 | 用户要求写一篇、创作、生成新笔记 |
| translate_note | 翻译笔记 | 用户要求翻译、翻译成其他语言 |
| create_note | 保存笔记 | 用户要求保存到我的笔记、加入我的笔记 |

## 工作原则
1. 分析用户意图，选择最合适的工具
2. 先搜索再获取：需要全文时先用 search_notes 找到笔记，再用 get_note_content 获取
3. 先获取再处理：总结、翻译、思维导图需要先获取笔记内容
4. 用户确认原则：在调用工具前，先向用户说明你要做什么，等待用户确认后再执行。例如："我将搜索关键词'机器学习'的笔记，确认搜索吗？"
5. 格式保真：翻译和总结时保留 Markdown 格式
6. 清晰输出：工具执行结果用清晰的格式呈现给用户
7. 诚实告知：没有找到匹配笔记时直接说明

## 回答风格
- 亲切、耐心、有鼓励性
- 使用清晰的 Markdown 格式
- 适当使用表情符号增加亲和力
- 简洁明了，不要废话
"""


class NoteAssistant(BaseAgent):
    name = "note_assistant"
    display_name = "Note助手"
    emoji = "📒"
    system_prompt = NOTE_ASSISTANT_SYSTEM_PROMPT
    tools_definition = NOTE_ASSISTANT_TOOLS

    async def run(
        self,
        message: str,
        history: Optional[List[Any]] = None,
        *,
        db: AsyncSession,
        db_user: UserDB,
    ) -> AsyncIterator[str]:
        yield sse_event(
            "agent_start",
            {
                "agent": self.name,
                "display_name": self.display_name,
                "emoji": self.emoji,
                "reason": "开始处理您的请求",
            },
        )

        async for evt in super().run(message, history, db=db, db_user=db_user):
            try:
                payload = json.loads(evt[len("data: "):].strip())
                event_type = payload.get("type")

                if event_type == "tool_start":
                    tool_name = payload.get("tool", {}).get("name", "")
                    sub_agent_key = TOOL_TO_SUB_AGENT.get(tool_name)
                    if sub_agent_key and SUB_AGENTS.get(sub_agent_key):
                        sub_agent = SUB_AGENTS[sub_agent_key]
                        yield sse_event(
                            "sub_agent_start",
                            {
                                "agent": sub_agent_key,
                                "display_name": sub_agent["display_name"],
                                "emoji": sub_agent["emoji"],
                                "tool": tool_name,
                            },
                        )
                elif event_type == "tool_end":
                    tool_name = payload.get("tool", {}).get("name", "")
                    sub_agent_key = TOOL_TO_SUB_AGENT.get(tool_name)
                    if sub_agent_key and SUB_AGENTS.get(sub_agent_key):
                        sub_agent = SUB_AGENTS[sub_agent_key]
                        yield sse_event(
                            "sub_agent_end",
                            {
                                "agent": sub_agent_key,
                                "display_name": sub_agent["display_name"],
                                "emoji": sub_agent["emoji"],
                                "tool": tool_name,
                            },
                        )
            except Exception:
                pass

            yield evt

        yield sse_event("agent_end", {"agent": self.name, "display_name": self.display_name})
