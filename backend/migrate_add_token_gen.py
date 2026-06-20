"""
数据库迁移脚本：给 users 表补齐缺失的 token_gen 列。

用法：
    python migrate_add_token_gen.py
    # 或
    .venv\Scripts\python.exe migrate_add_token_gen.py
"""
import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import text, inspect
from app.core.database import engine, Base


async def migrate():
    print(f"[migrate] 连接数据库: {engine.url}")

    async with engine.begin() as conn:
        # 先检查表是否存在
        table_exists = await conn.scalar(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = 'users'"
            )
        )
        if not table_exists:
            print("[migrate] users 表不存在，先调用 create_all() 创建")
            await conn.run_sync(Base.metadata.create_all)
            print("[migrate] create_all() 完成")
            return

        # 检查 token_gen 列是否存在
        col_exists = await conn.scalar(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = 'users' "
                "AND column_name = 'token_gen'"
            )
        )
        if col_exists:
            print("[migrate] token_gen 列已存在，无需操作")
            return

        print("[migrate] 添加 token_gen 列 (INT, NOT NULL, DEFAULT 0)")
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN token_gen INT NOT NULL DEFAULT 0")
        )
        print("[migrate] 完成！已给 users 表补齐 token_gen 列，默认值 0")


if __name__ == "__main__":
    asyncio.run(migrate())
