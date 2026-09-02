import hashlib
import os
import re
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.logger import app_logger as logger
from app.core.rate_limit import rate_limit_user
from app.core.redis_client import (
    batch_cache_recent_notes_async,
    cache_recent_note_async,
    clear_recent_notes_async,
    get_recent_notes_async,
    remove_recent_note_by_id_async,
)
from app.core.security import get_current_user
from app.crud import note as crud_note
from app.crud import user as crud_user
from app.models.note import NoteCreate, NoteDB, NoteResponse, NoteUpdate
from app.services import note_rag
from app.utils.file_parser import extract_title_from_filename, parse_file

router = APIRouter()

# 所有笔记操作共享同一限流策略
_notes_rate_limit = Depends(rate_limit_user("notes"))

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "uploads",
    "images",
)
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-image", summary="上传图片")
async def upload_image(
    file: UploadFile = File(...),
    x_content_md5: Optional[str] = Header(None, alias="X-Content-MD5"),
    _: None = _notes_rate_limit,
):
    """上传笔记正文配图（做魔数 + 扩展名双重校验）。"""
    from app.utils.file_upload import safe_image_filename, validate_image_bytes

    if file.size is not None and file.size > settings.IMAGE_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"图片超过上限 {settings.IMAGE_MAX_BYTES // 1024 // 1024}MB",
        )

    chunk_size = 1024 * 1024
    file_bytes = bytearray()
    md5 = hashlib.md5()
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_bytes.extend(chunk)
        md5.update(chunk)
        if len(file_bytes) > settings.IMAGE_MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"图片超过上限 {settings.IMAGE_MAX_BYTES // 1024 // 1024}MB",
            )

    if x_content_md5:
        computed_md5 = md5.hexdigest()
        if computed_md5.lower() != x_content_md5.lower():
            raise HTTPException(
                status_code=400,
                detail=f"文件MD5校验失败，期望 {x_content_md5}，实际 {computed_md5}",
            )

    ok, ext, err = validate_image_bytes(bytes(file_bytes), file.filename or "", max_bytes=settings.IMAGE_MAX_BYTES)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    safe_name = safe_image_filename(file.filename or f"image{ext}", ext)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    try:
        with open(file_path, "wb") as f:
            f.write(bytes(file_bytes))
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"图片保存失败: {e}")

    return {"url": f"/uploads/images/{safe_name}"}


async def _get_db_user(db: AsyncSession, current_user: dict):
    """获取当前登录的数据库用户（复用代码）"""
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user


def _text_preview(content: str, max_len: int = 200) -> str:
    """提取纯文本预览（去掉HTML标签）"""
    return re.sub(r"<[^>]+>", "", content)[:max_len] if content else ""


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


async def _sync_note_index(db: AsyncSession, db_user, note) -> None:
    """同步单篇笔记的 RAG 分块索引；索引失败只记日志，不影响笔记 CRUD"""
    try:
        await note_rag.index_note_chunks(db, db_user, note)
    except Exception as e:
        logger.info(f"⚠️ 笔记索引同步失败 note_id={note.id}: {e}")


async def _delete_note_index(db: AsyncSession, user_id: int, note_id: int) -> None:
    """删除笔记的 RAG 分块索引；失败只记日志，不影响笔记删除"""
    try:
        await note_rag.delete_note_chunks(db, user_id=user_id, note_id=note_id)
    except Exception as e:
        logger.info(f"⚠️ 笔记索引删除失败 note_id={note_id}: {e}")


@router.get("/search", summary="搜索笔记")
async def search_notes(
    keyword: str = Query("", description="搜索关键词（标题/正文模糊匹配 + 向量语义检索）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    is_favorite: Optional[bool] = Query(None, description="筛选收藏笔记"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """混合检索笔记：标题/正文关键词 + 向量语义（RAG），支持分页"""
    db_user = await _get_db_user(db, current_user)
    skip = (page - 1) * page_size
    notes, total = await note_rag.hybrid_search_notes(
        db,
        db_user=db_user,
        keyword=keyword,
        skip=skip,
        limit=page_size,
        is_favorite=is_favorite,
    )
    return {
        "items": notes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/rag/context", summary="检索笔记相关片段（RAG 上下文）")
async def rag_context(
    query: str = Query("", min_length=1, description="查询文本"),
    limit: int = Query(5, ge=1, le=10, description="返回片段数量上限"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """检索与 query 相关的笔记片段，供 AI 对话上下文注入使用。

    返回按相关度排序的片段列表：note_id / note_title / chunk_index / content / score / source。
    """
    db_user = await _get_db_user(db, current_user)
    items = await note_rag.retrieve_context(db, db_user=db_user, query=query, limit=limit)
    return {"query": query, "count": len(items), "items": items}


@router.post("/rag/rebuild", summary="重建笔记分块索引（RAG）")
async def rag_rebuild(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """重建当前用户全部笔记的分块索引（创建/更新/删除时已自动同步，此接口用于存量数据或 embedding 模型变更后重建）。"""
    db_user = await _get_db_user(db, current_user)
    stats = await note_rag.rebuild_all_note_chunks(db, db_user=db_user)
    return {"message": "重建完成", **stats}


@router.post("/", summary="创建笔记", response_model=NoteResponse)
async def create_note(
    note: NoteCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """创建新笔记，自动检测标题重复"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id

    # 检测是否已存在相同标题的笔记（走 SQL 索引，不再拉取 1000 条）
    existing_note = await crud_note.get_note_by_title(db=db, user_id=user_id, title=note.title)

    if existing_note:
        raise HTTPException(status_code=409, detail=f"笔记 '{note.title}' 已存在")

    # crud 层会自动将 bool 转换为数据库的 Integer
    db_note = await crud_note.create_note(
        db=db,
        user_id=user_id,
        title=note.title,
        content=note.content,
        tags=note.tags,
        is_favorite=note.is_favorite,
    )
    await _sync_note_index(db, db_user, db_note)
    return db_note


@router.get("/", summary="获取笔记列表", response_model=list[NoteResponse])
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """获取笔记列表（支持分页）"""
    db_user = await _get_db_user(db, current_user)
    return await crud_note.get_notes(db=db, user_id=db_user.id, skip=skip, limit=limit)


@router.get("/recent", summary="获取最近笔记")
async def list_recent_notes(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """获取用户的最近笔记（最多20个），优先从 Redis 缓存读取"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id

    try:
        cached = await get_recent_notes_async(user_id, limit=20)
        if cached:
            recent_ids = [n["id"] for n in cached if n.get("id") is not None]
            if recent_ids:
                result_ids = await db.execute(
                    select(NoteDB.id).where(NoteDB.user_id == user_id, NoteDB.id.in_(recent_ids))
                )
                valid_ids = set(result_ids.scalars().all())
            else:
                valid_ids = set()
            pruned = [n for n in cached if n["id"] in valid_ids]
            if len(pruned) != len(cached):
                (
                    await batch_cache_recent_notes_async(user_id, pruned)
                    if pruned
                    else await clear_recent_notes_async(user_id)
                )
            return pruned

        notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=20)
        notes.sort(key=lambda x: x.created_at, reverse=True)
        return [_note_to_recent_dict(n) for n in notes[:20]]
    except Exception as e:
        logger.info(f"❌ 获取最近笔记失败: {e}")
        import traceback as tb

        tb.print_exc()
        notes = await crud_note.get_notes(db=db, user_id=user_id, skip=0, limit=20)
        notes.sort(key=lambda x: x.created_at, reverse=True)
        return [_note_to_recent_dict(n) for n in notes[:20]]


@router.post("/recent/update", summary="更新最近笔记顺序")
async def update_recent_notes_order(
    note_ids: list[int],
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
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
        await batch_cache_recent_notes_async(user_id, notes_data)
        return {"message": "更新成功", "count": len(notes_data)}
    except Exception as e:
        logger.info(f"❌ 更新最近笔记顺序失败: {e}")
        import traceback as tb

        tb.print_exc()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/{note_id}", summary="获取笔记详情", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """获取笔记详情"""
    db_user = await _get_db_user(db, current_user)
    db_note = await crud_note.get_note(db=db, note_id=note_id, user_id=db_user.id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return db_note


@router.put("/{note_id}", summary="更新笔记", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note: NoteUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """更新笔记，并同步 RAG 分块索引"""
    db_user = await _get_db_user(db, current_user)
    db_note = await crud_note.update_note(
        db=db,
        note_id=note_id,
        user_id=db_user.id,
        title=note.title,
        content=note.content,
        tags=note.tags,
        is_favorite=note.is_favorite,
    )
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    await _sync_note_index(db, db_user, db_note)
    return db_note


@router.delete("/{note_id}", summary="删除笔记")
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """删除笔记，同时清除Redis缓存和关联的图片"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id
    db_note = await crud_note.get_note(db=db, note_id=note_id, user_id=user_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if db_note.content:
        image_urls = re.findall(
            rf"{re.escape(settings.API_BASE_URL)}/uploads/images/([\w]+\.[\w]+)",
            db_note.content,
        )
        for fn in image_urls:
            fp = os.path.join(UPLOAD_DIR, fn)
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception as e:
                    logger.info(f"⚠️ 删除图片失败 {fn}: {e}")

    await crud_note.delete_note(db=db, note_id=note_id, user_id=user_id)
    await _delete_note_index(db, user_id=user_id, note_id=note_id)
    await clear_recent_notes_async(user_id)
    return {"message": "删除成功"}


@router.post("/import", summary="导入笔记", response_model=NoteResponse)
async def import_note(
    file: UploadFile = File(...),
    overwrite: Optional[bool] = Form(False),
    x_content_md5: Optional[str] = Header(None, alias="X-Content-MD5"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _notes_rate_limit,
):
    """导入笔记文件（支持 .txt, .md, .docx）"""
    db_user = await _get_db_user(db, current_user)
    user_id = db_user.id

    allowed_extensions = [".txt", ".md", ".docx"]
    file_ext = os.path.splitext(os.path.basename(file.filename or ""))[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，仅支持 {', '.join(allowed_extensions)}",
        )

    if file.size is not None and file.size > settings.MAX_IMPORT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"文件超过上限 {settings.MAX_IMPORT_BYTES // 1024 // 1024}MB",
        )

    tmp_path = None
    try:
        md5 = hashlib.md5()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_path = tmp_file.name
            total = 0
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.MAX_IMPORT_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件超过上限 {settings.MAX_IMPORT_BYTES // 1024 // 1024}MB",
                    )
                md5.update(chunk)
                tmp_file.write(chunk)

        if x_content_md5:
            computed_md5 = md5.hexdigest()
            if computed_md5.lower() != x_content_md5.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"文件MD5校验失败，期望 {x_content_md5}，实际 {computed_md5}",
                )

        parsed = parse_file(tmp_path, file.filename)
        if not parsed:
            raise HTTPException(status_code=400, detail="文件解析失败，请检查文件格式是否正确")

        title = extract_title_from_filename(file.filename)
        dup = await crud_note.get_note_by_title(db=db, user_id=user_id, title=title)
        if dup:
            if not overwrite:
                raise HTTPException(status_code=409, detail=f"笔记 '{title}' 已存在，请选择是否覆盖")
            await crud_note.delete_note(db=db, note_id=dup.id, user_id=user_id)
            await _delete_note_index(db, user_id=user_id, note_id=dup.id)
            await remove_recent_note_by_id_async(user_id, dup.id)

        db_note = await crud_note.create_note(
            db=db, user_id=user_id, title=title, content=parsed, tags=f"导入,{file_ext}"
        )
        await _sync_note_index(db, db_user, db_note)
        note_data = _note_to_recent_dict(db_note)
        note_data["content"] = _text_preview(parsed)
        await cache_recent_note_async(user_id, note_data)
        return db_note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入笔记失败: {str(e)}")
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
