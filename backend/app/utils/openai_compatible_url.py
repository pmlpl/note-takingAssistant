"""Normalize OpenAI-compatible API base URLs (LM Studio, vLLM, etc.)."""

# SDK appends paths like /chat/completions; base must end at .../v1, not .../v1/models.
_BAD_BASE_SUFFIXES = ("/models", "/chat/completions")


def normalize_openai_compatible_base_url(url: str | None) -> str | None:
    """
    Strip trailing slashes and mistaken suffixes (/models, /chat/completions).
    Users often paste .../v1/models from docs or the listing endpoint.
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
    return u
