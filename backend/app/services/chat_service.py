"""
AI 聊天服务
负责 AI 对话功能
"""
from app.core.config import settings
from openai import OpenAI
from .prompts import CHAT_SYSTEM_PROMPT

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url=settings.LM_STUDIO_URL,
    api_key="not-needed"
)


def chat_with_ai(message: str, history: list = None) -> str:
    """
    AI 对话功能，支持上下文聊天
    
    :param message: 用户当前消息
    :param history: 聊天历史列表，每项包含 {role, content}
    :return: AI 回复内容
    """
    # 构建消息列表
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    
    # 添加聊天历史（最多保留最近 10 轮对话）
    if history:
        for msg in history[-10:]:
            if isinstance(msg, dict):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            else:
                # ChatMessage 对象
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"AI对话失败：{str(e)}")
