from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import re
import tempfile
import uuid
from datetime import datetime
from app.core.database import get_async_db
from app.models.note import NoteCreate, NoteUpdate, NoteResponse, NoteDB
from app.crud import note as crud_note
from app.crud import user as crud_user
from app.utils.file_parser import parse_file, extract_title_from_filename
from app.core.redis_client import (
    cache_recent_note,
    batch_cache_recent_notes,
    clear_recent_notes,
    remove_recent_note_by_id,
    get_recent_notes as redis_get_recent_notes,
)
from app.core.security import get_current_user
from app.core.config import settings

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


async def _get_db_user(db: AsyncSession, current_user: dict):
    """获取当前登录的数据库用户（复用代码）"""
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user


def _text_preview(content: str, max_len: int = 200) -> str:
    """提取纯文本预览（去掉HTML标签）"""
    return re.sub(r'<[^>]+>', '', content)[:max_len] if content else ""


def _note_to_recent_dict(note) -> dict:
    """将 NoteDB 对象转换为最近笔记所需的字典格式"""
    return {
        "id": note.id,
        "user_id": note.user_id,
        "title": note.title,
        "content": _text_preview(note.content),
        "tags": note.tags,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


@router.get("/search", summary="搜索笔记")
async def search_notes(
    keyword: str = Query("", description="搜索关键词（仅匹配笔记标题）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    is_favorite: Optional[bool] = Query(None, description="筛选收藏笔记"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """搜索笔记（仅按标题模糊匹配），支持分页"""
    db_user = await _get_db_user(db, current_user)
    skip = (page - 1) * page_size
    notes = await crud_note.search_notes(
        db, user_id=db_user.id, keyword=keyword,
        skip=skip, limit=page_size, is_favorite=is_favorite,
    )
    total = await crud_note.count_notes(
        db, user_id=db_user.id, keyword=keyword, is_favorite=is_favorite,
    )
    return {
        "items": notes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/", summary="创建笔记", response_model=NoteResponse)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """创建新笔记，自动检测标题重复"""
    db_user = await _get_db_user(db, current_user)
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
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """获取笔记列表（支持分页）"""
    db_user = await _get_db_user(db, current_user)
    return await crud_note.get_notes(db=db, user_id=db_user.id, skip=skip, limit=limit)


@router.get("/recent", summary="获取最近笔记")
async def list_recent_notes(db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """获取用户的最近笔记（最多20个），优先从 Redis 缓存读取"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id

    try:
        cached = redis_get_recent_notes(user_id, limit=20)
        if cached:
            recent_ids = [n["id"] for n in cached if n.get("id") is not None]
            if recent_ids:
                result_ids = await db.execute(
                    select(NoteDB.id).where(
                        NoteDB.user_id == user_id, NoteDB.id.in_(recent_ids)
                    )
                )
                valid_ids = set(result_ids.scalars().all())
            else:
                valid_ids = set()
            pruned = [n for n in cached if n["id"] in valid_ids]
            if len(pruned) != len(cached):
                (batch_cache_recent_notes(user_id, pruned) if pruned else clear_recent_notes(user_id))
            return pruned

        notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=20)
        notes.sort(key=lambda x: x.created_at, reverse=True)
        return [_note_to_recent_dict(n) for n in notes[:20]]
    except Exception as e:
        print(f"❌ 获取最近笔记失败: {e}")
        import traceback as tb
        tb.print_exc()
        notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=20)
        notes.sort(key=lambda x: x.created_at, reverse=True)
        return [_note_to_recent_dict(n) for n in notes[:20]]


@router.post("/recent/update", summary="更新最近笔记顺序")
async def update_recent_notes_order(
    note_ids: List[int],
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """更新用户的最近笔记顺序（前端传入ID列表，按最新到最旧）"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id

    try:
        notes_data = []
        for note_id in note_ids[:20]:
            note = await crud_note.get_note(db=db, note_id=note_id, user_id=user_id)
            if note:
                notes_data.append(_note_to_recent_dict(note))
        batch_cache_recent_notes(user_id, notes_data)
        return {"message": "更新成功", "count": len(notes_data)}
    except Exception as e:
        print(f"❌ 更新最近笔记顺序失败: {e}")
        import traceback as tb
        tb.print_exc()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/{note_id}", summary="获取笔记详情", response_model=NoteResponse)
async def get_note(note_id: int, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """获取笔记详情"""
    db_user = await _get_db_user(db, current_user)
    db_note = await crud_note.get_note(db=db, note_id=note_id, user_id=db_user.id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return db_note


@router.put("/{note_id}", summary="更新笔记", response_model=NoteResponse)
async def update_note(note_id: int, note: NoteUpdate, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """更新笔记"""
    db_user = await _get_db_user(db, current_user)
    is_favorite_int = None
    if note.is_favorite is not None:
        is_favorite_int = 1 if note.is_favorite else 0
    db_note = await crud_note.update_note(
        db=db, note_id=note_id, user_id=db_user.id,
        title=note.title, content=note.content, tags=note.tags,
        is_favorite=is_favorite_int,
    )
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return db_note


@router.delete("/{note_id}", summary="删除笔记")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """删除笔记，同时清除Redis缓存和关联的图片"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id
    db_note = await crud_note.get_note(db=db, note_id=note_id, user_id=user_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if db_note.content:
        image_urls = re.findall(
            rf'{re.escape(settings.API_BASE_URL)}/uploads/images/([\w]+\.[\w]+)',
            db_note.content,
        )
        for fn in image_urls:
            fp = os.path.join(UPLOAD_DIR, fn)
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception as e:
                    print(f"⚠️ 删除图片失败 {fn}: {e}")

    await crud_note.delete_note(db=db, note_id=note_id, user_id=user_id)
    clear_recent_notes(user_id)
    return {"message": "删除成功"}


@router.post("/import", summary="导入笔记", response_model=NoteResponse)
async def import_note(
    file: UploadFile = File(...),
    overwrite: Optional[bool] = Form(False),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """导入笔记文件（支持 .txt, .md, .docx）"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id

    allowed_extensions = ['.txt', '.md', '.docx']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，仅支持 {', '.join(allowed_extensions)}",
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            raw = await file.read()
            tmp_file.write(raw)
            tmp_path = tmp_file.name

        try:
            parsed = parse_file(tmp_path, file.filename)
            if not parsed:
                raise HTTPException(status_code=400, detail="文件解析失败，请检查文件格式是否正确")

            title = extract_title_from_filename(file.filename)
            existing = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=1000)
            dup = next((n for n in existing if n.title == title), None)
            if dup:
                if not overwrite:
                    raise HTTPException(status_code=409, detail=f"笔记 '{title}' 已存在，请选择是否覆盖")
                await crud_note.delete_note(db=db, note_id=dup.id, user_id=user_id)
                remove_recent_note_by_id(user_id, dup.id)

            db_note = await crud_note.create_note(db=db, user_id=user_id, title=title, content=parsed, tags=f"导入,{file_ext}")
            note_data = _note_to_recent_dict(db_note)
            note_data["content"] = _text_preview(parsed)
            cache_recent_note(user_id, note_data)
            return db_note
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入笔记失败: {str(e)}")
