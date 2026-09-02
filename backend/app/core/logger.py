"""结构化日志：统一替换 `print` 调用。"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "app", log_file: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """创建 / 获取一个带时间戳的结构化日志器。"""
    logger = logging.getLogger(name)
    if logger.handlers:  # 已经配置过，避免重复
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件（可选）
    if log_file:
        fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# 默认应用级 logger
app_logger = setup_logger("app")
