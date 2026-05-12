from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import tempfile
import uuid
from datetime import datetime
from app.core.database import get_async_db
from app.models.note import NoteCreate, NoteUpdate, NoteResponse
from app.crud import note as crud_note
from app.utils.file_parser import parse_file, extract_title_from_filename
from app.core.redis_client import cache_recent_note, batch_cache_recent_notes, clear_recent_notes
from app.core.security import get_current_user

router = APIRouter()

# 图片存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-image", summary="上传图片")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片文件，返回图片URL
    """
    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、GIF、WEBP 格式的图片")
    
    # 验证文件大小（限制为5MB）
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # 返回图片URL
    image_url = f"/uploads/images/{unique_filename}"
    return {"url": image_url}


@router.post("/", summary="创建笔记", response_model=NoteResponse)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """创建新笔记，自动检测标题重复"""
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    
    # 检测是否已存在相同标题的笔记
    existing_notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=1000)
    existing_note = next((n for n in existing_notes if n.title == note.title), None)
    
    if existing_note:
        raise HTTPException(
            status_code=409,
            detail=f"笔记 '{note.title}' 已存在"
        )
    
    # 将布尔值转换为整数（数据库使用 Integer 类型）
    is_favorite_int = 1 if note.is_favorite else 0
    
    return await crud_note.create_note(
        db=db, 
        user_id=user_id, 
        title=note.title, 
        content=note.content, 
        tags=note.tags,
        is_favorite=is_favorite_int
    )


@router.get("/", summary="获取笔记列表", response_model=List[NoteResponse])
async def get_notes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """获取笔记列表"""
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    return await crud_note.get_notes(db=db, user_id=user_id, skip=skip, limit=limit)


@router.get("/recent", summary="获取最近笔记")
async def list_recent_notes(db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """
    获取用户的最近笔记（从 Redis 缓存）
    最多返回20个最近打开/创建的笔记
    """
    
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    
    try:
        # 从 Redis 获取最近笔记（最备20个）
        from app.core.redis_client import get_recent_notes as redis_get_recent_notes
        recent_notes = redis_get_recent_notes(user_id, limit=20)

        if recent_notes:
            # 如果 Redis 中有数据，打印调试信息
            # 直接返回字典列表
            return recent_notes
        
        # 如果 Redis 中没有，从数据库获取（最备20个）
        notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=20)
        # 按创建时间倒序排列
        notes.sort(key=lambda x: x.created_at, reverse=True)
        
        # 转换为字典格式
        result = []
        for note in notes[:20]:
            # 提取纯文本预览（去掉HTML标签）
            import re
            text_preview = re.sub(r'<[^>]+>', '', note.content)[:200] if note.content else ""
            
            result.append({
                "id": note.id,
                "user_id": note.user_id,
                "title": note.title,
                "content": text_preview,  # 只返回文本预览
                "tags": note.tags,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None
            })
        
        return result
    except Exception as e:
        print(f"❌ 获取最近笔记失败: {e}")
        import traceback
        traceback.print_exc()
        # 出错时从数据库获取（最备20个）
        notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=20)
        notes.sort(key=lambda x: x.created_at, reverse=True)
        
        result = []
        for note in notes[:20]:
            # 提取纯文本预览（去掉HTML标签）
            import re
            text_preview = re.sub(r'<[^>]+>', '', note.content)[:200] if note.content else ""
            
            result.append({
                "id": note.id,
                "user_id": note.user_id,
                "title": note.title,
                "content": text_preview,  # 只返回文本预览
                "tags": note.tags,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None
            })
        
        return result


@router.post("/recent/update", summary="更新最近笔记顺序")
async def update_recent_notes_order(
    note_ids: List[int],
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新用户的最近笔记顺序
    前端传入笔记ID列表（按最新到最旧的顺序）
    """
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    
    try:
        # 根据note_ids获取完整的笔记信息（最备20个）
        notes_data = []
        for note_id in note_ids[:20]:  # 最多20个
            note = await crud_note.get_note(db=db, note_id=note_id, user_id=user_id)
            if note:
                # 提取纯文本预览
                import re
                text_preview = re.sub(r'<[^>]+>', '', note.content)[:200] if note.content else ""
                
                notes_data.append({
                    "id": note.id,
                    "user_id": note.user_id,
                    "title": note.title,
                    "content": text_preview,
                    "tags": note.tags,
                    "created_at": note.created_at.isoformat() if note.created_at else None,
                    "updated_at": note.updated_at.isoformat() if note.updated_at else None
                })
        # 使用批量缓存，按指定顺序保存
        batch_cache_recent_notes(user_id, notes_data)
        
        return {"message": "更新成功", "count": len(notes_data)}
    except Exception as e:
        print(f"❌ 更新最近笔记顺序失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/{note_id}", summary="获取笔记详情", response_model=NoteResponse)
async def get_note(note_id: int, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """获取笔记详情"""
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    db_note = await crud_note.get_note(db=db, note_id=note_id, user_id=user_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return db_note


@router.put("/{note_id}", summary="更新笔记", response_model=NoteResponse)
async def update_note(note_id: int, note: NoteUpdate, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """更新笔记"""
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    
    # 将布尔值转换为整数（数据库使用 Integer 类型）
    is_favorite_int = None
    if note.is_favorite is not None:
        is_favorite_int = 1 if note.is_favorite else 0
    
    db_note = await crud_note.update_note(
        db=db, note_id=note_id, user_id=user_id,
        title=note.title, content=note.content, tags=note.tags,
        is_favorite=is_favorite_int
    )
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return db_note


@router.delete("/{note_id}", summary="删除笔记")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """删除笔记，同时清除Redis缓存和关联的图片"""
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    
    # 先获取笔记内容，提取图片URL
    db_note = await crud_note.get_note(db=db, note_id=note_id, user_id=user_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    # 提取笔记中的图片URL并删除文件
    import re
    from app.core.config import settings
    if db_note.content:
        # 匹配图片URL: {settings.API_BASE_URL}/uploads/images/xxx.png
        image_urls = re.findall(rf'{re.escape(settings.API_BASE_URL)}/uploads/images/([\w]+\.[\w]+)', db_note.content)
        
        for image_filename in image_urls:
            image_path = os.path.join(UPLOAD_DIR, image_filename)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"✅ 已删除图片: {image_filename}")
                except Exception as e:
                    print(f"⚠️ 删除图片失败 {image_filename}: {e}")
    
    # 删除笔记
    await crud_note.delete_note(db=db, note_id=note_id, user_id=user_id)
    
    # 清除该用户的Redis缓存
    from app.core.redis_client import clear_recent_notes
    clear_recent_notes(user_id)
    
    return {"message": "删除成功"}


@router.post("/import", summary="导入笔记", response_model=NoteResponse)
async def import_note(
    file: UploadFile = File(...),
        overwrite: Optional[bool] = Form(False),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    导入笔记文件（支持 .txt, .md, .docx）
    - 解析文件内容
    - 创建新笔记到数据库
    - 缓存到Redis最近笔记
    - 检测重复文件
    """
    # 从 JWT token 中获取用户信息
    from app.crud import user as crud_user
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_id = db_user.id
    
    # 验证文件扩展名
    allowed_extensions = ['.txt', '.md', '.docx']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，仅支持 {', '.join(allowed_extensions)}"
        )
    
    try:
        # 创建临时文件保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            # 读取上传的文件内容并写入临时文件
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 解析文件内容
            parsed_content = parse_file(tmp_file_path, file.filename)
            
            if not parsed_content:
                raise HTTPException(
                    status_code=400,
                    detail="文件解析失败，请检查文件格式是否正确"
                )
            
            # 从文件名提取标题
            title = extract_title_from_filename(file.filename)
            
            # 检测是否已存在相同标题的笔记（去重）
            existing_notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=1000)
            existing_note = next((note for note in existing_notes if note.title == title), None)
            
            if existing_note:
                if not overwrite:
                    # 如果用户没有选择覆盖，返回冲突信息
                    raise HTTPException(
                        status_code=409,
                        detail=f"笔记 '{title}' 已存在，请选择是否覆盖"
                    )
                else:
                    # 用户选择覆盖，先删除旧笔记
                    await crud_note.delete_note(db=db, note_id=existing_note.id, user_id=user_id)

            # 创建笔记到数据库
            db_note = await crud_note.create_note(
                db=db,
                user_id=user_id,
                title=title,
                content=parsed_content,
                tags=f"导入,{file_ext}"
            )
            
            # 缓存到Redis（最近笔记）- 只缓存摘要信息，不包含完整内容
            # 提取纯文本预览（去掉HTML标签）
            import re
            text_preview = re.sub(r'<[^>]+>', '', parsed_content)[:200]  # 前200字符
            
            note_data = {
                "id": db_note.id,
                "user_id": user_id,
                "title": db_note.title,
                "content": text_preview,  # 只缓存文本预览
                "tags": db_note.tags,
                "created_at": db_note.created_at.isoformat() if db_note.created_at else None,
                "updated_at": db_note.updated_at.isoformat() if db_note.updated_at else None
            }
            cache_recent_note(user_id, note_data)
            
            return db_note
        
        finally:
            # 删除临时文件
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"导入笔记失败: {str(e)}"
        )
