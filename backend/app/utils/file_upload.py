"""图片上传安全工具。

- 扩展名白名单
- 文件魔数（magic number）校验，防止伪装图片
- 文件名安全化（去除路径、保留扩展名）
"""
from __future__ import annotations

import mimetypes
import os
import secrets
from typing import Tuple

# 允许的扩展名 -> 对应的魔数（bytes）
# 参考：https://en.wikipedia.org/wiki/List_of_file_signatures
_SAFE_IMAGE_TYPES: dict[str, list[bytes]] = {
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".webp": [b"RIFF"],  # WEBP 文件以 "RIFF" 开头，第 8-11 字节为 "WEBP"
}


def _normalize_extension(filename: str) -> str:
    """统一取小写扩展名，含前导点号。已做路径清洗。"""
    safe_name = os.path.basename(filename or "")
    ext = os.path.splitext(safe_name)[1].lower()
    return ext


def validate_image_bytes(
    file_bytes: bytes,
    filename: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> Tuple[bool, str, str]:
    """校验图片文件。

    返回: (是否安全, 标准化扩展名, 错误信息)
    """
    # 1. 扩展名白名单
    ext = _normalize_extension(filename)
    if ext not in _SAFE_IMAGE_TYPES:
        return (
            False,
            ext,
            f"不支持的图片格式：{ext or '（无扩展名）'}；仅支持 {', '.join(_SAFE_IMAGE_TYPES.keys())}",
        )

    # 2. 文件大小
    if len(file_bytes) == 0:
        return False, ext, "上传的文件为空"
    if len(file_bytes) > max_bytes:
        return False, ext, f"文件超过上限 {max_bytes // 1024 // 1024}MB"

    # 3. 魔数校验：读取文件前 16 字节，与对应扩展名的签名做对比
    head = file_bytes[:16]
    expected_signatures = _SAFE_IMAGE_TYPES[ext]
    matched = any(head.startswith(sig) for sig in expected_signatures)

    # WEBP 特殊二次校验：必须在 8~12 字节位置包含 "WEBP"
    if matched and ext == ".webp":
        if len(file_bytes) < 12 or file_bytes[8:12] != b"WEBP":
            matched = False

    if not matched:
        return False, ext, "文件内容与扩展名不匹配，可能被篡改或非图片"

    # 4. 推导 MIME（作为附加兜底）
    mime, _ = mimetypes.guess_type(f"file{ext}")
    if mime is None or not mime.startswith("image/"):
        return False, ext, "无法识别为图片类型"

    return True, ext, ""


def safe_image_filename(original_filename: str, ext: str) -> str:
    """生成随机且安全的文件名（避免路径遍历、XSS 文件名）。"""
    safe_ext = ext if ext.startswith(".") else f".{ext.lstrip('.')}"
    # 使用随机 hex 作为文件名，防止遍历/覆盖
    return f"{secrets.token_hex(16)}{safe_ext}"
