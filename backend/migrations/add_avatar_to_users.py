"""
数据库迁移脚本：添加用户头像字段
运行此脚本将 avatar_url 字段添加到 users 表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def migrate():
    """执行数据库迁移"""
    db = None
    try:
        db = AsyncSessionLocal()
        
        # 检查字段是否已存在
        result = await db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'avatar_url'
        """))
        
        if result.scalar():
            print("✓ avatar_url 字段已存在，跳过迁移")
            return
        
        # 添加 avatar_url 字段
        await db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN avatar_url TEXT NULL COMMENT '用户头像URL'
        """))
        
        await db.commit()
        print("✓ 成功添加 avatar_url 字段到 users 表")
        
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
