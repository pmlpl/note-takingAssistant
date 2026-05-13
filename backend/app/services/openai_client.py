"""Shared AsyncOpenAI client — LLM I/O runs on the event loop without blocking workers."""
from openai import AsyncOpenAI
from app.core.config import settings

async_openai_client = AsyncOpenAI(
    base_url=settings.LM_STUDIO_URL,
    api_key="not-needed",
)
