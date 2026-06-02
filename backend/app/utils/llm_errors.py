"""将 OpenAI SDK / httpx 异常转为面向用户的中文提示。"""
from __future__ import annotations


def format_llm_error(action: str, exc: Exception) -> str:
    """
    :param action: 业务动作名，如「AI对话」「AI生成笔记」
    """
    raw = str(exc).strip()
    lower = raw.lower()

    if any(
        token in lower
        for token in (
            "connection error",
            "connect error",
            "connection refused",
            "failed to connect",
            "name or service not known",
            "nodename nor servname",
            "timed out",
            "timeout",
        )
    ):
        return (
            f"{action}失败：无法连接推理服务。请确认 LM Studio（或其它兼容端）已启动 Local Server，"
            f"且 LM_STUDIO_URL 端口正确（一般为 http://127.0.0.1:1234/v1）。"
        )

    if any(
        token in lower
        for token in (
            "invalid_api_key",
            "invalid api key",
            "authentication",
            "unauthorized",
            "401",
            "api token is required",
            "incorrect api key",
        )
    ):
        return (
            f"{action}失败：API 鉴权未通过。请在 backend/.env 配置 OPENAI_API_KEY（LM Studio Token），"
            f"或在个人中心填写 API Key。"
        )

    if "model" in lower and any(t in lower for t in ("not found", "does not exist", "unknown")):
        return f"{action}失败：模型不存在。请检查 LM_STUDIO_MODEL 或个人中心中的模型名称是否与推理端一致。"

    if raw:
        return f"{action}失败：{raw}"
    return f"{action}失败，请稍后重试。"
