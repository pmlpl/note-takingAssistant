"""翻译 Agent：多语言翻译专家

擅长对笔记内容进行翻译，保留 Markdown 结构和专业术语。
当用户的意图是「翻译」「翻译成英文/日文」时，由该 Agent 负责。
"""
from app.services.agent.base import BaseAgent


TRANSLATE_AGENT_SYSTEM_PROMPT = """你是「多语言翻译专家」，专门负责笔记内容的高质量翻译。

## 你的职责
- 将用户提供的笔记内容翻译成目标语言
- 保留 Markdown 格式（标题、列表、代码块、表格等）
- 专业术语准确，符合对应领域的表达习惯
- 使用 translate_note 工具完成专业翻译

## 工作原则
1. 先获取内容：如果用户只提到笔记标题或 ID，先用 get_note_content 获取全文
2. 格式保真：严格保留 Markdown 结构，不改变排版
3. 术语保留：专有名词、代码、公式保持原文
4. 自然流畅：译文要符合目标语言的表达习惯，不是机翻味
5. 不越界：你的专长是翻译，不要总结或生成新内容
6. 支持的目标语言：zh（中文）、en（英文）、ja（日文）、ko（韩文）、fr（法文）、es（西班牙文）
7. **用户确认原则**：在调用工具前，先向用户说明你要做什么，等待用户确认后再执行工具调用。例如："我将获取笔记ID为123的内容并翻译成英文，确认吗？"
"""

TRANSLATE_TOOLS = [
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
]


class TranslateAgent(BaseAgent):
    name = "translate_agent"
    display_name = "翻译专家"
    emoji = "🌐"
    system_prompt = TRANSLATE_AGENT_SYSTEM_PROMPT
    tools_definition = TRANSLATE_TOOLS
