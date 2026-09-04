"""app.core.redis_client 单元测试

覆盖：
- RedisClient 单例、连接失败降级、client/is_available/get_redis
- cache_recent_note / remove_recent_note_by_id / batch_cache_recent_notes
- get_recent_notes / clear_recent_notes
- blacklist_token / is_token_blacklisted / _rate_limit_bump
- _run_in_pool 及全部 async 包装
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.core import redis_client as rc_mod
from app.core.redis_client import (
    BLACKLIST_PREFIX,
    RedisClient,
    _rate_limit_bump,
    _run_in_pool,
    batch_cache_recent_notes,
    batch_cache_recent_notes_async,
    blacklist_token,
    cache_recent_note,
    cache_recent_note_async,
    clear_recent_notes,
    clear_recent_notes_async,
    get_recent_notes,
    get_recent_notes_async,
    get_redis,
    is_token_blacklisted,
    redis_client,
    remove_recent_note_by_id,
    remove_recent_note_by_id_async,
)


# ────────────────────── helpers ──────────────────────

def _set_client(mock_obj):
    """临时替换 redis_client._client，返回原始值以便恢复。"""
    original = redis_client._client
    redis_client._client = mock_obj
    return original


def _make_note_json(note_id: int, title: str = "t") -> str:
    return json.dumps({"id": note_id, "title": title}, ensure_ascii=False)


# ────────────────────── RedisClient 类 ──────────────────────

class TestRedisClientSingleton:
    def test_singleton_returns_same_instance(self):
        a = RedisClient()
        b = RedisClient()
        assert a is b

    def test_client_property_returns_internal_client(self):
        original = _set_client("fake-client")
        try:
            assert redis_client.client == "fake-client"
        finally:
            redis_client._client = original

    def test_is_available_true_when_client_set(self):
        original = _set_client(MagicMock())
        try:
            assert redis_client.is_available() is True
        finally:
            redis_client._client = original

    def test_is_available_false_when_client_none(self):
        original = _set_client(None)
        try:
            assert redis_client.is_available() is False
        finally:
            redis_client._client = original

    def test_get_redis_returns_client(self):
        original = _set_client("the-client")
        try:
            assert get_redis() == "the-client"
        finally:
            redis_client._client = original

    def test_init_redis_failure_sets_client_none(self):
        """模拟 redis.Redis 构造或 ping 抛异常，_client 应为 None。"""
        with patch("app.core.redis_client.redis.Redis", side_effect=ConnectionError("refused")):
            inst = RedisClient.__new__(RedisClient)
            inst._init_redis()
            assert inst._client is None

    def test_init_redis_success_creates_client(self):
        mock_redis_instance = MagicMock()
        with patch("app.core.redis_client.redis.Redis", return_value=mock_redis_instance) as mock_cls:
            inst = RedisClient.__new__(RedisClient)
            inst._init_redis()
            assert inst._client is mock_redis_instance
            mock_redis_instance.ping.assert_called_once()
            # 验证密码为 None 时不传入 password 参数
            call_kwargs = mock_cls.call_args[1]
            assert "password" not in call_kwargs

    def test_init_redis_with_password(self):
        mock_redis_instance = MagicMock()
        with patch("app.core.redis_client.redis.Redis", return_value=mock_redis_instance):
            with patch.object(rc_mod.settings, "REDIS_PASSWORD", "secret"):
                inst = RedisClient.__new__(RedisClient)
                inst._init_redis()
                call_kwargs = rc_mod.redis.Redis.call_args[1]
                assert call_kwargs.get("password") == "secret"


# ────────────────────── cache_recent_note ──────────────────────

class TestCacheRecentNote:
    def test_redis_unavailable_skips(self):
        original = _set_client(None)
        try:
            cache_recent_note(1, {"id": 1, "title": "x"})  # 不应抛异常
        finally:
            redis_client._client = original

    def test_caches_new_note(self):
        mock = MagicMock()
        mock.lrange.return_value = []
        original = _set_client(mock)
        try:
            cache_recent_note(42, {"id": 10, "title": "hello"})
            mock.lpush.assert_called_once()
            mock.ltrim.assert_called_once_with("recent_notes:42", 0, 19)
            mock.expire.assert_called_once()
        finally:
            redis_client._client = original

    def test_removes_existing_note_before_push(self):
        existing = _make_note_json(10, "old")
        mock = MagicMock()
        mock.lrange.return_value = [existing]
        original = _set_client(mock)
        try:
            cache_recent_note(1, {"id": 10, "title": "new"})
            mock.lrem.assert_called_once()
            mock.lpush.assert_called_once()
        finally:
            redis_client._client = original

    def test_keeps_other_notes_when_id_differs(self):
        existing = _make_note_json(99, "other")
        mock = MagicMock()
        mock.lrange.return_value = [existing]
        original = _set_client(mock)
        try:
            cache_recent_note(1, {"id": 10, "title": "new"})
            mock.lrem.assert_not_called()
        finally:
            redis_client._client = original

    def test_malformed_json_in_existing_is_skipped(self):
        mock = MagicMock()
        mock.lrange.return_value = ["not-valid-json{{"]
        original = _set_client(mock)
        try:
            cache_recent_note(1, {"id": 10, "title": "new"})
            mock.lpush.assert_called_once()
        finally:
            redis_client._client = original

    def test_exception_logged_and_swallowed(self):
        mock = MagicMock()
        mock.lrange.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            cache_recent_note(1, {"id": 10})  # 不应抛异常
        finally:
            redis_client._client = original


# ────────────────────── remove_recent_note_by_id ──────────────────────

class TestRemoveRecentNoteById:
    def test_redis_unavailable_returns(self):
        original = _set_client(None)
        try:
            remove_recent_note_by_id(1, 10)
        finally:
            redis_client._client = original

    def test_no_match_returns_early(self):
        mock = MagicMock()
        mock.lrange.return_value = [_make_note_json(99)]
        original = _set_client(mock)
        try:
            remove_recent_note_by_id(1, 10)
            mock.pipeline.assert_not_called()
        finally:
            redis_client._client = original

    def test_match_removes_and_rebuilds_list(self):
        mock = MagicMock()
        pipe = MagicMock()
        mock.pipeline.return_value = pipe
        mock.lrange.return_value = [_make_note_json(10), _make_note_json(20)]
        original = _set_client(mock)
        try:
            remove_recent_note_by_id(1, 10)
            pipe.delete.assert_called_once_with("recent_notes:1")
            # 只剩 id=20，reversed 后 lpush 一次
            assert pipe.lpush.call_count == 1
            pipe.expire.assert_called_once()
            pipe.execute.assert_called_once()
        finally:
            redis_client._client = original

    def test_match_all_kept_empty_no_expire(self):
        mock = MagicMock()
        pipe = MagicMock()
        mock.pipeline.return_value = pipe
        mock.lrange.return_value = [_make_note_json(10)]
        original = _set_client(mock)
        try:
            remove_recent_note_by_id(1, 10)
            pipe.delete.assert_called_once()
            pipe.lpush.assert_not_called()
            pipe.expire.assert_not_called()
        finally:
            redis_client._client = original

    def test_malformed_json_treated_as_kept(self):
        mock = MagicMock()
        mock.lrange.return_value = ["bad-json"]
        original = _set_client(mock)
        try:
            remove_recent_note_by_id(1, 10)
            mock.pipeline.assert_not_called()
        finally:
            redis_client._client = original

    def test_exception_swallowed(self):
        mock = MagicMock()
        mock.lrange.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            remove_recent_note_by_id(1, 10)
        finally:
            redis_client._client = original


# ────────────────────── batch_cache_recent_notes ──────────────────────

class TestBatchCacheRecentNotes:
    def test_redis_unavailable_skips(self):
        original = _set_client(None)
        try:
            batch_cache_recent_notes(1, [{"id": 1}])
        finally:
            redis_client._client = original

    def test_replaces_and_inserts_in_order(self):
        mock = MagicMock()
        original = _set_client(mock)
        try:
            notes = [{"id": 1}, {"id": 2}, {"id": 3}]
            batch_cache_recent_notes(1, notes)
            mock.delete.assert_called_once_with("recent_notes:1")
            # reversed: id=3,2,1 → lpush 3 次，最新 id=1 在左边
            assert mock.lpush.call_count == 3
            mock.expire.assert_called_once()
        finally:
            redis_client._client = original

    def test_limits_to_20(self):
        mock = MagicMock()
        original = _set_client(mock)
        try:
            notes = [{"id": i} for i in range(30)]
            batch_cache_recent_notes(1, notes)
            assert mock.lpush.call_count == 20
        finally:
            redis_client._client = original

    def test_exception_swallowed(self):
        mock = MagicMock()
        mock.delete.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            batch_cache_recent_notes(1, [{"id": 1}])
        finally:
            redis_client._client = original


# ────────────────────── get_recent_notes ──────────────────────

class TestGetRecentNotes:
    def test_redis_unavailable_returns_empty(self):
        original = _set_client(None)
        try:
            assert get_recent_notes(1) == []
        finally:
            redis_client._client = original

    def test_returns_parsed_notes(self):
        mock = MagicMock()
        mock.lrange.return_value = [_make_note_json(1), _make_note_json(2)]
        original = _set_client(mock)
        try:
            result = get_recent_notes(1, limit=5)
            assert len(result) == 2
            assert result[0]["id"] == 1
            mock.lrange.assert_called_once_with("recent_notes:1", 0, 4)
        finally:
            redis_client._client = original

    def test_skips_malformed_json(self):
        mock = MagicMock()
        mock.lrange.return_value = ["bad", _make_note_json(2)]
        original = _set_client(mock)
        try:
            result = get_recent_notes(1)
            assert len(result) == 1
            assert result[0]["id"] == 2
        finally:
            redis_client._client = original

    def test_exception_returns_empty(self):
        mock = MagicMock()
        mock.lrange.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            assert get_recent_notes(1) == []
        finally:
            redis_client._client = original


# ────────────────────── clear_recent_notes ──────────────────────

class TestClearRecentNotes:
    def test_redis_unavailable_returns(self):
        original = _set_client(None)
        try:
            clear_recent_notes(1)
        finally:
            redis_client._client = original

    def test_deletes_key(self):
        mock = MagicMock()
        original = _set_client(mock)
        try:
            clear_recent_notes(1)
            mock.delete.assert_called_once_with("recent_notes:1")
        finally:
            redis_client._client = original

    def test_exception_swallowed(self):
        mock = MagicMock()
        mock.delete.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            clear_recent_notes(1)
        finally:
            redis_client._client = original


# ────────────────────── blacklist_token ──────────────────────

class TestBlacklistToken:
    def test_redis_unavailable_returns_false(self):
        original = _set_client(None)
        try:
            assert blacklist_token("abc", 300) is False
        finally:
            redis_client._client = original

    def test_jti_format_uses_direct_key(self):
        mock = MagicMock()
        original = _set_client(mock)
        try:
            result = blacklist_token("user:123:abc", 300)
            assert result is True
            mock.setex.assert_called_once()
            key = mock.setex.call_args[0][0]
            assert key == f"{BLACKLIST_PREFIX}user:123:abc"
        finally:
            redis_client._client = original

    def test_plain_token_uses_hash_key(self):
        mock = MagicMock()
        original = _set_client(mock)
        try:
            result = blacklist_token("plain-token", 300)
            assert result is True
            key = mock.setex.call_args[0][0]
            assert key == f"{BLACKLIST_PREFIX}{hash('plain-token')}"
        finally:
            redis_client._client = original

    def test_ttl_clamped_to_min_1(self):
        mock = MagicMock()
        original = _set_client(mock)
        try:
            blacklist_token("jti:x", 0)
            ttl = mock.setex.call_args[0][1]
            assert ttl == 1
        finally:
            redis_client._client = original

    def test_exception_returns_false(self):
        mock = MagicMock()
        mock.setex.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            assert blacklist_token("jti:x", 300) is False
        finally:
            redis_client._client = original


# ────────────────────── is_token_blacklisted ──────────────────────

class TestIsTokenBlacklisted:
    def test_redis_unavailable_returns_true(self):
        """安全策略：Redis 不可用时保守拒绝。"""
        original = _set_client(None)
        try:
            assert is_token_blacklisted("any-token") is True
        finally:
            redis_client._client = original

    def test_token_in_blacklist_returns_true(self):
        mock = MagicMock()
        mock.exists.return_value = 1
        original = _set_client(mock)
        try:
            with patch("app.core.security.get_jti_from_token", return_value="jti-123"):
                assert is_token_blacklisted("token") is True
        finally:
            redis_client._client = original

    def test_token_not_in_blacklist_returns_false(self):
        mock = MagicMock()
        mock.exists.return_value = 0
        original = _set_client(mock)
        try:
            with patch("app.core.security.get_jti_from_token", return_value="jti-123"):
                assert is_token_blacklisted("token") is False
        finally:
            redis_client._client = original

    def test_no_jti_falls_back_to_hash(self):
        mock = MagicMock()
        mock.exists.return_value = 0
        original = _set_client(mock)
        try:
            with patch("app.core.security.get_jti_from_token", return_value=None):
                is_token_blacklisted("old-token")
                key = mock.exists.call_args[0][0]
                assert key == f"{BLACKLIST_PREFIX}{hash('old-token')}"
        finally:
            redis_client._client = original

    def test_exception_returns_true(self):
        mock = MagicMock()
        mock.exists.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            with patch("app.core.security.get_jti_from_token", return_value="jti"):
                assert is_token_blacklisted("token") is True
        finally:
            redis_client._client = original


# ────────────────────── _rate_limit_bump ──────────────────────

class TestRateLimitBump:
    def test_redis_unavailable_returns_none(self):
        original = _set_client(None)
        try:
            assert _rate_limit_bump("key", 60) is None
        finally:
            redis_client._client = original

    def test_first_bump_sets_ttl(self):
        mock = MagicMock()
        mock.incr.return_value = 1
        original = _set_client(mock)
        try:
            result = _rate_limit_bump("rl:1", 60)
            assert result == 1
            mock.expire.assert_called_once_with("rl:1", 60)
        finally:
            redis_client._client = original

    def test_subsequent_bump_no_ttl(self):
        mock = MagicMock()
        mock.incr.return_value = 5
        original = _set_client(mock)
        try:
            result = _rate_limit_bump("rl:1", 60)
            assert result == 5
            mock.expire.assert_not_called()
        finally:
            redis_client._client = original

    def test_exception_returns_none(self):
        mock = MagicMock()
        mock.incr.side_effect = RuntimeError("boom")
        original = _set_client(mock)
        try:
            assert _rate_limit_bump("rl:1", 60) is None
        finally:
            redis_client._client = original


# ────────────────────── _run_in_pool & async wrappers ──────────────────────

class TestRunInPool:
    @pytest.mark.asyncio
    async def test_success_returns_result(self):
        def sync_func(x):
            return x * 2

        result = await _run_in_pool(sync_func, 21)
        assert result == 42

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        def sync_func():
            raise RuntimeError("boom")

        result = await _run_in_pool(sync_func)
        assert result is None


class TestAsyncWrappers:
    @pytest.mark.asyncio
    async def test_cache_recent_note_async(self):
        with patch("app.core.redis_client.cache_recent_note") as mock_sync:
            await cache_recent_note_async(1, {"id": 1})
            mock_sync.assert_called_once_with(1, {"id": 1})

    @pytest.mark.asyncio
    async def test_get_recent_notes_async(self):
        with patch("app.core.redis_client.get_recent_notes", return_value=[{"id": 1}]):
            result = await get_recent_notes_async(1, limit=5)
            assert result == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_get_recent_notes_async_none_returns_empty(self):
        with patch("app.core.redis_client.get_recent_notes", return_value=None):
            result = await get_recent_notes_async(1)
            assert result == []

    @pytest.mark.asyncio
    async def test_batch_cache_recent_notes_async(self):
        with patch("app.core.redis_client.batch_cache_recent_notes") as mock_sync:
            await batch_cache_recent_notes_async(1, [{"id": 1}])
            mock_sync.assert_called_once_with(1, [{"id": 1}])

    @pytest.mark.asyncio
    async def test_clear_recent_notes_async(self):
        with patch("app.core.redis_client.clear_recent_notes") as mock_sync:
            await clear_recent_notes_async(1)
            mock_sync.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_remove_recent_note_by_id_async(self):
        with patch("app.core.redis_client.remove_recent_note_by_id") as mock_sync:
            await remove_recent_note_by_id_async(1, 10)
            mock_sync.assert_called_once_with(1, 10)
