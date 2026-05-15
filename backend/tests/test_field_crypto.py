from cryptography.fernet import Fernet

from app.core.field_crypto import api_key_last_four, decrypt_secret, encrypt_secret


def test_encrypt_decrypt_roundtrip():
    raw = "sk-test-secret-key-12345"
    enc = encrypt_secret(raw)
    assert enc != raw
    assert decrypt_secret(enc) == raw


def test_api_key_last_four():
    assert api_key_last_four("sk-verylong") == "long"
    assert api_key_last_four("x") == "x"


def test_encrypt_decrypt_uses_derived_when_encryption_key_empty(monkeypatch):
    from app.core import field_crypto

    monkeypatch.setattr(field_crypto.settings, "ENCRYPTION_KEY", "")
    monkeypatch.setattr(field_crypto.settings, "SECRET_KEY", "fixed-secret-for-test")
    raw = "sk-byok-derived-path"
    enc = field_crypto.encrypt_secret(raw)
    assert enc != raw
    assert field_crypto.decrypt_secret(enc) == raw


def test_decrypt_falls_back_to_derived_when_explicit_key_wrong(monkeypatch):
    """Admin adds ENCRYPTION_KEY later; old ciphertext was encrypted with derived key."""
    from app.core import field_crypto

    monkeypatch.setattr(field_crypto.settings, "ENCRYPTION_KEY", "")
    monkeypatch.setattr(field_crypto.settings, "SECRET_KEY", "same-secret")
    raw = "sk-migration"
    enc = field_crypto.encrypt_secret(raw)
    monkeypatch.setattr(field_crypto.settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert field_crypto.decrypt_secret(enc) == raw
