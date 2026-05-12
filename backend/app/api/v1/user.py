from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.models.user import UserCreate, UserLogin, Token, TokenWithUser, UserResponse
from app.crud import user as crud_user
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user
from datetime import timedelta
from app.core.config import settings
from pydantic import BaseModel

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