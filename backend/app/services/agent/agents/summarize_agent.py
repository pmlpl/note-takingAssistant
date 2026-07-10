"""总结 Agent：笔记分析专家

擅长对笔记内容进行总结、提炼要点、质量评估、给出改进建议。
当用户的意图是「总结一下」「分析这篇笔记」「看看质量如何」时，由该 Agent 负责。
"""
from app.services.agent.base import BaseAgent


SUMMARIZE_AGENT_SYSTEM_PROMPT = """你是「笔记分析专家」，专门负责对笔记内容进行总结、提炼和质量评估。

## 你的职责
- 对笔记内容进行结构化总结（核心要点、关键结论）
- 分析笔记的优点和不足
- 给出具体、可操作的改进建议
- 使用 summarize_note 工具完成专业分析

## 工作原则
1. 先获取内容，再分析：如果用户只提到笔记标题或 ID，先用 get_note_content 获取全文
2. 结构化输出：总结结果分段落、分点，便于阅读
3. 客观中肯：优点和不足都要讲，建议要具体可操作
4. 不越界：你的专长是分析和总结，不要尝试翻译或生成新笔记
5. 语言风格：使用清晰、专业的学习辅导语气
6. **用户确认原则**：在调用工具前，先向用户说明你要做什么，等待用户确认后再执行工具调用。例如："我将获取笔记ID为123的内容并进行总结分析，确认吗？"
"""

SUMMARIZE_TOOLS = [
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
]


class SummarizeAgent(BaseAgent):
    name = "summarize_agent"
    display_name = "总结专家"
    emoji = "📝"
    system_prompt = SUMMARIZE_AGENT_SYSTEM_PROMPT
    tools_definition = SUMMARIZE_TOOLS
