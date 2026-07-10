"""各专业 Agent 注册

AGENTS: {name: agent_instance} 的映射，供 Coordinator 调度。
"""
from app.services.agent.agents.general_agent import GeneralAgent
from app.services.agent.agents.search_agent import SearchAgent
from app.services.agent.agents.summarize_agent import SummarizeAgent
from app.services.agent.agents.generate_agent import GenerateAgent
from app.services.agent.agents.translate_agent import TranslateAgent
from app.services.agent.agents.mindmap_agent import MindmapAgent

# 单例实例（无状态，可复用）
general_agent = GeneralAgent()
search_agent = SearchAgent()
summarize_agent = SummarizeAgent()
generate_agent = GenerateAgent()
translate_agent = TranslateAgent()
mindmap_agent = MindmapAgent()

AGENTS = {
    "general": general_agent,
    "search": search_agent,
    "summarize": summarize_agent,
    "generate": generate_agent,
    "translate": translate_agent,
    "mindmap": mindmap_agent,
}

# Agent 显示名称映射（用于前端展示）
AGENT_DISPLAY_NAMES = {
    name: (agent.display_name, agent.emoji)
    for name, agent in AGENTS.items()
}


def get_agent(name: str) -> "BaseAgent":  # type: ignore  # noqa: F821
    """按名称获取 Agent 实例，不存在则返回通用 Agent"""
    return AGENTS.get(name, general_agent)
