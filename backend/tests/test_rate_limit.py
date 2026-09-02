"""速率限制单元测试（mock Redis 计数层）。

覆盖：
- key 生成格式
- 客户端 IP 提取（X-Forwarded-For 只取第一段）
- 未知策略放行 / 超限抛 429 / 未超限放行
- Redis 异常降级放行 / RATE_LIMIT_DISABLED 放行
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.core import rate_limit


def test_build_key_format():
    assert rate_limit._build_key("login", "1.2.3.4") == "rate_limit:login:1.2.3.4"


def test_client_ip_uses_first_forwarded_segment():
    req = SimpleNamespace(headers={"x-forwarded-for": "10.0.0.1, 10.0.0.2"}, client=None)
    assert rate_limit._client_ip(req) == "10.0.0.1"


def test_client_ip_falls_back_to_host():
    req = SimpleNamespace(headers={}, client=SimpleNamespace(host="192.168.1.1"))
    assert rate_limit._client_ip(req) == "192.168.1.1"


def test_unknown_policy_allows():
    assert rate_limit.check_and_bump("no_such_policy", "x") is None


def test_over_limit_raises_429(monkeypatch):
    # conftest 全局设 RATE_LIMIT_DISABLED=1，此处显式关闭以测真实限流
    monkeypatch.delenv("RATE_LIMIT_DISABLED", raising=False)
    # login 策略: 5 次 / 60s，计数 11 → 超限
    with patch("app.core.rate_limit._redis_bump", return_value=11):
        with pytest.raises(HTTPException) as exc:
            rate_limit.check_and_bump("login", "1.2.3.4")
        assert exc.value.status_code == 429


def test_under_limit_allows():
    with patch("app.core.rate_limit._redis_bump", return_value=2):
        rate_limit.check_and_bump("login", "1.2.3.4")


def test_redis_exception_degrades_allow():
    with patch("app.core.rate_limit._redis_bump", side_effect=Exception("redis down")):
        rate_limit.check_and_bump("login", "1.2.3.4")


def test_disabled_skips_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_DISABLED", "1")
    with patch("app.core.rate_limit._redis_bump", return_value=999):
        rate_limit.check_and_bump("login", "1.2.3.4")
    monkeypatch.delenv("RATE_LIMIT_DISABLED")
