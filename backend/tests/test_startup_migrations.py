"""app.core.startup_migrations 测试

通过 mock engine.dialect 和 db.execute 来测试幂等 DDL 迁移函数。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.startup_migrations import (
    _alembic_applied,
    ensure_ai_conversation_tables,
    ensure_user_llm_columns,
    ensure_user_oauth_columns,
)


def _make_mock_db(scalar_returns=None):
    """创建一个 mock db，execute 返回指定的 scalar 值序列。"""
    mock_db = MagicMock()
    if scalar_returns is None:
        scalar_returns = [1]  # 默认都存在
    returns_iter = iter(scalar_returns)

    async def mock_execute(*args, **kwargs):
        result = MagicMock()
        try:
            val = next(returns_iter)
        except StopIteration:
            val = 1
        result.scalar.return_value = val
        return result

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    return mock_db


# ============== _alembic_applied ==============

@pytest.mark.asyncio
async def test_alembic_applied_non_mysql():
    with patch("app.core.startup_migrations.engine") as mock_engine:
        mock_engine.dialect.name = "sqlite"
        result = await _alembic_applied(MagicMock())
        assert result is False


@pytest.mark.asyncio
async def test_alembic_applied_mysql_no_table():
    mock_conn = MagicMock()
    mock_conn.scalar = AsyncMock(return_value=0)

    with patch("app.core.startup_migrations.engine") as mock_engine:
        mock_engine.dialect.name = "mysql"
        result = await _alembic_applied(mock_conn)
        assert result is False


@pytest.mark.asyncio
async def test_alembic_applied_mysql_with_table():
    mock_conn = MagicMock()
    mock_conn.scalar = AsyncMock(return_value=1)

    with patch("app.core.startup_migrations.engine") as mock_engine:
        mock_engine.dialect.name = "mysql"
        result = await _alembic_applied(mock_conn)
        assert result is True


# ============== ensure_user_llm_columns ==============

@pytest.mark.asyncio
async def test_ensure_user_llm_columns_skipped_when_alembic():
    mock_db = MagicMock()
    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic:
        mock_alembic.return_value = True
        await ensure_user_llm_columns(mock_db)
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_user_llm_columns_skipped_non_mysql():
    mock_db = MagicMock()
    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "sqlite"
        await ensure_user_llm_columns(mock_db)
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_user_llm_columns_all_exist():
    # 4 列查询都返回 1（存在）
    mock_db = _make_mock_db([1, 1, 1, 1])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_user_llm_columns(mock_db)

    # 只执行 4 次查询，不执行 ALTER
    assert mock_db.execute.await_count == 4


@pytest.mark.asyncio
async def test_ensure_user_llm_columns_missing_columns():
    # 4 列查询都返回 0（不存在），然后 4 次 ALTER
    # 提供 8 个值，确保 ALTER 调用也有返回值
    mock_db = _make_mock_db([0, 0, 0, 0, 0, 0, 0, 0])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_user_llm_columns(mock_db)

    # 4 列查询 + 4 列 ALTER = 8 次
    assert mock_db.execute.await_count == 8


# ============== ensure_user_oauth_columns ==============

@pytest.mark.asyncio
async def test_ensure_user_oauth_columns_skipped_when_alembic():
    mock_db = MagicMock()
    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic:
        mock_alembic.return_value = True
        await ensure_user_oauth_columns(mock_db)
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_user_oauth_columns_skipped_non_mysql():
    mock_db = MagicMock()
    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "postgresql"
        await ensure_user_oauth_columns(mock_db)
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_user_oauth_columns_all_exist():
    # nickname, email_verified, email列存在, email长度255, oauth表存在, provider_username存在, username可空
    mock_db = _make_mock_db([1, 1, 1, 255, 1, 1, "YES"])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_user_oauth_columns(mock_db)

    # 只查询，不执行 ALTER/CREATE
    assert mock_db.execute.await_count == 7


@pytest.mark.asyncio
async def test_ensure_user_oauth_columns_email_too_short():
    # nickname存在, email_verified存在, email列存在, email长度100(太短)→ALTER, oauth表存在, provider_username存在, username可空
    # 序列：4查询 + 1ALTER + 3查询 = 8 次 execute
    mock_db = _make_mock_db([1, 1, 1, 100, 1, 1, 1, "YES"] + [1] * 20)

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_user_oauth_columns(mock_db)

    # 应该多执行一次 ALTER 扩展 email
    assert mock_db.execute.await_count == 8


@pytest.mark.asyncio
async def test_ensure_user_oauth_columns_create_oauth_table():
    # nickname存在, email_verified存在, email列存在, email长度255, oauth表不存在(0)→CREATE, provider_username存在, username可空
    # 序列：5查询 + 1CREATE + 2查询 = 8 次 execute
    mock_db = _make_mock_db([1, 1, 1, 255, 0, 1, 1, "YES"] + [1] * 20)

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_user_oauth_columns(mock_db)

    # 应该多执行一次 CREATE TABLE
    assert mock_db.execute.await_count == 8


@pytest.mark.asyncio
async def test_ensure_user_oauth_columns_username_not_nullable():
    # nickname存在, email_verified存在, email列存在, email长度255, oauth表存在, provider_username存在, username不可空(NO)
    # 提供 8 个值，确保 ALTER 调用也有返回值
    mock_db = _make_mock_db([1, 1, 1, 255, 1, 1, "NO", 1])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_user_oauth_columns(mock_db)

    # 应该多执行一次 ALTER 修改 username
    assert mock_db.execute.await_count == 8


# ============== ensure_ai_conversation_tables ==============

@pytest.mark.asyncio
async def test_ensure_ai_conversation_tables_skipped_when_alembic():
    mock_db = MagicMock()
    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic:
        mock_alembic.return_value = True
        await ensure_ai_conversation_tables(mock_db)
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_ai_conversation_tables_skipped_non_mysql():
    mock_db = MagicMock()
    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "sqlite"
        await ensure_ai_conversation_tables(mock_db)
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_ai_conversation_tables_all_exist():
    # 两张表都存在
    mock_db = _make_mock_db([1, 1])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_ai_conversation_tables(mock_db)

    # 只查询，不创建
    assert mock_db.execute.await_count == 2


@pytest.mark.asyncio
async def test_ensure_ai_conversation_tables_create_both():
    # 两张表都不存在
    # 提供 4 个值，确保 CREATE 调用也有返回值
    mock_db = _make_mock_db([0, 0, 0, 0])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_ai_conversation_tables(mock_db)

    # 2 次查询 + 2 次 CREATE = 4
    assert mock_db.execute.await_count == 4


@pytest.mark.asyncio
async def test_ensure_ai_conversation_tables_only_messages_missing():
    # ai_conversations 存在，ai_messages 不存在
    mock_db = _make_mock_db([1, 0])

    with patch("app.core.startup_migrations._alembic_applied", new_callable=AsyncMock) as mock_alembic, \
         patch("app.core.startup_migrations.engine") as mock_engine:
        mock_alembic.return_value = False
        mock_engine.dialect.name = "mysql"
        await ensure_ai_conversation_tables(mock_db)

    # 2 次查询 + 1 次 CREATE = 3
    assert mock_db.execute.await_count == 3
