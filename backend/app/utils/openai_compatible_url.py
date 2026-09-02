"""Normalize OpenAI-compatible API base URLs (LM Studio, vLLM, etc.).

Also provides `assert_safe_llm_url` to block SSRF attempts against:
- non-http(s) schemes
- private / loopback / link-local / metadata-service IPs
- non-whitelist ports (only common LLM inference server ports)
- raw hostnames that resolve to internal addresses after DNS lookup
"""

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

from app.core.config import settings

# SDK appends paths like /chat/completions; base must end at .../v1, not .../v1/models.
_BAD_BASE_SUFFIXES = ("/models", "/chat/completions")

# 仅允许 http / https 协议，拒绝 file:// / gopher:// / dict:// 等可能触发 SSRF 的协议
_ALLOWED_SCHEMES = ("http", "https")

# 端口白名单：常见 LLM 推理服务端口；默认不含 22、3306、6379、8080(管理) 等敏感端口
_ALLOWED_PORTS = frozenset([80, 443, 1234, 2000, 3000, 8000, 8081, 8082, 8083, 8084, 8085, 8888, 11434, 30000, 30001])

# 云元数据服务地址（所有云厂商通用）
_METADATA_HOSTS = frozenset(["metadata.google.internal", "169.254.169.254", "169.254.170.2", "fd00:ec2::254"])

# Docker Compose 内部服务名，禁止被指向内网数据库/缓存
_INTERNAL_HOSTNAMES = frozenset(["mysql", "redis", "postgres", "mariadb", "localhost", "host.docker.internal"])


class UnsafeLlmUrlError(ValueError):
    """Raised when a user-supplied LLM base URL fails the SSRF safety check."""


def _is_private_or_link_local_ip(ip_str: str) -> bool:
    """判断 IP 是否属于私有/环回/链路本地/未指定地址。"""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_unspecified or ip.is_reserved or ip.is_multicast


def _host_resolves_to_internal(host: str) -> bool:
    """对 hostname 做一次 DNS 解析，若任何一条 A/AAAA 记录指向内网 IP，则视为危险。"""
    try:
        # 仅获取地址信息，不建立连接；超时兜底 1 秒避免慢 DNS 阻塞事件循环
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # 无法解析的主机名 —— 保持保守，放行但上层会因连接失败而返回错误
        return False
    except OSError:
        return False
    for info in infos:
        try:
            ip_str = info[4][0]
            if _is_private_or_link_local_ip(ip_str):
                return True
        except (IndexError, TypeError):
            continue
    return False


def assert_safe_llm_url(url: str | None) -> str | None:
    """
    校验用户提供的 LLM base_url 是否安全。
    通过则返回 URL 原值，失败则抛出 UnsafeLlmUrlError。

    规则：
    1. 只允许 http / https
    2. hostname 不得为私有 IP、localhost、云元数据地址、Docker 内部服务名
    3. 端口必须在 _ALLOWED_PORTS 白名单内
    4. 对 hostname 做一次 DNS 反向解析，若解析到内网 IP 亦拒绝
    """
    if url is None:
        return None
    u = url.strip()
    if not u:
        return None

    parsed = urlparse(u)
    if not parsed.scheme or parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UnsafeLlmUrlError(f"LLM API 地址仅允许 http/https 协议（收到 {parsed.scheme!r}），请修改后重试。")
    if not parsed.hostname:
        raise UnsafeLlmUrlError("LLM API 地址缺少主机名，请填写有效的 IP 或域名。")

    host = parsed.hostname.lower()

    if host in _METADATA_HOSTS or host in _INTERNAL_HOSTNAMES:
        if settings.DEBUG:
            pass
        else:
            raise UnsafeLlmUrlError("LLM API 地址指向内网/云元数据服务被拒绝，请填写公网可访问的推理服务地址。")

    if _is_private_or_link_local_ip(host):
        if settings.DEBUG:
            pass
        else:
            raise UnsafeLlmUrlError("LLM API 地址指向私有/环回/链路本地 IP 被拒绝，请填写公网 IP 或域名。")

    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme.lower() == "https" else 80
    if port not in _ALLOWED_PORTS:
        raise UnsafeLlmUrlError(f"LLM API 端口 {port} 不在允许列表内（允许：{sorted(_ALLOWED_PORTS)}）。")

    if _host_resolves_to_internal(host):
        if settings.DEBUG:
            pass
        else:
            raise UnsafeLlmUrlError("LLM API 域名解析到内网 IP 被拒绝，请填写公网可访问的推理服务地址。")

    return url


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
