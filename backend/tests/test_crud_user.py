"""app.crud.user CRUD 测试

使用 async_db_session fixture，测试用户和 OAuth 账号的增删查改。
"""

import os

import pytest

from app.core.security import get_password_hash, verify_password
from app.crud.user import (
    authenticate_user,
    create_oauth_account,
    create_user,
    delete_oauth_account,
    get_oauth_account,
    get_user,
    get_user_by_email,
    get_user_by_username,
    get_user_oauth_accounts,
    get_user_oauth_by_provider,
    get_users,
)
from app.models.user import OAuthAccountDB, UserDB


def _random_email():
    return f"test_{os.urandom(4).hex()}@example.com"


def _random_str(prefix: str = "") -> str:
    return f"{prefix}{os.urandom(4).hex()}"


# ============== User CRUD ==============

@pytest.mark.asyncio
async def test_create_user(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="Test123456", nickname="测试用户")
    assert user.id is not None
    assert user.email == email
    assert user.nickname == "测试用户"
    assert user.hashed_password is not None
    # 密码应被哈希，不是明文
    assert user.hashed_password != "Test123456"
    assert verify_password("Test123456", user.hashed_password)


@pytest.mark.asyncio
async def test_create_user_with_username(async_db_session):
    email = _random_email()
    username = _random_str("user_")
    user = await create_user(async_db_session, email=email, password="pwd", nickname="nick", username=username)
    assert user.username == username


@pytest.mark.asyncio
async def test_create_user_default_nickname(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    assert user.nickname is None


@pytest.mark.asyncio
async def test_get_user(async_db_session):
    email = _random_email()
    created = await create_user(async_db_session, email=email, password="pwd", nickname="获取测试")
    fetched = await get_user(async_db_session, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.email == email


@pytest.mark.asyncio
async def test_get_user_not_found(async_db_session):
    result = await get_user(async_db_session, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email(async_db_session):
    email = _random_email()
    await create_user(async_db_session, email=email, password="pwd")
    fetched = await get_user_by_email(async_db_session, email)
    assert fetched is not None
    assert fetched.email == email


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(async_db_session):
    result = await get_user_by_email(async_db_session, "nonexistent@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_username(async_db_session):
    email = _random_email()
    username = _random_str("unique_")
    await create_user(async_db_session, email=email, password="pwd", username=username)
    fetched = await get_user_by_username(async_db_session, username)
    assert fetched is not None
    assert fetched.username == username


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(async_db_session):
    result = await get_user_by_username(async_db_session, "nosuchuser")
    assert result is None


@pytest.mark.asyncio
async def test_get_users(async_db_session):
    # 至少能查到之前创建的用户
    email1 = _random_email()
    email2 = _random_email()
    await create_user(async_db_session, email=email1, password="pwd")
    await create_user(async_db_session, email=email2, password="pwd")

    # 用大 limit 避免历史数据溢出
    users = await get_users(async_db_session, limit=10000)
    assert len(users) >= 2
    emails = [u.email for u in users]
    assert email1 in emails
    assert email2 in emails


@pytest.mark.asyncio
async def test_get_users_with_pagination(async_db_session):
    # 创建一些用户
    for i in range(3):
        await create_user(async_db_session, email=f"page_{os.urandom(4).hex()}_{i}@example.com", password="pwd")
    # 分页查询
    users_page1 = await get_users(async_db_session, skip=0, limit=2)
    assert len(users_page1) == 2
    users_page2 = await get_users(async_db_session, skip=2, limit=2)
    assert len(users_page2) >= 1


# ============== authenticate_user ==============

@pytest.mark.asyncio
async def test_authenticate_user_success(async_db_session):
    email = _random_email()
    await create_user(async_db_session, email=email, password="CorrectPass123")
    user = await authenticate_user(async_db_session, email, "CorrectPass123")
    assert user is not False
    assert user.email == email


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(async_db_session):
    email = _random_email()
    await create_user(async_db_session, email=email, password="CorrectPass123")
    result = await authenticate_user(async_db_session, email, "WrongPass")
    assert result is False


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent(async_db_session):
    result = await authenticate_user(async_db_session, "nobody@example.com", "password")
    assert result is False


# ============== OAuth Account CRUD ==============

@pytest.mark.asyncio
async def test_create_oauth_account(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    openid = _random_str("gh_")
    oauth = await create_oauth_account(
        async_db_session,
        user_id=user.id,
        provider="github",
        openid=openid,
        access_token="gho_token",
        avatar_url="https://avatar.url",
        provider_username="ghuser",
    )
    assert oauth.id is not None
    assert oauth.user_id == user.id
    assert oauth.provider == "github"
    assert oauth.openid == openid
    assert oauth.access_token == "gho_token"
    assert oauth.avatar_url == "https://avatar.url"
    assert oauth.provider_username == "ghuser"


@pytest.mark.asyncio
async def test_create_oauth_account_minimal(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    openid = _random_str("go_")
    oauth = await create_oauth_account(
        async_db_session,
        user_id=user.id,
        provider="google",
        openid=openid,
    )
    assert oauth.id is not None
    assert oauth.access_token is None
    assert oauth.avatar_url is None
    assert oauth.provider_username is None


@pytest.mark.asyncio
async def test_get_oauth_account(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    openid = _random_str("gh_get_")
    await create_oauth_account(async_db_session, user_id=user.id, provider="github", openid=openid)
    oauth = await get_oauth_account(async_db_session, "github", openid)
    assert oauth is not None
    assert oauth.provider == "github"
    assert oauth.openid == openid


@pytest.mark.asyncio
async def test_get_oauth_account_not_found(async_db_session):
    result = await get_oauth_account(async_db_session, "github", "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_user_oauth_accounts(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    await create_oauth_account(async_db_session, user_id=user.id, provider="github", openid=_random_str("gh1_"))
    await create_oauth_account(async_db_session, user_id=user.id, provider="google", openid=_random_str("go1_"))

    accounts = await get_user_oauth_accounts(async_db_session, user.id)
    assert len(accounts) == 2
    providers = [a.provider for a in accounts]
    assert "github" in providers
    assert "google" in providers


@pytest.mark.asyncio
async def test_get_user_oauth_accounts_empty(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    accounts = await get_user_oauth_accounts(async_db_session, user.id)
    assert accounts == []


@pytest.mark.asyncio
async def test_get_user_oauth_by_provider(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    await create_oauth_account(async_db_session, user_id=user.id, provider="github", openid=_random_str("ghp_"))
    await create_oauth_account(async_db_session, user_id=user.id, provider="google", openid=_random_str("gop_"))

    gh = await get_user_oauth_by_provider(async_db_session, user.id, "github")
    assert gh is not None
    assert gh.provider == "github"

    go = await get_user_oauth_by_provider(async_db_session, user.id, "google")
    assert go is not None
    assert go.provider == "google"


@pytest.mark.asyncio
async def test_get_user_oauth_by_provider_not_found(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    result = await get_user_oauth_by_provider(async_db_session, user.id, "wechat")
    assert result is None


@pytest.mark.asyncio
async def test_delete_oauth_account(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    await create_oauth_account(async_db_session, user_id=user.id, provider="github", openid=_random_str("ghd_"))

    deleted = await delete_oauth_account(async_db_session, user.id, "github")
    assert deleted is not None
    assert deleted.provider == "github"

    # 删除后应找不到
    result = await get_user_oauth_by_provider(async_db_session, user.id, "github")
    assert result is None


@pytest.mark.asyncio
async def test_delete_oauth_account_not_found(async_db_session):
    email = _random_email()
    user = await create_user(async_db_session, email=email, password="pwd")
    result = await delete_oauth_account(async_db_session, user.id, "nonexistent")
    assert result is None
