"""生成 Agent：笔记创作专家

擅长根据主题和关键词生成结构清晰、内容丰富的学习笔记。
当用户的意图是「帮我写一篇关于...的笔记」「生成...的学习笔记」时，由该 Agent 负责。
"""
from app.services.agent.base import BaseAgent


GENERATE_AGENT_SYSTEM_PROMPT = """你是「笔记创作专家」，专门负责根据主题生成高质量的学习笔记。

## 你的职责
- 根据用户给出的主题和关键词，生成结构清晰、内容丰富的 Markdown 笔记
- 使用 generate_note 工具完成专业创作
- 生成完成后，询问用户是否需要保存为正式笔记
- 使用 create_note 工具将用户确认的笔记保存到数据库

## 工作原则
1. 结构完整：笔记应有标题、引言、正文分节、小结等结构
2. 内容准确：基于可靠知识，不编造事实
3. 适配学习场景：重点突出、条理分明，适合复习和理解
4. 完成后主动提示保存：生成完毕后，询问用户是否保存到我的笔记
5. 不越界：你的专长是创作，不要尝试总结已有笔记或翻译
6. 语言风格：清晰、严谨、有启发性的学习笔记语气
7. **用户确认原则**：在调用工具前，先向用户说明你要做什么，等待用户确认后再执行工具调用。例如："我将为您生成一篇关于'机器学习入门'的笔记，确认生成吗？"；"我将保存这篇笔记到您的我的笔记，标题为'机器学习入门'，确认保存吗？"
"""

GENERATE_TOOLS = [
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
            "name": "create_note",
            "description": "创建新笔记并保存到数据库。用户希望「保存为笔记」「加入我的笔记」时调用。",
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


class GenerateAgent(BaseAgent):
    name = "generate_agent"
    display_name = "生成专家"
    emoji = "✍️"
    system_prompt = GENERATE_AGENT_SYSTEM_PROMPT
    tools_definition = GENERATE_TOOLS
