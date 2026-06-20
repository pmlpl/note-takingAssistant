"""Shared httpx client and helpers for AsyncOpenAI — per-request clients use user or server defaults.

SSRF 防御：在构造用户自定义 base_url 的客户端前，会调用 `assert_safe_llm_url` 拦截私有 IP / 元数据服务 / 非白名单端口。
"""
import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.openai_compatible_url import (
    normalize_openai_compatible_base_url,
    assert_safe_llm_url,
    UnsafeLlmUrlError,
)

# 本地 LM Studio 常见「冷启动 + 首 token」远超默认 5min 读超时，单独放宽 read
_llm_http_timeout = httpx.Timeout(
    connect=60.0,
    read=settings.LLM_HTTP_READ_TIMEOUT_SECONDS,
    write=120.0,
    pool=60.0,
)

# 独立 AsyncClient：trust_env=False 时忽略 HTTP_PROXY，避免本机 LM Studio 被导向 Privoxy 等代理并报错
llm_shared_http_client = httpx.AsyncClient(
    timeout=_llm_http_timeout,
    trust_env=settings.LLM_HTTP_TRUST_ENV,
)

_default_llm_base = (
    normalize_openai_compatible_base_url((settings.LM_STUDIO_URL or "").strip())
    or (settings.LM_STUDIO_URL or "").strip().rstrip("/")
)

# 兼容旧导入：无用户上下文时的服务端默认客户端
async_openai_client = AsyncOpenAI(
    base_url=_default_llm_base,
    api_key=(settings.OPENAI_API_KEY or "").strip() or "not-needed",
    http_client=llm_shared_http_client,
)


def make_async_openai_client(base_url: str, api_key: str) -> AsyncOpenAI:
    """Build an AsyncOpenAI instance sharing the process-wide httpx pool/timeouts.

    额外执行 SSRF 安全校验：拒绝私有 IP / 云元数据 / 非白名单端口；若 URL 不安全则抛 UnsafeLlmUrlError。
    """
    key = (api_key or "").strip() or "not-needed"
    raw = (base_url or "").strip()
    if raw:
        assert_safe_llm_url(raw)  # SSRF 安全拦截
    base = normalize_openai_compatible_base_url(raw) or raw.rstrip("/")
    return AsyncOpenAI(
        base_url=base,
        api_key=key,
        http_client=llm_shared_http_client,
    )
