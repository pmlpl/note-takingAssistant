"""
清理孤儿头像文件脚本
删除数据库中未引用的头像文件
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from pathlib import Path
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import UserDB


async def cleanup_orphan_avatars():
    """清理孤儿头像文件"""
    db = None
    try:
        db = AsyncSessionLocal()
        
        # 获取所有用户的头像URL
        result = await db.execute(select(UserDB.avatar_url))
        avatar_urls = result.scalars().all()
        
        # 构建有效头像路径集合
        valid_avatars = set()
        for url in avatar_urls:
            if url:
                # 从 URL 中提取文件路径
                path = url.lstrip('/')
                valid_avatars.add(path)
        
        print(f"数据库中的有效头像数量: {len(valid_avatars)}")
        
        # 获取uploads/avatars目录下的所有文件
        upload_dir = Path("uploads/avatars")
        if not upload_dir.exists():
            print("头像目录不存在，无需清理")
            return
        
        all_files = list(upload_dir.iterdir())
        print(f"uploads/avatars目录中的文件数量: {len(all_files)}")
        
        # 找出孤儿文件
        orphan_files = []
        for file_path in all_files:
            relative_path = str(file_path).replace('\\', '/')
            if relative_path not in valid_avatars:
                orphan_files.append(file_path)
        
        print(f"孤儿文件数量: {len(orphan_files)}")
        
        # 删除孤儿文件
        deleted_count = 0
        total_size = 0
        
        for orphan_file in orphan_files:
            try:
                file_size = orphan_file.stat().st_size
                orphan_file.unlink()
                deleted_count += 1
                total_size += file_size
                print(f"已删除: {orphan_file.name}")
            except Exception as e:
                print(f"删除失败 {orphan_file.name}: {e}")
        
        # 输出统计信息
        print("\n" + "="*50)
        print(f"清理完成！")
        print(f"删除文件数: {deleted_count}")
        print(f"释放空间: {total_size / 1024 / 1024:.2f} MB")
        print("="*50)
        
    except Exception as e:
        print(f"清理失败: {e}")
        raise
    finally:
        if db:
            await db.close()


if __name__ == "__main__":
    import warnings
    # 忽略 aiomysql 连接清理警告
    warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
    
    print("开始清理孤儿头像文件...")
    try:
        asyncio.run(cleanup_orphan_avatars())
        print("清理完成！")
    except Exception as e:
        print(f"程序执行失败: {e}")
        import sys
        sys.exit(1)

