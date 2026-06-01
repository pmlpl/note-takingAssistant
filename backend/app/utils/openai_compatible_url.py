"""Normalize OpenAI-compatible API base URLs (LM Studio, vLLM, etc.)."""

from urllib.parse import urlparse, urlunparse

# SDK appends paths like /chat/completions; base must end at .../v1, not .../v1/models.
_BAD_BASE_SUFFIXES = ("/models", "/chat/completions")


def _ensure_v1_path_suffix(url: str) -> str:
    """Append /v1 when users only enter host:port (LM Studio 常见误填)."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    path = (parsed.path or "").rstrip("/")
    if path.lower() == "v1" or path.lower().endswith("/v1"):
        return url
    if not path:
        return urlunparse(parsed._replace(path="/v1"))
    return urlunparse(parsed._replace(path=f"{path}/v1"))


def normalize_openai_compatible_base_url(url: str | None) -> str | None:
    """
    Strip trailing slashes and mistaken suffixes (/models, /chat/completions).
    Users often paste .../v1/models from docs or the listing endpoint.
    If the URL has no /v1 segment (e.g. http://127.0.0.1:1234), append /v1 automatically.
    """
    if url is None:
        return None
    u = url.strip().rstrip("/")
    if not u:
        return None
    lu = u.lower()
    while True:
        matched = False
        for suf in _BAD_BASE_SUFFIXES:
            if lu.endswith(suf):
                u = u[: len(u) - len(suf)].rstrip("/")
                lu = u.lower()
                matched = True
                break
        if not matched:
            break
        if not u:
            return None
    return _ensure_v1_path_suffix(u)
