"""Token 撤销与代数失效的单元测试：jti 黑名单 + token_gen 代数校验。

覆盖：
- create_access_token 的 jti 格式（sub:tgen:uuid）与 tgen 载荷
- get_jti_from_token / get_token_exp_seconds 边界
- _check_tgen_valid 各分支（无 tgen_min / 旧 token / 当前 token / Redis 不可用）
- get_current_user 主流程（有效、黑名单、签名错误）
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core import security
from app.core.config import settings


def _make_token(email: str, tgen: int = 0) -> str:
    return security.create_access_token({"sub": email}, token_gen=tgen)


class TestJtiAndPayload:
    def test_jti_contains_sub_tgen_uuid(self):
        payload = jwt.decode(_make_token("u@example.com", tgen=3), settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["jti"].startswith("u@example.com:3:")
        assert payload["tgen"] == 3

    def test_jti_uses_uuid4_hex_suffix(self):
        payload = jwt.decode(_make_token("u@example.com"), settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload["jti"]
        suffix = jti.rsplit(":", 1)[1]
        assert len(suffix) == 32  # uuid4().hex

    def test_get_jti_from_token_valid(self):
        token = _make_token("u@example.com")
        assert security.get_jti_from_token(token)

    def test_get_jti_from_token_invalid(self):
        assert security.get_jti_from_token("not.a.jwt") is None

    def test_get_token_exp_seconds_positive(self):
        assert security.get_token_exp_seconds(_make_token("u@example.com")) > 0


class TestTgenCheck:
    def test_allow_when_no_tgen_min(self):
        redis = SimpleNamespace(client=SimpleNamespace(get=lambda k: None))
        assert security._check_tgen_valid("u@example.com", 0, redis) is True

    def test_reject_old_token(self):
        redis = SimpleNamespace(client=SimpleNamespace(get=lambda k: b"5"))
        assert security._check_tgen_valid("u@example.com", 3, redis) is False

    def test_allow_current_token(self):
        redis = SimpleNamespace(client=SimpleNamespace(get=lambda k: b"3"))
        assert security._check_tgen_valid("u@example.com", 3, redis) is True

    def test_allow_redis_down(self):
        assert security._check_tgen_valid("u@example.com", 0, None) is True


class TestGetCurrentUser:
    def test_valid_token_returns_email(self):
        token = _make_token("u@example.com")
        with (
            patch("app.core.security.is_token_blacklisted", return_value=False),
            patch("app.core.redis_client.redis_client", SimpleNamespace(client=None)),
        ):
            assert security.get_current_user(token) == {"email": "u@example.com"}

    def test_blacklisted_token_rejected(self):
        token = _make_token("u@example.com")
        with patch("app.core.security.is_token_blacklisted", return_value=True):
            with pytest.raises(HTTPException) as exc:
                security.get_current_user(token)
            assert exc.value.status_code == 401

    def test_invalid_signature_rejected(self):
        with patch("app.core.security.is_token_blacklisted", return_value=False):
            with pytest.raises(HTTPException) as exc:
                security.get_current_user("bad.token.value")
            assert exc.value.status_code == 401
