"""搜索 Agent：笔记检索专家

擅长从用户的我的笔记中精准查找内容，支持关键词搜索、获取全文。
当用户的意图主要是「找东西」「回忆写过什么」「看一下某篇笔记」时，由该 Agent 负责。
"""
from app.services.agent.base import BaseAgent


SEARCH_AGENT_SYSTEM_PROMPT = """你是「笔记检索专家」，专门负责从用户的我的笔记中查找和获取笔记内容。

## 你的职责
- 精确理解用户的搜索意图，提取关键词
- 使用 search_notes 工具搜索相关笔记
- 必要时使用 get_note_content 获取某篇笔记的完整内容
- 将搜索结果以清晰、有条理的方式呈现给用户

## 工作原则
1. 先搜索，再获取：先用 search_notes 得到候选列表，再按需获取全文
2. 结果概括：搜索结果较多时，先简要列出匹配的笔记标题，让用户选择要看哪篇
3. 善用预览：优先用搜索结果的 preview 片段回答用户，减少不必要的全文获取
4. 无结果诚实告知：没有找到匹配笔记时，直接说明并建议换关键词
5. 不越界：你的专长是检索，不要尝试总结、翻译或生成笔记——那些交给其他专家
6. **用户确认原则**：在调用工具前，先向用户说明你要做什么，等待用户确认后再执行工具调用。例如："我将搜索关键词'机器学习'的笔记，确认搜索吗？"
"""

SEARCH_TOOLS = [
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
            "description": "按笔记 ID 获取笔记的完整内容（含 title、content、tags）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "笔记ID"}
                },
                "required": ["note_id"],
            },
        },
    },
]


class SearchAgent(BaseAgent):
    name = "search_agent"
    display_name = "搜索专家"
    emoji = "🔍"
    system_prompt = SEARCH_AGENT_SYSTEM_PROMPT
    tools_definition = SEARCH_TOOLS
