"""意图分类 Agent：让 LLM 通过 Function Calling 选择专业 Agent

主流的 Agent 架构不使用关键词匹配，而是让 LLM 通过工具选择来决定调用哪个 Agent。
这才是正确的方式。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDB
from app.services.agent.agents import AGENTS
from app.services.agent.base import sse_event
from app.services.llm_runtime import openai_client_and_model_for_user
from app.utils.llm_errors import format_llm_error

logger = logging.getLogger(__name__)


INTENT_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "use_general_agent",
            "description": "使用通用助手：处理闲聊、问答、学习方法建议、不明确的问题",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use_search_agent",
            "description": "使用搜索专家：搜索笔记、查找内容、回忆写过什么",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use_summarize_agent",
            "description": "使用总结专家：总结笔记、分析笔记、提炼要点、质量评估",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use_generate_agent",
            "description": "使用生成专家：生成笔记、创作学习笔记、保存笔记",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use_translate_agent",
            "description": "使用翻译专家：翻译笔记、多语言转换",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use_mindmap_agent",
            "description": "使用思维导图专家：生成思维导图、结构化梳理",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

TOOL_TO_AGENT_MAP = {
    "use_general_agent": "general",
    "use_search_agent": "search",
    "use_summarize_agent": "summarize",
    "use_generate_agent": "generate",
    "use_translate_agent": "translate",
    "use_mindmap_agent": "mindmap",
}

INTENT_CLASSIFICATION_SYSTEM_PROMPT = """你是一个智能调度员，负责根据用户的请求选择最合适的 AI 助手。

## 可用助手列表

| 助手 | 适用场景 |
|------|---------|
| 通用助手 | 闲聊、问答、学习方法建议、不明确的问题、无法归类的问题 |
| 搜索专家 | 搜索笔记、查找内容、回忆写过什么、找某篇笔记 |
| 总结专家 | 总结笔记、分析笔记、提炼要点、质量评估、改进建议 |
| 生成专家 | 生成笔记、写一篇关于...的笔记、创作学习笔记、保存笔记到笔记库 |
| 翻译专家 | 翻译笔记、翻译成英文/日文/中文等、多语言转换 |
| 思维导图专家 | 思维导图、结构化梳理、知识可视化、整理成 Mermaid |

## 工作原则

1. 根据用户的具体请求选择最合适的助手
2. 如果用户说"保存到我的笔记""帮我保存"，选择生成专家
3. 如果用户说"总结""概括""提炼"，选择总结专家
4. 如果用户说"翻译""translate"，选择翻译专家
5. 如果用户说"思维导图""脑图"，选择思维导图专家
6. 如果用户说"搜索""查找""找笔记"，选择搜索专家
7. 如果用户说"生成""写一篇""创作"，选择生成专家
8. 如果用户的问题不明确或不属于以上类别，选择通用助手

## 输出格式

必须调用 use_xxx_agent 工具，不要直接回答用户。
"""


async def classify_intent_with_tools(
    message: str, history: Optional[List[Any]], db_user: UserDB
) -> str:
    """通过 Function Calling 让 LLM 选择 Agent，返回 Agent 名称"""
    try:
        client, model = openai_client_and_model_for_user(db_user)
    except Exception as e:
        logger.warning(f"无法获取 LLM 客户端，使用通用 Agent: {e}")
        return "general"

    context_messages = [{"role": "system", "content": INTENT_CLASSIFICATION_SYSTEM_PROMPT}]
    recent = (history or [])[-3:]
    for msg in recent:
        if isinstance(msg, dict):
            role = str(msg.get("role") or "user")
            content = str(msg.get("content") or "")
        else:
            role = "user"
            content = str(getattr(msg, "content", "") or "")
        if role in ("user", "assistant"):
            context_messages.append({"role": role, "content": content})
    context_messages.append({"role": "user", "content": message})

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=context_messages,
            tools=INTENT_AGENT_TOOLS,
            tool_choice="required",
            temperature=0.1,
            max_tokens=200,
        )

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls and tool_calls[0]:
            tool_name = tool_calls[0].function.name
            agent_name = TOOL_TO_AGENT_MAP.get(tool_name, "general")
            logger.info(f"LLM 选择 Agent: {agent_name} (via {tool_name})")
            return agent_name

        return "general"
    except Exception as e:
        logger.warning(f"意图分类失败，使用通用 Agent: {e}")
        return "general"
