from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.models.user import UserCreate, UserLogin, Token, TokenWithUser, UserResponse
from app.crud import user as crud_user
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user
from datetime import timedelta
from app.core.config import settings
from pydantic import BaseModel
import os
import uuid
from pathlib import Path

router = APIRouter()


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str
    confirmPassword: str


@router.post("/register", summary="用户注册", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """用户注册接口"""
    db_user = await crud_user.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    return await crud_user.create_user(db=db, username=user.username, email=user.email, password=user.password)


@router.post("/login", summary="用户登录", response_model=TokenWithUser)
async def login(user: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """用户登录接口"""
    db_user = await crud_user.authenticate_user(db, username=user.username, password=user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "avatar_url": db_user.avatar_url,
            "created_at": db_user.created_at
        }
    }


@router.get("/me", summary="获取当前用户信息", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """获取当前用户信息（需要JWT认证）"""
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "avatar_url": db_user.avatar_url,
        "created_at": db_user.created_at
    }


@router.put("/password", summary="修改密码")
async def change_password(req: ChangePasswordRequest, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """修改密码接口"""
    if req.newPassword != req.confirmPassword:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    
    # 从 JWT token 中获取用户信息
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not verify_password(req.currentPassword, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    
    db_user.hashed_password = get_password_hash(req.newPassword)
    await db.commit()
    await db.refresh(db_user)
    
    return {"message": "密码修改成功"}


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """上传用户头像"""
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持图片格式（JPG、PNG、GIF、WebP）")
    
    # 验证文件大小（限制5MB）
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    # 获取当前用户信息
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 如果用户已有头像，先删除旧文件
    if db_user.avatar_url:
        try:
            # 从URL中提取文件路径
            old_avatar_path = db_user.avatar_url.lstrip('/')
            old_file = Path(old_avatar_path)
            if old_file.exists():
                old_file.unlink()
                print(f"已删除旧头像: {old_avatar_path}")
        except Exception as e:
            print(f"删除旧头像失败: {e}")
            # 不阻断上传流程，继续执行
    
    # 生成唯一文件名
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    
    # 确保上传目录存在
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 生成访问URL
    avatar_url = f"/uploads/avatars/{unique_filename}"
    
    # 更新数据库
    db_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(db_user)
    
    return {"message": "头像上传成功", "avatar_url": avatar_url}


@router.get("/stats", summary="获取用户统计信息")
async def get_user_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户统计信息：笔记数量、AI使用次数、活跃天数"""
    from sqlalchemy import select, func, distinct
    from app.models.note import NoteDB
    from app.crud import ai_usage as crud_ai_usage
    from datetime import datetime, timedelta
    
    # 获取用户
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user_id = db_user.id
    
    # 统计笔记数量
    note_count_result = await db.execute(
        select(func.count(NoteDB.id)).where(NoteDB.user_id == user_id)
    )
    note_count = note_count_result.scalar() or 0
    
    # 统计AI使用次数
    ai_usage = await crud_ai_usage.get_user_ai_usage_count(db, user_id)
    
    # 计算活跃天数（有笔记创建的日期）
    active_dates_result = await db.execute(
        select(distinct(func.date(NoteDB.created_at))).where(NoteDB.user_id == user_id)
    )
    active_dates = active_dates_result.scalars().all()
    days_active = len(active_dates)
    
    return {
        "note_count": note_count,
        "ai_usage": ai_usage,
        "days_active": days_active
    }