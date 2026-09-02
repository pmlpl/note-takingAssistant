from app.utils.openai_compatible_url import normalize_openai_compatible_base_url


def test_normalize_strips_v1_models():
    assert normalize_openai_compatible_base_url("http://10.75.14.7:1234/v1/models") == "http://10.75.14.7:1234/v1"


def test_normalize_strips_trailing_slash_and_models():
    assert normalize_openai_compatible_base_url("http://host/v1/models/") == "http://host/v1"


def test_normalize_strips_chat_completions():
    assert normalize_openai_compatible_base_url("http://host/v1/chat/completions") == "http://host/v1"


def test_normalize_plain_v1_unchanged():
    assert normalize_openai_compatible_base_url("http://host:1234/v1") == "http://host:1234/v1"


def test_normalize_empty():
    assert normalize_openai_compatible_base_url("") is None
    assert normalize_openai_compatible_base_url("   ") is None
    assert normalize_openai_compatible_base_url(None) is None


def test_normalize_appends_v1_for_host_port_only():
    assert normalize_openai_compatible_base_url("http://10.16.54.177:1234") == "http://10.16.54.177:1234/v1"


def test_normalize_appends_v1_for_localhost_without_port_path():
    assert normalize_openai_compatible_base_url("http://127.0.0.1:1234/") == "http://127.0.0.1:1234/v1"
