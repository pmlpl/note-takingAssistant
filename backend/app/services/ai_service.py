from app.core.config import settings
import json
from openai import OpenAI

# 初始化 OpenAI 客户端（兼容 LM Studio 和 Ollama）
# LM Studio: http://localhost:1234/v1
# Ollama: http://localhost:11434/v1
client = OpenAI(
    base_url=settings.LM_STUDIO_URL,  # 从配置文件读取LM Studio地址
    api_key="not-needed"  # LM Studio 不需要 API key
)


# ==================== 系统提示词模板 ====================

# AI 笔记生成专家的系统角色定义
NOTE_GENERATION_SYSTEM_PROMPT = """你是一位专业的学习笔记助手，专门为大学生和自学者创建高质量的学习笔记。

你的特点：
1. 结构清晰：使用标题、列表、重点标注等方式组织内容
2. 深入浅出：用通俗易懂的语言解释复杂概念
3. 实用导向：注重知识点的实际应用和考试要点
4. 格式规范：使用 Markdown 格式，包含适当的标题层级、列表、代码块等

输出要求：
- 使用 Markdown 格式
- 包含清晰的标题层级（# ## ###）
- 重要概念使用 **加粗** 标注
- 代码示例使用 ```代码块```
- 适当使用列表（有序/无序）
- 字数控制在 500-800 字
- 语言简洁明了，适合学习复习"""

# AI 笔记分析专家的系统角色定义
NOTE_ANALYSIS_SYSTEM_PROMPT = """你是一位经验丰富的学习笔记评审专家，擅长评估笔记质量并提供改进建议。

你的分析维度：
1. 内容完整性：是否覆盖了主题的核心知识点
2. 结构清晰度：逻辑是否清晰，层次是否分明
3. 表达准确性：概念解释是否准确，语言是否通顺
4. 实用性：是否便于复习和理解

输出要求：
- 必须返回严格的 JSON 格式
- summary: 150字以内的精炼总结
- strengths: 3个优点（具体、有针对性）
- weaknesses: 3个不足（建设性批评）
- suggestions: 3条改进建议（可操作、具体）
- 所有评价都要基于笔记实际内容，避免空泛"""


def ai_generate_note_stream(topic: str, keyword: str = None, reference_notes: list = None, images: list = None, word_count: int = 600):
    """
    流式生成笔记内容（生成器函数）
    
    :param topic: 笔记主题
    :param keyword: 补充关键词（可选）
    :param reference_notes: 参考笔记列表，每项包含 {filename, content}
    :param images: 图片 base64 列表（预留，当前版本暂不支持图片识别）
    :param word_count: 期望的字数（默认600字）
    :yield: 生成的文本片段
    """
    # 构建用户提示词
    user_prompt = f"请为主题「{topic}」生成一篇学习笔记。"
    
    if keyword:
        user_prompt += f"\n\n重点关注的关键词：{keyword}"
    
    # 如果有参考笔记，加入提示词
    if reference_notes and len(reference_notes) > 0:
        user_prompt += "\n\n以下是参考材料，请结合这些内容生成笔记：\n"
        for i, note in enumerate(reference_notes, 1):
            user_prompt += f"\n【参考资料{i} - {note.get('filename', '未知文件')}】\n"
            # 限制参考内容的长度，避免超出 token 限制
            content = note.get('content', '')
            if len(content) > 2000:
                content = content[:2000] + "...（内容过长，已截断）"
            user_prompt += content
    
    user_prompt += "\n\n请按照以下结构生成笔记：\n"
    user_prompt += "1. 核心概念介绍\n"
    user_prompt += "2. 关键知识点详解（分点阐述）\n"
    user_prompt += "3. 实际应用或示例\n"
    user_prompt += "4. 总结与复习要点\n"
    
    # 添加字数要求
    min_words = max(300, word_count - 100)
    max_words = word_count + 100
    user_prompt += f"\n字数要求：{min_words}-{max_words}字左右\n"
    
    try:
        # 使用流式 API
        response = client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": NOTE_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=word_count * 3,
            stream=True  # 启用流式输出
        )
        
        # 逐块返回内容
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        raise Exception(f"AI生成笔记失败：{str(e)}")


def ai_generate_note(topic: str, keyword: str = None, reference_notes: list = None, images: list = None, word_count: int = 600) -> str:
    """
    根据主题、关键词、参考笔记和图片，AI生成高质量笔记内容
    
    :param topic: 笔记主题
    :param keyword: 补充关键词（可选）
    :param reference_notes: 参考笔记列表，每项包含 {filename, content}
    :param images: 图片 base64 列表（预留，当前版本暂不支持图片识别）
    :param word_count: 期望的字数（默认600字）
    :return: 生成的 Markdown 格式笔记内容
    """
    # 构建用户提示词
    user_prompt = f"请为主题「{topic}」生成一篇学习笔记。"
    
    if keyword:
        user_prompt += f"\n\n重点关注的关键词：{keyword}"
    
    # 如果有参考笔记，加入提示词
    if reference_notes and len(reference_notes) > 0:
        user_prompt += "\n\n以下是参考材料，请结合这些内容生成笔记：\n"
        for i, note in enumerate(reference_notes, 1):
            user_prompt += f"\n【参考资料{i} - {note.get('filename', '未知文件')}】\n"
            # 限制参考内容的长度，避免超出 token 限制
            content = note.get('content', '')
            if len(content) > 2000:
                content = content[:2000] + "...（内容过长，已截断）"
            user_prompt += content
    
    user_prompt += "\n\n请按照以下结构生成笔记：\n"
    user_prompt += "1. 核心概念介绍\n"
    user_prompt += "2. 关键知识点详解（分点阐述）\n"
    user_prompt += "3. 实际应用或示例\n"
    user_prompt += "4. 总结与复习要点\n"
    
    # 添加字数要求
    min_words = max(300, word_count - 100)
    max_words = word_count + 100
    user_prompt += f"\n字数要求：{min_words}-{max_words}字左右\n"
    
    try:
        response = client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,  # 使用LM Studio配置的模型名称
            messages=[
                {"role": "system", "content": NOTE_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=word_count * 3  # 根据期望字数动态设置
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"AI生成笔记失败：{str(e)}")


def ai_summarize_note(content: str) -> dict:
    """
    对笔记内容进行AI全面分析，包括总结、字数统计、优缺点和建议
    
    :param content: 笔记原文（Markdown 格式）
    :return: 包含summary、strengths、weaknesses、suggestions的字典
    """
    # 限制内容长度，避免超出 token 限制
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
        
        # 尝试提取 JSON 部分（可能包含```json标记）
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        # 尝试修复常见的 JSON 格式问题
        # 移除末尾可能的逗号
        result_text = result_text.rstrip(',')
        
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            # 如果解析失败，尝试更宽松的解析
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
        # JSON 解析失败，返回友好错误
        raise Exception(f"AI 返回格式错误，请重试。错误信息：{str(e)}")
    except Exception as e:
        raise Exception(f"AI分析失败：{str(e)}")


def ai_chat(message: str, history: list = None) -> str:
    """
    AI 对话功能，支持上下文聊天
    
    :param message: 用户当前消息
    :param history: 聊天历史列表，每项包含 {role, content}
    :return: AI 回复内容
    """
    # 系统提示词 - 定义 AI 助手的角色
    system_prompt = """你是一位智能笔记助手，专门帮助用户管理和优化学习笔记。

你的能力：
1. 回答关于学习方法、笔记技巧的问题
2. 帮助总结和优化笔记内容
3. 提供学习建议和知识解释
4. 协助整理和组织笔记结构

你的特点：
- 友好、专业、耐心
- 回答简洁明了，重点突出
- 适当使用 Markdown 格式增强可读性
- 鼓励用户主动学习和思考

注意：
- 如果用户询问与笔记无关的问题，友好地引导回学习主题
- 保持回答的实用性和可操作性
- 避免过于冗长的回答"""
    
    # 构建消息列表
    messages = [{"role": "system", "content": system_prompt}]
    
    # 添加聊天历史（最多保留最近 10 轮对话）
    if history:
        for msg in history[-10:]:
            # msg 可能是字典或 ChatMessage 对象
            if isinstance(msg, dict):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            else:
                # ChatMessage 对象，直接访问属性
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
