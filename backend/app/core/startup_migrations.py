"""Lightweight DDL for deployments without Alembic (idempotent)."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_user_llm_columns(db: AsyncSession) -> None:
    """Add BYOK / LLM override columns to users if missing."""
    pairs = [
        ("llm_base_url", "ALTER TABLE users ADD COLUMN llm_base_url TEXT NULL"),
        ("llm_model", "ALTER TABLE users ADD COLUMN llm_model VARCHAR(512) NULL"),
        ("llm_api_key_encrypted", "ALTER TABLE users ADD COLUMN llm_api_key_encrypted TEXT NULL"),
    ]
    for column_name, ddl in pairs:
        r = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = :col
                """
            ),
            {"col": column_name},
        )
        if (r.scalar() or 0) == 0:
            await db.execute(text(ddl))
