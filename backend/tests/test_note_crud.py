from app.crud import note as crud_note
from app.models.note import NoteDB


async def _create_test_note(db, user_id: int, title: str = "Test", content: str = "Hello", tags: str = "test"):
    return await crud_note.create_note(db, user_id=user_id, title=title, content=content, tags=tags, is_favorite=1)


async def test_create_and_get_note(async_db_session, test_user_id):
    note = await _create_test_note(async_db_session, test_user_id)
    assert note.id is not None
    assert note.title == "Test"
    assert note.content == "Hello"

    fetched = await crud_note.get_note(async_db_session, note.id, test_user_id)
    assert fetched is not None
    assert fetched.id == note.id


async def test_search_notes_by_title(async_db_session, test_user_id):
    await _create_test_note(async_db_session, test_user_id, title="Python笔记")
    await _create_test_note(async_db_session, test_user_id, title="Java笔记")

    results = await crud_note.search_notes(async_db_session, test_user_id, keyword="Python")
    assert len(results) == 1
    assert results[0].title == "Python笔记"


async def test_search_notes_matches_content(async_db_session, test_user_id):
    """RAG 化后正文关键词可命中（原行为：仅标题可搜）"""
    await _create_test_note(
        async_db_session,
        test_user_id,
        title="普通标题",
        content="这是一个关于机器学习的笔记",
    )
    results = await crud_note.search_notes(async_db_session, test_user_id, keyword="机器学习")
    assert len(results) == 1
    assert results[0].title == "普通标题"


async def test_search_notes_favorite_filter(async_db_session, test_user_id):
    await crud_note.create_note(async_db_session, test_user_id, title="收藏笔记1", content="a", is_favorite=1)
    await crud_note.create_note(async_db_session, test_user_id, title="未收藏笔记", content="b", is_favorite=0)

    fav = await crud_note.search_notes(async_db_session, test_user_id, is_favorite=True)
    assert len(fav) == 1
    assert fav[0].title == "收藏笔记1"

    non_fav = await crud_note.search_notes(async_db_session, test_user_id, is_favorite=False)
    assert len(non_fav) == 1
    assert non_fav[0].title == "未收藏笔记"


async def test_search_pagination(async_db_session, test_user_id):
    for i in range(5):
        await _create_test_note(async_db_session, test_user_id, title=f"笔记{i}", content=f"内容{i}")

    page1 = await crud_note.search_notes(async_db_session, test_user_id, skip=0, limit=2)
    assert len(page1) == 2

    page2 = await crud_note.search_notes(async_db_session, test_user_id, skip=2, limit=2)
    assert len(page2) == 2


async def test_count_notes(async_db_session, test_user_id):
    await _create_test_note(async_db_session, test_user_id, title="AI笔记1")
    await _create_test_note(async_db_session, test_user_id, title="AI笔记2")
    await _create_test_note(async_db_session, test_user_id, title="其他")

    total = await crud_note.count_notes(async_db_session, test_user_id)
    assert total == 3

    matched = await crud_note.count_notes(async_db_session, test_user_id, keyword="AI")
    assert matched == 2


async def test_update_note(async_db_session, test_user_id):
    note = await _create_test_note(async_db_session, test_user_id)
    updated = await crud_note.update_note(async_db_session, note.id, test_user_id, title="Updated")
    assert updated.title == "Updated"


async def test_delete_note(async_db_session, test_user_id):
    note = await _create_test_note(async_db_session, test_user_id)
    await crud_note.delete_note(async_db_session, note.id, test_user_id)
    fetched = await crud_note.get_note(async_db_session, note.id, test_user_id)
    assert fetched is None
