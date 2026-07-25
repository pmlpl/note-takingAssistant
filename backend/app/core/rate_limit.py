"""Simple Redis-backed rate limiter (sliding-window counting).

设计目标：
- 未登录接口（register/login）按客户端 IP 节流
- 已登录接口（ai/notes/user）按用户名节流
- Redis 不可用时降级为「放行」而非拒绝，保证基本可用性
- 测试环境（RATE_LIMIT_DISABLED=1）直接放行，避免 CI 单 IP 触发限流
"""
from __future__ import annotations

import os
import time
from typing import Callable, Dict, Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.redis_client import (
    redis_client,
    _rate_limit_bump as _redis_bump,  # type: ignore[attr-defined]
)


def _is_disabled() -> bool:
    """测试环境可通过环境变量禁用速率限制"""
    return os.environ.get("RATE_LIMIT_DISABLED", "0") == "1"


# 命名限流策略：key_prefix -> (max_requests, window_seconds)
LIMIT_POLICIES: Dict[str, tuple[int, int]] = {
    "register": (10, 3600),
    "login": (5, 60),
    "email_code": (3, 300),
    "email_verify": (10, 300),
    "ai": (60, 60),
    "notes": (120, 60),
    "public": (60, 60),
}


def _client_ip(request: Request) -> str:
    """从请求中提取客户端 IP（兼容代理场景 X-Forwarded-For，但只取第一段）。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _build_key(policy_name: str, identifier: str) -> str:
    """Redis key：rate_limit:{policy}:{identifier}。"""
    return f"rate_limit:{policy_name}:{identifier}"


class RateLimitExceeded(HTTPException):
    """请求过于频繁。"""

    def __init__(self, detail: str = "请求过于频繁，请稍后再试"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


def check_and_bump(policy_name: str, identifier: str) -> None:
    """
    对当前请求做「计数 + 校验」两步操作。
    通过（或 Redis 不可用时降级放行）不抛异常；超过阈值则抛 RateLimitExceeded。
    """
    if _is_disabled():
        return  # 测试环境：直接放行
    if policy_name not in LIMIT_POLICIES:
        return  # 未知策略：放行（保守处理）
    max_req, window_sec = LIMIT_POLICIES[policy_name]
    key = _build_key(policy_name, identifier)

    # Redis 不可用时直接放行（降级）
    try:
        current = _redis_bump(key, window_seconds=window_sec)
    except Exception:
        return

    if current is None:
        # Redis 不可用：降级放行
        return
    if current > max_req:
        raise RateLimitExceeded()


# ===== FastAPI Dependency 工厂 =====

def rate_limit_anon(policy_name: str) -> Callable[[Request], None]:
    """未登录接口的限流依赖 —— 按客户端 IP。"""

    def _dep(request: Request) -> None:
        check_and_bump(policy_name, _client_ip(request))

    return _dep


def rate_limit_user(policy_name: str) -> Callable[[Request, dict], None]:
    """已登录接口的限流依赖 —— 优先按邮箱，退化时回退 IP。"""
    from app.core.security import get_current_user

    def _dep(request: Request, current_user: dict = Depends(get_current_user)) -> None:
        identifier = current_user.get("email") or _client_ip(request)
        check_and_bump(policy_name, identifier)

    return _dep
