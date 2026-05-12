"""
笔记生成服务
负责 AI 生成笔记内容
"""
from app.core.config import settings
from openai import OpenAI
from .prompts import NOTE_GENERATION_SYSTEM_PROMPT

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url=settings.LM_STUDIO_URL,
    api_key="not-needed"
)


def generate_note_stream(topic: str, keyword: str = None, reference_notes: list = None, 
                        images: list = None, word_count: int = 600):
    """
    流式生成笔记内容（生成器函数）
    
    :param topic: 笔记主题
    :param keyword: 补充关键词（可选）
    :param reference_notes: 参考笔记列表，每项包含 {filename, content}
    :param images: 图片 base64 列表（预留）
    :param word_count: 期望的字数（默认600字）
    :yield: 生成的文本片段
    """
    user_prompt = _build_generation_prompt(topic, keyword, reference_notes, word_count)
    
    try:
        response = client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": NOTE_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=word_count * 3,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        raise Exception(f"AI生成笔记失败：{str(e)}")


def generate_note(topic: str, keyword: str = None, reference_notes: list = None, 
                 images: list = None, word_count: int = 600) -> str:
    """
    根据主题、关键词、参考笔记和图片，AI生成高质量笔记内容
    
    :param topic: 笔记主题
    :param keyword: 补充关键词（可选）
    :param reference_notes: 参考笔记列表，每项包含 {filename, content}
    :param images: 图片 base64 列表（预留）
    :param word_count: 期望的字数（默认600字）
    :return: 生成的 Markdown 格式笔记内容
    """
    user_prompt = _build_generation_prompt(topic, keyword, reference_notes, word_count)
    
    try:
        response = client.chat.completions.create(
            model=settings.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": NOTE_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=word_count * 3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"AI生成笔记失败：{str(e)}")


def _build_generation_prompt(topic: str, keyword: str = None, 
                            reference_notes: list = None, word_count: int = 600) -> str:
    """
    构建笔记生成的用户提示词
    
    :param topic: 笔记主题
    :param keyword: 补充关键词
    :param reference_notes: 参考笔记列表
    :param word_count: 期望字数
    :return: 完整的用户提示词
    """
    user_prompt = f"请为主题「{topic}」生成一篇学习笔记。"
    
    if keyword:
        user_prompt += f"\n\n重点关注的关键词：{keyword}"
    
    # 添加参考笔记
    if reference_notes and len(reference_notes) > 0:
        user_prompt += "\n\n以下是参考材料，请结合这些内容生成笔记：\n"
        for i, note in enumerate(reference_notes, 1):
            user_prompt += f"\n【参考资料{i} - {note.get('filename', '未知文件')}】\n"
            content = note.get('content', '')
            if len(content) > 2000:
                content = content[:2000] + "...（内容过长，已截断）"
            user_prompt += content
    
    # 添加结构要求
    user_prompt += "\n\n请按照以下结构生成笔记：\n"
    user_prompt += "1. 核心概念介绍\n"
    user_prompt += "2. 关键知识点详解（分点阐述）\n"
    user_prompt += "3. 实际应用或示例\n"
    user_prompt += "4. 总结与复习要点\n"
    
    # 添加字数要求
    min_words = max(300, word_count - 100)
    max_words = word_count + 100
    user_prompt += f"\n字数要求：{min_words}-{max_words}字左右\n"
    
    return user_prompt
