"""app.crud.ai_conversation CRUD 测试

使用 async_db_session 和 test_user_id fixture，测试对话和消息的增删查改。
"""

import pytest

from app.crud.ai_conversation import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
    rename_conversation,
)
from app.models.ai_conversation import AIMessageDB


# ============== Conversation CRUD ==============

@pytest.mark.asyncio
async def test_create_conversation(async_db_session, test_user_id):
    conv = await create_conversation(async_db_session, test_user_id, "测试对话")
    assert conv.id is not None
    assert conv.user_id == test_user_id
    assert conv.title == "测试对话"
    assert conv.created_at is not None


@pytest.mark.asyncio
async def test_get_conversation(async_db_session, test_user_id):
    created = await create_conversation(async_db_session, test_user_id, "获取测试")
    fetched = await get_conversation(async_db_session, created.id, test_user_id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "获取测试"


@pytest.mark.asyncio
async def test_get_conversation_not_found(async_db_session, test_user_id):
    result = await get_conversation(async_db_session, 99999, test_user_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_conversation_wrong_user(async_db_session, test_user_id):
    """对话不属于该用户时应返回 None"""
    created = await create_conversation(async_db_session, test_user_id, "他人对话")
    result = await get_conversation(async_db_session, created.id, user_id=99999)
    assert result is None


@pytest.mark.asyncio
async def test_list_conversations(async_db_session, test_user_id):
    await create_conversation(async_db_session, test_user_id, "对话1")
    await create_conversation(async_db_session, test_user_id, "对话2")
    await create_conversation(async_db_session, test_user_id, "对话3")

    convs = await list_conversations(async_db_session, test_user_id)
    assert len(convs) >= 3
    # 按 updated_at 倒序
    titles = [c.title for c in convs]
    assert "对话1" in titles
    assert "对话2" in titles
    assert "对话3" in titles


@pytest.mark.asyncio
async def test_list_conversations_with_limit(async_db_session, test_user_id):
    for i in range(5):
        await create_conversation(async_db_session, test_user_id, f"对话{i}")
    convs = await list_conversations(async_db_session, test_user_id, limit=2)
    assert len(convs) == 2


@pytest.mark.asyncio
async def test_list_conversations_empty(async_db_session):
    """没有对话的用户应返回空列表"""
    from app.core.security import get_password_hash
    from app.models.user import UserDB
    import os
    random_suffix = os.urandom(4).hex()
    user = UserDB(
        username=f"empty_user_{random_suffix}",
        email=f"empty_{random_suffix}@example.com",
        hashed_password=get_password_hash("test123"),
    )
    async_db_session.add(user)
    await async_db_session.flush()
    await async_db_session.refresh(user)

    convs = await list_conversations(async_db_session, user.id)
    assert convs == []


@pytest.mark.asyncio
async def test_rename_conversation(async_db_session, test_user_id):
    created = await create_conversation(async_db_session, test_user_id, "旧标题")
    updated = await rename_conversation(async_db_session, created.id, test_user_id, "新标题")
    assert updated is not None
    assert updated.title == "新标题"


@pytest.mark.asyncio
async def test_rename_conversation_not_found(async_db_session, test_user_id):
    result = await rename_conversation(async_db_session, 99999, test_user_id, "新标题")
    assert result is None


@pytest.mark.asyncio
async def test_delete_conversation(async_db_session, test_user_id):
    created = await create_conversation(async_db_session, test_user_id, "待删除")
    result = await delete_conversation(async_db_session, created.id, test_user_id)
    assert result is True
    # 删除后应找不到
    fetched = await get_conversation(async_db_session, created.id, test_user_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_conversation_not_found(async_db_session, test_user_id):
    result = await delete_conversation(async_db_session, 99999, test_user_id)
    assert result is False


@pytest.mark.asyncio
async def test_delete_conversation_cascades_messages(async_db_session, test_user_id):
    """删除对话时应同时删除其下的消息"""
    conv = await create_conversation(async_db_session, test_user_id, "级联测试")
    # 手动添加消息
    msg1 = AIMessageDB(conversation_id=conv.id, role="user", content="你好")
    msg2 = AIMessageDB(conversation_id=conv.id, role="assistant", content="你好！")
    async_db_session.add_all([msg1, msg2])
    await async_db_session.flush()

    result = await delete_conversation(async_db_session, conv.id, test_user_id)
    assert result is True

    # 验证消息也被删除
    from sqlalchemy import select
    result_msgs = await async_db_session.execute(
        select(AIMessageDB).where(AIMessageDB.conversation_id == conv.id)
    )
    assert result_msgs.scalars().all() == []


# ============== Message CRUD ==============

@pytest.mark.asyncio
async def test_list_messages(async_db_session, test_user_id):
    conv = await create_conversation(async_db_session, test_user_id, "消息测试")
    msg1 = AIMessageDB(conversation_id=conv.id, role="user", content="第一条")
    msg2 = AIMessageDB(conversation_id=conv.id, role="assistant", content="第二条")
    async_db_session.add_all([msg1, msg2])
    await async_db_session.flush()

    messages = await list_messages(async_db_session, conv.id, test_user_id)
    assert len(messages) == 2
    assert messages[0].content == "第一条"
    assert messages[1].content == "第二条"
    # 按时间正序
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_list_messages_wrong_user(async_db_session, test_user_id):
    conv = await create_conversation(async_db_session, test_user_id, "他人消息")
    msg = AIMessageDB(conversation_id=conv.id, role="user", content="消息")
    async_db_session.add(msg)
    await async_db_session.flush()

    messages = await list_messages(async_db_session, conv.id, user_id=99999)
    assert messages == []


@pytest.mark.asyncio
async def test_list_messages_conversation_not_found(async_db_session, test_user_id):
    messages = await list_messages(async_db_session, 99999, test_user_id)
    assert messages == []


@pytest.mark.asyncio
async def test_list_messages_empty(async_db_session, test_user_id):
    conv = await create_conversation(async_db_session, test_user_id, "空消息")
    messages = await list_messages(async_db_session, conv.id, test_user_id)
    assert messages == []
