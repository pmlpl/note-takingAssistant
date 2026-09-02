"""
数据库迁移脚本：创建AI使用记录表
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio

from sqlalchemy import text

from app.core.database import AsyncSessionLocal


async def migrate():
    """执行数据库迁移"""
    db = None
    try:
        db = AsyncSessionLocal()

        # 检查表是否已存在
        result = await db.execute(
            text("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ai_usage_logs'
        """)
        )

        if result.scalar():
            print("✓ ai_usage_logs 表已存在，跳过迁移")
            return

        # 创建 ai_usage_logs 表
        await db.execute(
            text("""
            CREATE TABLE ai_usage_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                usage_type VARCHAR(50) NOT NULL COMMENT '使用类型: generate, summarize, chat',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI使用记录表'
        """)
        )

        await db.commit()
        print("✓ 成功创建 ai_usage_logs 表")

    except Exception as e:
        if db:
            await db.rollback()
        print(f"✗ 迁移失败: {e}")
        raise
    finally:
        if db:
            await db.close()


if __name__ == "__main__":
    import warnings

    # 忽略 aiomysql 连接清理警告
    warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

    print("开始执行数据库迁移...")
    try:
        asyncio.run(migrate())
        print("迁移完成！")
    except Exception as e:
        print(f"程序执行失败: {e}")
        import sys

        sys.exit(1)
