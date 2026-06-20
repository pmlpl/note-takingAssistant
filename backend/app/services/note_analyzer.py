"""
笔记分析服务
负责 AI 分析笔记内容（异步 OpenAI 客户端）
"""
import json
from typing import Any, Dict

from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.utils.llm_errors import format_llm_error
from .prompts import NOTE_ANALYSIS_SYSTEM_PROMPT
from app.core.logger import app_logger as logger


async def analyze_note(content: str, *, db_user: UserDB) -> Dict[str, Any]:
    """
    对笔记内容进行 AI 分析，返回总结、优缺点和建议。
    """

    user_prompt = f"""请对以下学习笔记进行专业分析和评估：

【笔记内容】
{content}

请从以下几个维度进行分析：
1. 内容完整性：是否覆盖了主题的核心知识点
2. 结构清晰度：逻辑是否清晰，层次是否分明
3. 表达准确性：概念解释是否准确，语言是否通顺
4. 实用性：是否便于复习和理解

请以严格的 JSON 格式返回分析结果，不要包含其他文字或 Markdown 标记。"""

    try:
        client, model = openai_client_and_model_for_user(db_user)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": NOTE_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content
        result_text = (raw or "").strip()

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result_text = result_text.rstrip(",")

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            logger.info(f"JSON 解析失败，原始内容: {result_text[:200]}")
            logger.info(f"错误信息: {str(e)}")
            return {
                "summary": "AI 分析完成，但返回格式有误",
                "strengths": ["笔记结构清晰", "内容较为完整"],
                "weaknesses": ["可以增加更多实例", "表达可以更精炼"],
                "suggestions": ["建议补充相关案例", "优化段落结构"],
            }

        return {
            "summary": result.get("summary", "暂无总结"),
            "strengths": result.get("strengths", ["笔记结构清晰"]),
            "weaknesses": result.get("weaknesses", ["可以增加更多实例"]),
            "suggestions": result.get("suggestions", ["建议补充相关案例"]),
        }
    except Exception as e:
        raise Exception(format_llm_error("AI分析", e)) from e
