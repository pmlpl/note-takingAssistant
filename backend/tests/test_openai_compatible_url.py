"""app.utils.openai_compatible_url 测试

覆盖 URL 规范化和 SSRF 安全校验。
"""

from unittest.mock import patch

import pytest

from app.utils.openai_compatible_url import (
    UnsafeLlmUrlError,
    _ensure_v1_path_suffix,
    _is_private_or_link_local_ip,
    assert_safe_llm_url,
    normalize_openai_compatible_base_url,
)


# ============== _is_private_or_link_local_ip ==============

def test_is_private_ip_10():
    assert _is_private_or_link_local_ip("10.0.0.1") is True


def test_is_private_ip_172():
    assert _is_private_or_link_local_ip("172.16.0.1") is True


def test_is_private_ip_192():
    assert _is_private_or_link_local_ip("192.168.1.1") is True


def test_is_loopback_ip():
    assert _is_private_or_link_local_ip("127.0.0.1") is True


def test_is_link_local_ip():
    assert _is_private_or_link_local_ip("169.254.1.1") is True


def test_is_unspecified_ip():
    assert _is_private_or_link_local_ip("0.0.0.0") is True


def test_is_public_ip():
    assert _is_private_or_link_local_ip("8.8.8.8") is False
    assert _is_private_or_link_local_ip("1.1.1.1") is False


def test_is_invalid_ip():
    assert _is_private_or_link_local_ip("not-an-ip") is False
    assert _is_private_or_link_local_ip("999.999.999.999") is False


def test_is_ipv6_loopback():
    assert _is_private_or_link_local_ip("::1") is True


def test_is_ipv6_private():
    assert _is_private_or_link_local_ip("fc00::1") is True


def test_is_ipv6_public():
    assert _is_private_or_link_local_ip("2001:4860:4860::8888") is False


def test_is_multicast_ip():
    assert _is_private_or_link_local_ip("224.0.0.1") is True


def test_is_reserved_ip():
    assert _is_private_or_link_local_ip("240.0.0.1") is True


# ============== _ensure_v1_path_suffix ==============

def test_ensure_v1_no_path():
    result = _ensure_v1_path_suffix("http://127.0.0.1:1234")
    assert result == "http://127.0.0.1:1234/v1"


def test_ensure_v1_already_has_v1():
    result = _ensure_v1_path_suffix("http://127.0.0.1:1234/v1")
    assert result == "http://127.0.0.1:1234/v1"


def test_ensure_v1_path_ends_with_v1():
    result = _ensure_v1_path_suffix("http://host:8000/api/v1")
    assert result == "http://host:8000/api/v1"


def test_ensure_v1_other_path():
    result = _ensure_v1_path_suffix("http://host:8000/api")
    assert result == "http://host:8000/api/v1"


def test_ensure_v1_invalid_url():
    result = _ensure_v1_path_suffix("not-a-url")
    assert result == "not-a-url"


def test_ensure_v1_empty_scheme():
    result = _ensure_v1_path_suffix("://host")
    assert result == "://host"


# ============== normalize_openai_compatible_base_url ==============

def test_normalize_none():
    assert normalize_openai_compatible_base_url(None) is None


def test_normalize_empty():
    assert normalize_openai_compatible_base_url("") is None
    assert normalize_openai_compatible_base_url("   ") is None


def test_normalize_strip_trailing_slash():
    result = normalize_openai_compatible_base_url("http://host:1234/v1/")
    assert result == "http://host:1234/v1"


def test_normalize_strip_multiple_slashes():
    result = normalize_openai_compatible_base_url("http://host:1234/v1///")
    assert result == "http://host:1234/v1"


def test_normalize_remove_models_suffix():
    result = normalize_openai_compatible_base_url("http://host:1234/v1/models")
    assert result == "http://host:1234/v1"


def test_normalize_remove_chat_completions_suffix():
    result = normalize_openai_compatible_base_url("http://host:1234/v1/chat/completions")
    assert result == "http://host:1234/v1"


def test_normalize_remove_models_then_add_v1():
    result = normalize_openai_compatible_base_url("http://host:1234/models")
    assert result == "http://host:1234/v1"


def test_normalize_no_v1_adds_v1():
    result = normalize_openai_compatible_base_url("http://host:1234")
    assert result == "http://host:1234/v1"


def test_normalize_with_path_no_v1():
    result = normalize_openai_compatible_base_url("http://host:8000/api")
    assert result == "http://host:8000/api/v1"


def test_normalize_whitespace():
    result = normalize_openai_compatible_base_url("  http://host:1234/v1  ")
    assert result == "http://host:1234/v1"


def test_normalize_only_suffix_returns_none():
    # URL 去掉后缀后为空
    result = normalize_openai_compatible_base_url("/models")
    assert result is None


def test_normalize_https():
    result = normalize_openai_compatible_base_url("https://api.example.com")
    assert result == "https://api.example.com/v1"


# ============== assert_safe_llm_url ==============

def test_assert_safe_none():
    assert assert_safe_llm_url(None) is None


def test_assert_safe_empty():
    assert assert_safe_llm_url("") is None
    assert assert_safe_llm_url("   ") is None


def test_assert_safe_public_http():
    result = assert_safe_llm_url("http://api.example.com/v1")
    assert result == "http://api.example.com/v1"


def test_assert_safe_public_https():
    result = assert_safe_llm_url("https://api.openai.com/v1")
    assert result == "https://api.openai.com/v1"


def test_assert_safe_lm_studio_local():
    # LM Studio 本地地址，DEBUG 模式下放行
    with patch("app.utils.openai_compatible_url.settings.DEBUG", True):
        result = assert_safe_llm_url("http://127.0.0.1:1234/v1")
        assert result == "http://127.0.0.1:1234/v1"


def test_assert_unsafe_file_scheme():
    with pytest.raises(UnsafeLlmUrlError, match="仅允许 http/https"):
        assert_safe_llm_url("file:///etc/passwd")


def test_assert_unsafe_gopher_scheme():
    with pytest.raises(UnsafeLlmUrlError, match="仅允许 http/https"):
        assert_safe_llm_url("gopher://host:1234")


def test_assert_unsafe_no_scheme():
    with pytest.raises(UnsafeLlmUrlError, match="仅允许 http/https"):
        assert_safe_llm_url("host:1234/v1")


def test_assert_unsafe_no_hostname():
    with pytest.raises(UnsafeLlmUrlError, match="缺少主机名"):
        assert_safe_llm_url("http:///v1")


def test_assert_unsafe_localhost_production():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", False):
        with pytest.raises(UnsafeLlmUrlError, match="内网/云元数据"):
            assert_safe_llm_url("http://localhost:1234/v1")


def test_assert_unsafe_private_ip_production():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", False):
        with pytest.raises(UnsafeLlmUrlError, match="私有/环回/链路本地"):
            assert_safe_llm_url("http://192.168.1.1:1234/v1")


def test_assert_unsafe_metadata_host():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", False):
        with pytest.raises(UnsafeLlmUrlError, match="内网/云元数据"):
            assert_safe_llm_url("http://169.254.169.254/latest/meta-data")


def test_assert_unsafe_docker_internal():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", False):
        with pytest.raises(UnsafeLlmUrlError, match="内网/云元数据"):
            assert_safe_llm_url("http://redis:6379/v1")


def test_assert_unsafe_port_mysql():
    # 端口 3306 不在白名单
    with patch("app.utils.openai_compatible_url.settings.DEBUG", True):
        with pytest.raises(UnsafeLlmUrlError, match="端口.*不在允许列表"):
            assert_safe_llm_url("http://127.0.0.1:3306/v1")


def test_assert_unsafe_port_redis():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", True):
        with pytest.raises(UnsafeLlmUrlError, match="端口.*不在允许列表"):
            assert_safe_llm_url("http://127.0.0.1:6379/v1")


def test_assert_safe_port_1234():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", True):
        result = assert_safe_llm_url("http://127.0.0.1:1234/v1")
        assert result is not None


def test_assert_safe_port_8000():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", True):
        result = assert_safe_llm_url("http://127.0.0.1:8000/v1")
        assert result is not None


def test_assert_safe_port_11434():
    with patch("app.utils.openai_compatible_url.settings.DEBUG", True):
        result = assert_safe_llm_url("http://127.0.0.1:11434/v1")
        assert result is not None


def test_assert_safe_default_port_http():
    # http 默认 80 端口
    result = assert_safe_llm_url("http://api.example.com/v1")
    assert result is not None


def test_assert_safe_default_port_https():
    # https 默认 443 端口
    result = assert_safe_llm_url("https://api.example.com/v1")
    assert result is not None


def test_assert_unsafe_dns_resolves_to_internal():
    # 模拟 DNS 解析到内网 IP
    with patch("app.utils.openai_compatible_url._host_resolves_to_internal", return_value=True), \
         patch("app.utils.openai_compatible_url.settings.DEBUG", False):
        with pytest.raises(UnsafeLlmUrlError, match="域名解析到内网 IP"):
            assert_safe_llm_url("http://evil.example.com/v1")


def test_assert_safe_dns_resolves_to_public():
    with patch("app.utils.openai_compatible_url._host_resolves_to_internal", return_value=False):
        result = assert_safe_llm_url("http://safe.example.com/v1")
        assert result is not None


# ============== _host_resolves_to_internal ==============

def test_host_resolves_gaierror():
    import socket
    with patch("socket.getaddrinfo", side_effect=socket.gaierror("Name not resolved")):
        from app.utils.openai_compatible_url import _host_resolves_to_internal
        assert _host_resolves_to_internal("nonexistent.example.com") is False


def test_host_resolves_oserror():
    with patch("socket.getaddrinfo", side_effect=OSError("OS error")):
        from app.utils.openai_compatible_url import _host_resolves_to_internal
        assert _host_resolves_to_internal("error.example.com") is False


def test_host_resolves_to_public_ip():
    # 模拟解析到公网 IP
    infos = [(2, 1, 6, "", ("8.8.8.8", 0))]
    import socket
    with patch("socket.getaddrinfo", return_value=infos):
        from app.utils.openai_compatible_url import _host_resolves_to_internal
        assert _host_resolves_to_internal("public.example.com") is False


def test_host_resolves_to_private_ip():
    import socket
    infos = [(2, 1, 6, "", ("192.168.1.1", 0))]
    with patch("socket.getaddrinfo", return_value=infos):
        from app.utils.openai_compatible_url import _host_resolves_to_internal
        assert _host_resolves_to_internal("internal.example.com") is True
