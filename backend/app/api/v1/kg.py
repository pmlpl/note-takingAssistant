from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.core.rate_limit import rate_limit_user
from app.crud import user as crud_user
from app.models.kg import KGGraphResponse, KGStatusResponse
from app.services.knowledge_graph_service import (
    build_knowledge_graph,
    save_kg_to_db,
    update_kg_status,
    get_kg_status,
    get_kg_from_db,
)
from app.core.logger import app_logger as logger

router = APIRouter()
_kg_rate_limit = Depends(rate_limit_user("notes"))


async def _get_db_user(db: AsyncSession, current_user: dict):
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user


@router.get("/graph", summary="获取知识图谱数据")
async def get_kg_graph(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _kg_rate_limit,
):
    db_user = await _get_db_user(db, current_user)
    try:
        cached = await get_kg_from_db(db, db_user.id)
        if cached is not None:
            nodes, edges, stats = cached
            return KGGraphResponse(nodes=nodes, edges=edges, stats=stats)
        nodes, edges, stats = await build_knowledge_graph(db, db_user.id, db_user)
        await save_kg_to_db(db, db_user.id, nodes, edges)
        await update_kg_status(db, db_user.id, "ready", progress=100)
        return KGGraphResponse(nodes=nodes, edges=edges, stats=stats)
    except Exception as e:
        logger.error(f"获取知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图谱失败: {str(e)}")


@router.post("/refresh", summary="刷新知识图谱")
async def refresh_kg(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _kg_rate_limit,
):
    db_user = await _get_db_user(db, current_user)

    status = await get_kg_status(db, db_user.id)
    if status and status.status == "generating":
        raise HTTPException(status_code=409, detail="图谱正在生成中，请稍候")

    await update_kg_status(
        db,
        db_user.id,
        "generating",
        progress=0,
        total_notes=0,
        processed_notes=0,
        error_msg=None,
        started_at=datetime.utcnow(),
        finished_at=None,
    )

    import asyncio
    from app.core.database import AsyncSessionLocal

    async def _background_generate():
        async with AsyncSessionLocal() as bg_db:
            try:
                nodes, edges, stats = await build_knowledge_graph(bg_db, db_user.id, db_user)
                await save_kg_to_db(bg_db, db_user.id, nodes, edges)
                await update_kg_status(
                    bg_db,
                    db_user.id,
                    "ready",
                    progress=100,
                    total_notes=stats.get("note_count", 0),
                    processed_notes=stats.get("note_count", 0),
                    finished_at=datetime.utcnow(),
                )
            except Exception as e:
                logger.error(f"图谱生成失败: {e}")
                await update_kg_status(
                    bg_db,
                    db_user.id,
                    "failed",
                    error_msg=str(e),
                    finished_at=datetime.utcnow(),
                )

    asyncio.create_task(_background_generate())

    return {"message": "图谱生成已开始", "status": "generating"}


@router.get("/status", summary="获取图谱生成状态", response_model=KGStatusResponse)
async def get_kg_graph_status(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = _kg_rate_limit,
):
    db_user = await _get_db_user(db, current_user)
    status = await get_kg_status(db, db_user.id)
    if not status:
        return KGStatusResponse(
            status="idle",
            progress=0,
            total_notes=0,
            processed_notes=0,
        )
    return KGStatusResponse(
        status=status.status,
        progress=status.progress,
        total_notes=status.total_notes,
        processed_notes=status.processed_notes,
        error_msg=status.error_msg,
        started_at=status.started_at,
        finished_at=status.finished_at,
    )
