"""Encrypt/decrypt sensitive per-user fields (e.g. LLM API keys). Never log plaintext."""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class SecretCryptoError(Exception):
    """Raised when encryption is misconfigured or ciphertext is invalid."""


# Stable pepper so derived key is not raw SECRET_KEY alone.
_DERIVE_CONTEXT = b"note-takingAssistant/user-llm-api-key/fernet-v1\x00"


def _derive_fernet_key_from_secret(secret: str) -> bytes:
    """32-byte Fernet key material encoded as urlsafe base64 (ASCII bytes for Fernet())."""
    digest = hashlib.sha256(_DERIVE_CONTEXT + secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet_explicit() -> Fernet | None:
    raw = (settings.ENCRYPTION_KEY or "").strip()
    if not raw:
        return None
    return Fernet(raw.encode("utf-8"))


def _fernet_derived() -> Fernet | None:
    sk = (settings.SECRET_KEY or "").strip()
    if not sk:
        return None
    return Fernet(_derive_fernet_key_from_secret(sk))


def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt UTF-8 text.
    Prefer ENCRYPTION_KEY when set; otherwise derive from SECRET_KEY so BYOK works without admin setup.
    """
    f = _fernet_explicit() or _fernet_derived()
    if not f:
        raise SecretCryptoError(
            "无法加密密钥：请在服务端配置 SECRET_KEY（或任选其一 ENCRYPTION_KEY）。"
        )
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(ciphertext: str) -> str:
    """
    Decrypt Fernet token to UTF-8 string.
    Try explicit ENCRYPTION_KEY first (existing installs), then SECRET_KEY-derived key.
    """
    tokens = ciphertext.encode("ascii")
    tried_explicit = False
    f_explicit = _fernet_explicit()
    if f_explicit:
        tried_explicit = True
        try:
            return f_explicit.decrypt(tokens).decode("utf-8")
        except InvalidToken:
            pass

    f_derived = _fernet_derived()
    if not f_derived:
        if tried_explicit:
            raise SecretCryptoError("Could not decrypt stored secret") from None
        raise SecretCryptoError(
            "无法解密密钥：请配置 SECRET_KEY 或与加密时一致的 ENCRYPTION_KEY。"
        ) from None

    try:
        return f_derived.decrypt(tokens).decode("utf-8")
    except InvalidToken as e:
        raise SecretCryptoError("Could not decrypt stored secret") from e


def api_key_last_four(plaintext: str) -> str:
    s = plaintext.strip()
    if len(s) <= 4:
        return s
    return s[-4:]


def mask_api_key_hint(last_four: str | None) -> str | None:
    if not last_four:
        return None
    return f"****{last_four}"
