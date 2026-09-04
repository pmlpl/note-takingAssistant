"""app.utils.file_parser 测试

使用临时文件测试文本、Markdown 解析，以及文件名提取标题。
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from app.utils.file_parser import (
    extract_title_from_filename,
    parse_file,
    parse_markdown_file,
    parse_text_file,
    parse_word_file,
)


# ============== parse_text_file ==============

def test_parse_text_file_success():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Hello World\nThis is a text file.")
        path = f.name
    try:
        content = parse_text_file(path)
        assert content == "Hello World\nThis is a text file."
    finally:
        os.unlink(path)


def test_parse_text_file_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("")
        path = f.name
    try:
        content = parse_text_file(path)
        assert content == ""
    finally:
        os.unlink(path)


def test_parse_text_file_not_found():
    content = parse_text_file("/nonexistent/path/file.txt")
    assert content is None


def test_parse_text_file_unicode():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("中文内容\n特殊字符：±∞→")
        path = f.name
    try:
        content = parse_text_file(path)
        assert "中文内容" in content
        assert "±∞→" in content
    finally:
        os.unlink(path)


# ============== parse_markdown_file ==============

def test_parse_markdown_file_success():
    md_content = "# Title\n\nThis is **bold** and *italic*.\n\n- Item 1\n- Item 2"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md_content)
        path = f.name
    try:
        content = parse_markdown_file(path)
        assert content == md_content
        assert "# Title" in content
        assert "**bold**" in content
    finally:
        os.unlink(path)


def test_parse_markdown_file_not_found():
    content = parse_markdown_file("/nonexistent/path/file.md")
    assert content is None


def test_parse_markdown_file_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("")
        path = f.name
    try:
        content = parse_markdown_file(path)
        assert content == ""
    finally:
        os.unlink(path)


# ============== parse_word_file ==============

def test_parse_word_file_not_found():
    content = parse_word_file("/nonexistent/path/file.docx")
    assert content is None


def test_parse_word_file_invalid_file():
    # 创建一个不是有效 docx 的文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".docx", delete=False, encoding="utf-8") as f:
        f.write("This is not a real docx file")
        path = f.name
    try:
        content = parse_word_file(path)
        assert content is None
    finally:
        os.unlink(path)


def test_parse_word_file_import_error():
    # 模拟 python-docx 未安装
    with patch("builtins.__import__", side_effect=ImportError("No module named 'docx'")):
        content = parse_word_file("test.docx")
        assert content is None


# ============== parse_file (自动选择解析器) ==============

def test_parse_file_txt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Text content")
        path = f.name
    try:
        content = parse_file(path, "document.txt")
        assert content == "Text content"
    finally:
        os.unlink(path)


def test_parse_file_md():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Markdown")
        path = f.name
    try:
        content = parse_file(path, "document.md")
        assert content == "# Markdown"
    finally:
        os.unlink(path)


def test_parse_file_unsupported_extension():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False, encoding="utf-8") as f:
        f.write("PDF content")
        path = f.name
    try:
        content = parse_file(path, "document.pdf")
        assert content is None
    finally:
        os.unlink(path)


def test_parse_file_case_insensitive_extension():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".TXT", delete=False, encoding="utf-8") as f:
        f.write("UPPER CASE EXT")
        path = f.name
    try:
        content = parse_file(path, "DOCUMENT.TXT")
        assert content == "UPPER CASE EXT"
    finally:
        os.unlink(path)


def test_parse_file_path_traversal_safe():
    # 文件名包含路径应该只取 basename
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("safe content")
        path = f.name
    try:
        content = parse_file(path, "../../../etc/passwd.txt")
        # 扩展名是 .txt，应该能解析
        assert content == "safe content"
    finally:
        os.unlink(path)


def test_parse_file_no_extension():
    with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False, encoding="utf-8") as f:
        f.write("no ext")
        path = f.name
    try:
        content = parse_file(path, "README")
        assert content is None
    finally:
        os.unlink(path)


# ============== extract_title_from_filename ==============

def test_extract_title_simple():
    assert extract_title_from_filename("my-note.md") == "my-note"


def test_extract_title_with_path():
    assert extract_title_from_filename("/path/to/my-note.md") == "my-note"


def test_extract_title_windows_path():
    assert extract_title_from_filename("C:\\Users\\Docs\\note.txt") == "note"


def test_extract_title_multiple_dots():
    assert extract_title_from_filename("my.note.title.md") == "my.note.title"


def test_extract_title_no_extension():
    assert extract_title_from_filename("README") == "README"


def test_extract_title_empty_name():
    # .md 的 basename 是 .md，splitext 得到 ('.md', '')
    result = extract_title_from_filename(".md")
    assert result == ".md"


def test_extract_title_only_dot():
    result = extract_title_from_filename(".")
    assert result == "."


def test_extract_title_whitespace_name():
    assert extract_title_from_filename("  .txt") == "未命名笔记"


def test_extract_title_strips_whitespace():
    assert extract_title_from_filename("  My Note  .md") == "My Note"


def test_extract_title_unicode():
    assert extract_title_from_filename("学习笔记.md") == "学习笔记"


def test_extract_title_special_chars():
    assert extract_title_from_filename("note-2024_01!@#.md") == "note-2024_01!@#"


def test_extract_title_traversal_path():
    assert extract_title_from_filename("../../../etc/passwd") == "passwd"
