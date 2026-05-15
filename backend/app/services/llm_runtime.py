"""Resolve OpenAI-compatible base URL, model, and client for a user (BYOK + server defaults)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

from app.core.config import settings
from app.core.field_crypto import SecretCryptoError, decrypt_secret
from app.services.openai_client import make_async_openai_client
from app.utils.openai_compatible_url import normalize_openai_compatible_base_url

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from app.models.user import UserDB


def resolve_llm_base_url(db_user: "UserDB") -> str:
    u = (getattr(db_user, "llm_base_url", None) or "").strip()
    raw = u or (settings.LM_STUDIO_URL or "").strip()
    out = normalize_openai_compatible_base_url(raw) or raw.rstrip("/")
    return out


def resolve_llm_model(db_user: "UserDB") -> str:
    u = (getattr(db_user, "llm_model", None) or "").strip()
    return u or settings.LM_STUDIO_MODEL


def resolve_default_server_api_key() -> str:
    return (settings.OPENAI_API_KEY or "").strip() or "not-needed"


def openai_client_and_model_for_user(db_user: "UserDB") -> Tuple["AsyncOpenAI", str]:
    """
    Per-user BYOK: if llm_api_key_encrypted is set, decrypt and use with user's base URL/model fallbacks.
    Otherwise use server OPENAI_API_KEY (or not-needed) and server LM_STUDIO_* defaults for unset user fields.
    """
    base = resolve_llm_base_url(db_user)
    model = resolve_llm_model(db_user)
    enc = getattr(db_user, "llm_api_key_encrypted", None)
    if enc:
        try:
            plain = decrypt_secret(enc)
        except SecretCryptoError:
            raise
        api_key = (plain or "").strip() or "not-needed"
    else:
        api_key = resolve_default_server_api_key()
    client = make_async_openai_client(base, api_key)
    return client, model
