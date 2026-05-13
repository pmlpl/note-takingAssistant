"""Shared AsyncOpenAI client — LLM I/O runs on the event loop without blocking workers."""
import httpx
from openai import AsyncOpenAI

from app.core.config import settings

# 本地 LM Studio 常见「冷启动 + 首 token」远超默认 5min 读超时，单独放宽 read
_llm_http_timeout = httpx.Timeout(
    connect=60.0,
    read=settings.LLM_HTTP_READ_TIMEOUT_SECONDS,
    write=120.0,
    pool=60.0,
)

async_openai_client = AsyncOpenAI(
    base_url=settings.LM_STUDIO_URL,
    api_key="not-needed",
    timeout=_llm_http_timeout,
)
