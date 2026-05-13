"""
测试脚本：检查用户头像是否正确保存到数据库
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import UserDB


async def check_avatar():
    """检查用户头像"""
    async with AsyncSessionLocal() as db:
        try:
            # 获取所有用户
            result = await db.execute(select(UserDB))
            users = result.scalars().all()
            
            print("="*60)
            print("用户头像信息检查")
            print("="*60)
            
            if not users:
                print("数据库中没有用户")
                return
            
            for user in users:
                print(f"\n用户ID: {user.id}")
                print(f"用户名: {user.username}")
                print(f"邮箱: {user.email}")
                print(f"头像URL: {user.avatar_url or '无'}")
                print("-"*60)
            
        except Exception as e:
            print(f"检查失败: {e}")
            raise


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
    
    print("开始检查用户头像...\n")
    asyncio.run(check_avatar())
    print("\n检查完成！")
