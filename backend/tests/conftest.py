"""Pytest: set required env before app modules load Settings()."""
import os

from cryptography.fernet import Fernet

# TestClient 会触发应用 lifespan；默认跳过 init_db / 迁移，避免本机未配置 MySQL 时失败。
# 需要连真实库做集成测试时：可在命令行设置 SKIP_APP_LIFESPAN=0 并提供可用 DB_*。
os.environ.setdefault("SKIP_APP_LIFESPAN", "1")

os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
