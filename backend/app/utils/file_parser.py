"""
文件解析工具
支持导入 Word (.docx)、Markdown (.md)、Text (.txt) 等格式的文档
"""

import os
from typing import Optional

from app.core.logger import app_logger as logger


def parse_text_file(file_path: str) -> Optional[str]:
    """
    解析纯文本文件 (.txt)

    Args:
        file_path: 文件路径

    Returns:
        str: 文件内容，失败返回None
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        logger.info(f"❌ 解析TXT文件失败: {e}")
        return None


def parse_markdown_file(file_path: str) -> Optional[str]:
    """
    解析Markdown文件 (.md)

    Args:
        file_path: 文件路径

    Returns:
        str: Markdown内容，失败返回None
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        # Markdown可以直接作为HTML显示，或者后续可以转换为HTML
        return content
    except Exception as e:
        logger.info(f"❌ 解析MD文件失败: {e}")
        return None


def parse_word_file(file_path: str) -> Optional[str]:
    """
    解析Word文档 (.docx)
    使用 python-docx 库提取文本内容

    Args:
        file_path: 文件路径

    Returns:
        str: 提取的文本内容，失败返回None
    """
    try:
        from docx import Document

        doc = Document(file_path)

        # 提取所有段落的文本
        paragraphs = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # 跳过空段落
                paragraphs.append(paragraph.text)

        # 用换行符连接所有段落
        content = "\n\n".join(paragraphs)

        return content
    except ImportError:
        logger.info("❌ 未安装 python-docx 库，请运行: pip install python-docx")
        return None
    except Exception as e:
        logger.info(f"❌ 解析Word文件失败: {e}")
        return None


def parse_file(file_path: str, filename: str) -> Optional[str]:
    """
    根据文件扩展名自动选择解析器

    Args:
        file_path: 文件路径
        filename: 文件名（用于判断扩展名）

    Returns:
        str: 解析后的内容，失败返回None
    """
    safe_filename = os.path.basename(filename)
    ext = os.path.splitext(safe_filename)[1].lower()

    # 根据扩展名选择解析器
    if ext == ".txt":
        return parse_text_file(file_path)
    elif ext == ".md":
        return parse_markdown_file(file_path)
    elif ext == ".docx":
        return parse_word_file(file_path)
    else:
        logger.info(f"⚠️ 不支持的文件格式: {ext}")
        return None


def extract_title_from_filename(filename: str) -> str:
    """
    从文件名中提取标题（去掉扩展名），已做路径清洗

    Args:
        filename: 原始文件名

    Returns:
        str: 提取的标题
    """
    safe_name = os.path.basename(filename)
    title = os.path.splitext(safe_name)[0]

    if not title.strip():
        title = "未命名笔记"

    return title.strip()
