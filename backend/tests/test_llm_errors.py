from app.utils.llm_errors import format_llm_error


def test_connection_error_hint():
    msg = format_llm_error("AI对话", Exception("Connection error."))
    assert "无法连接推理服务" in msg
    assert "LM Studio" in msg


def test_auth_error_hint():
    msg = format_llm_error("AI对话", Exception("invalid_api_key"))
    assert "鉴权" in msg
    assert "OPENAI_API_KEY" in msg
