"""
测试异步数据库配置
"""

import asyncio

from app.core.config import settings
from app.core.database import engine, get_async_db


async def verify_async_database():
    """异步数据库连通性检查（由 `python tests/test_async_db.py` 手动运行，非 pytest 用例）。"""
    print("🔍 测试异步数据库配置...")
    print(f"📌 数据库 URL: {settings.DATABASE_URL}")

    # 检查是否使用 aiomysql
    if "aiomysql" in settings.DATABASE_URL:
        print("✅ 数据库 URL 使用 aiomysql 驱动")
    else:
        print("❌ 数据库 URL 未使用 aiomysql 驱动")
        return False

    # 测试引擎类型
    print(f"📌 引擎类型: {type(engine).__name__}")

    if "AsyncEngine" in type(engine).__name__:
        print("✅ 使用异步引擎")
    else:
        print("⚠️  使用的是同步引擎（可能是 SQLite）")

    # 测试获取会话
    try:
        async for db in get_async_db():
            print("✅ 成功获取异步数据库会话")
            # 测试简单查询
            from sqlalchemy import text

            result = await db.execute(text("SELECT 1"))
            print(f"✅ 数据库查询成功: {result.scalar()}")
            break
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n🎉 所有测试通过！异步数据库配置正确。")
    return True


if __name__ == "__main__":
    result = asyncio.run(verify_async_database())
    exit(0 if result else 1)
