"""本地测试用户生成脚本

使用方法：
    cd backend
    python create_test_user.py --email test@example.com --password test1234 --nickname 测试用户

该脚本会直接在数据库中创建一个测试用户，无需邮件验证即可登录。
仅用于本地开发测试，请勿在生产环境使用！
"""
import argparse
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.crud.user import get_user_by_email, create_user


async def main():
    parser = argparse.ArgumentParser(description="创建本地测试用户")
    parser.add_argument("--email", default="test@example.com", help="测试用户邮箱")
    parser.add_argument("--password", default="test1234", help="测试用户密码")
    parser.add_argument("--nickname", default="测试用户", help="测试用户昵称")
    args = parser.parse_args()

    print(f"准备创建测试用户: {args.email}")
    print("=" * 40)

    # 初始化数据库（确保表存在）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 检查用户是否已存在
        existing = await get_user_by_email(session, args.email)
        if existing:
            print(f"⚠️ 用户 {args.email} 已存在！")
            print(f"  ID: {existing.id}")
            print(f"  昵称: {existing.nickname}")
            print("如需重新创建，请先删除数据库中的记录。")
            return

        # 创建用户
        print(f"创建用户: {args.email}")
        hashed_password = get_password_hash(args.password)

        from app.models.user import UserDB

        user = UserDB(
            email=args.email,
            hashed_password=hashed_password,
            nickname=args.nickname,
            email_verified=True,  # 直接标记已验证，跳过邮件验证
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        print(f"✅ 测试用户创建成功！")
        print(f"  ID: {user.id}")
        print(f"  邮箱: {user.email}")
        print(f"  昵称: {user.nickname}")
        print(f"  密码: {args.password}")
        print(f"  邮箱已验证: {user.email_verified}")
        print()
        print("现在可以用以下账号登录：")
        print(f"  邮箱: {args.email}")
        print(f"  密码: {args.password}")


if __name__ == "__main__":
    asyncio.run(main())
