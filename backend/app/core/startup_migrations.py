"""Lightweight DDL for deployments without Alembic (idempotent).

If Alembic has been applied (alembic_version table exists), all DDL is skipped
since Alembic is the source of truth for schema management.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, Base
from app.core.logger import app_logger as logger
from app.models.kg import KGConceptDB, KGRelationDB, KGStatusDB  # noqa: F401
from app.models.user import UserDB, OAuthAccountDB  # noqa: F401


async def _alembic_applied(conn) -> bool:
    """Return True if alembic_version table exists, meaning Alembic has taken over."""
    if engine.dialect.name != "mysql":
        return False
    r = await conn.scalar(
        text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema=DATABASE() AND table_name='alembic_version'"
        )
    )
    return (r or 0) > 0


async def ensure_user_llm_columns(db: AsyncSession) -> None:
    """Add BYOK / LLM override columns + token_gen to users if missing（仅 MySQL）。"""
    if await _alembic_applied(db):
        return
    if engine.dialect.name != "mysql":
        return
    pairs = [
        ("llm_base_url", "ALTER TABLE users ADD COLUMN llm_base_url TEXT NULL"),
        ("llm_model", "ALTER TABLE users ADD COLUMN llm_model VARCHAR(512) NULL"),
        ("llm_api_key_encrypted", "ALTER TABLE users ADD COLUMN llm_api_key_encrypted TEXT NULL"),
        ("token_gen", "ALTER TABLE users ADD COLUMN token_gen INT NOT NULL DEFAULT 0"),
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
            logger.info(f"已添加列 users.{column_name}")


async def ensure_user_oauth_columns(db: AsyncSession) -> None:
    """Add nickname, email_verified columns and oauth_accounts table if missing（仅 MySQL）。"""
    if await _alembic_applied(db):
        return
    if engine.dialect.name != "mysql":
        return

    user_columns = [
        ("nickname", "ALTER TABLE users ADD COLUMN nickname VARCHAR(50) NULL"),
        ("email_verified", "ALTER TABLE users ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 0"),
    ]
    for column_name, ddl in user_columns:
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
            logger.info(f"已添加列 users.{column_name}")

    email_col_r = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'users'
              AND COLUMN_NAME = 'email'
            """
        )
    )
    if (email_col_r.scalar() or 0) > 0:
        length_r = await db.execute(
            text(
                """
                SELECT CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = 'email'
                """
            )
        )
        current_len = length_r.scalar() or 0
        if current_len < 255:
            await db.execute(text("ALTER TABLE users MODIFY COLUMN email VARCHAR(255) NULL"))
            logger.info("已扩展 users.email 长度到 255")

    table_r = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'oauth_accounts'
            """
        )
    )
    if (table_r.scalar() or 0) == 0:
        await db.execute(
            text(
                """
                CREATE TABLE oauth_accounts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    provider VARCHAR(20) NOT NULL,
                    openid VARCHAR(128) NOT NULL,
                    access_token TEXT NULL,
                    avatar_url VARCHAR(512) NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_provider (provider),
                    INDEX idx_openid (openid),
                    UNIQUE KEY uk_provider_openid (provider, openid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        )
        logger.info("已创建表 oauth_accounts")

    oauth_username_col_r = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'oauth_accounts'
              AND COLUMN_NAME = 'provider_username'
            """
        )
    )
    if (oauth_username_col_r.scalar() or 0) == 0:
        await db.execute(
            text("ALTER TABLE oauth_accounts ADD COLUMN provider_username VARCHAR(128) NULL")
        )
        logger.info("已添加列 oauth_accounts.provider_username")

    username_null_r = await db.execute(
        text(
            """
            SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'users'
              AND COLUMN_NAME = 'username'
            """
        )
    )
    is_nullable = username_null_r.scalar()
    if is_nullable and is_nullable.upper() == "NO":
        await db.execute(text("ALTER TABLE users MODIFY COLUMN username VARCHAR(50) NULL"))
        logger.info("已将 users.username 改为可空")
