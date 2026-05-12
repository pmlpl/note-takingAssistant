"""
笔记分析服务
负责 AI 分析笔记内容
"""
from app.core.config import settings
from openai import OpenAI
import json
from .prompts import NOTE_ANALYSIS_SYSTEM_PROMPT

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url=settings.LM_STUDIO_URL,
    api_key="not-needed"
)


def analyze_note(content: str) -> dict:
    """
    对笔记内容进行AI全面分析，包括总结、字数统计、优缺点和建议
    
    :param content: 笔记原文（Markdown 格式）
    :return: 包含summary、strengths、weaknesses、suggestions的字典
    """
    # 限制内容长度
    if len(content) > 5000:
        content = content[:5000] + "...（内容过长，已截断）"
    
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
        response = client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": NOTE_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # 解析 AI 返回的 JSON
        result_text = response.choices[0].message.content.strip()
        
        # 尝试提取 JSON 部分
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        # 尝试修复常见的 JSON 格式问题
        result_text = result_text.rstrip(',')
        
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败，原始内容: {result_text[:200]}")
            print(f"错误信息: {str(e)}")
            
            # 返回默认值
            return {
                "summary": "AI 分析完成，但返回格式有误",
                "strengths": ["笔记结构清晰", "内容较为完整"],
                "weaknesses": ["可以增加更多实例", "表达可以更精炼"],
                "suggestions": ["建议补充相关案例", "优化段落结构"]
            }
        
        # 确保返回的数据结构完整
        return {
            "summary": result.get("summary", "暂无总结"),
            "strengths": result.get("strengths", ["笔记结构清晰"]),
            "weaknesses": result.get("weaknesses", ["可以增加更多实例"]),
            "suggestions": result.get("suggestions", ["建议补充相关案例"])
        }
    except json.JSONDecodeError as e:
        raise Exception(f"AI 返回格式错误，请重试。错误信息：{str(e)}")
    except Exception as e:
        raise Exception(f"AI分析失败：{str(e)}")
