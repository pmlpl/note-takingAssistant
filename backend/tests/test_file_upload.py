"""文件上传校验与解析测试。

覆盖 app/utils/file_upload（图片魔数+扩展名校验、安全文件名）与
app/utils/file_parser（txt/md/docx 解析、标题提取）。
"""

from app.utils.file_parser import (
    extract_title_from_filename,
    parse_file,
    parse_markdown_file,
    parse_text_file,
)
from app.utils.file_upload import safe_image_filename, validate_image_bytes

PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG_MAGIC = b"\xff\xd8\xff\xe0" + b"\x00" * 32


class TestValidateImageBytes:
    def test_valid_png(self):
        ok, ext, err = validate_image_bytes(PNG_MAGIC, "photo.png")
        assert ok is True
        assert ext == ".png"
        assert not err

    def test_valid_jpg(self):
        ok, ext, _ = validate_image_bytes(JPEG_MAGIC, "photo.jpg")
        assert ok is True
        assert ext == ".jpg"

    def test_rejects_text_content_as_image(self):
        ok, _, err = validate_image_bytes(b"this is not an image", "photo.png")
        assert ok is False
        assert "不匹配" in err

    def test_rejects_empty_file(self):
        ok, _, err = validate_image_bytes(b"", "photo.png")
        assert ok is False
        assert "为空" in err

    def test_rejects_unsupported_extension(self):
        ok, _, err = validate_image_bytes(PNG_MAGIC, "photo.txt")
        assert ok is False
        assert "不支持" in err


class TestSafeImageFilename:
    def test_strips_path_and_uses_random_hex(self):
        name = safe_image_filename("../../etc/passwd.png", "png")
        assert name.endswith(".png")
        assert "/" not in name and "\\" not in name
        stem = name.split(".")[0]
        assert len(stem) == 32  # uuid4().hex

    def test_normalizes_extension_case(self):
        name = safe_image_filename("avatar", "PNG")
        assert name.split(".")[-1].lower() == "png"


class TestFileParser:
    def test_parse_txt(self, tmp_path):
        p = tmp_path / "note.txt"
        p.write_text("hello 笔记", encoding="utf-8")
        assert parse_text_file(str(p)) == "hello 笔记"

    def test_parse_txt_missing_file(self):
        assert parse_text_file("no_such_file_xyz.txt") is None

    def test_parse_markdown(self, tmp_path):
        p = tmp_path / "note.md"
        p.write_text("# 标题\n\n正文", encoding="utf-8")
        assert parse_markdown_file(str(p)) == "# 标题\n\n正文"

    def test_parse_file_routes_by_extension(self, tmp_path):
        p = tmp_path / "a.txt"
        p.write_text("hi", encoding="utf-8")
        assert parse_file(str(p), "a.txt") == "hi"

    def test_parse_file_unsupported_extension(self, tmp_path):
        p = tmp_path / "a.xyz"
        p.write_text("x", encoding="utf-8")
        assert parse_file(str(p), "a.xyz") is None

    def test_extract_title_strips_extension_and_path(self):
        assert extract_title_from_filename("我的笔记.md") == "我的笔记"
        assert extract_title_from_filename("dir/note.TXT") == "note"

    def test_extract_title_empty_fallback(self):
        assert extract_title_from_filename("") == "未命名笔记"
