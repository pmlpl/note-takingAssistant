"""
手动迁移：为 users 表添加 LLM / BYOK 列（与启动时 ensure_user_llm_columns 一致）。
在 backend 目录下: python migrations/add_user_llm_settings.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal
from app.core.startup_migrations import ensure_user_llm_columns


async def migrate():
    async with AsyncSessionLocal() as session:
        await ensure_user_llm_columns(session)
        await session.commit()
    print("✓ users LLM / BYOK 列已就绪")


if __name__ == "__main__":
    asyncio.run(migrate())
