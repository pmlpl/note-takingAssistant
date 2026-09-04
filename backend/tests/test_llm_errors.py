"""app.utils.llm_errors 测试

覆盖 format_llm_error 对各种异常类型的格式化。
"""

from app.utils.llm_errors import format_llm_error


# ============== 连接错误 ==============

def test_connection_error():
    exc = Exception("Connection error: failed to connect to host")
    result = format_llm_error("AI对话", exc)
    assert "AI对话失败" in result
    assert "无法连接推理服务" in result
    assert "LM Studio" in result


def test_connection_refused():
    exc = Exception("Connection refused")
    result = format_llm_error("AI生成笔记", exc)
    assert "无法连接推理服务" in result


def test_failed_to_connect():
    exc = Exception("Failed to connect to server")
    result = format_llm_error("AI翻译", exc)
    assert "无法连接推理服务" in result


def test_timed_out():
    exc = Exception("Request timed out")
    result = format_llm_error("AI对话", exc)
    assert "无法连接推理服务" in result


def test_timeout():
    exc = Exception("Read timeout")
    result = format_llm_error("AI分析", exc)
    assert "无法连接推理服务" in result


def test_name_or_service_not_known():
    exc = Exception("Name or service not known")
    result = format_llm_error("AI对话", exc)
    assert "无法连接推理服务" in result


def test_nodename_nor_servname():
    exc = Exception("nodename nor servname provided, or not known")
    result = format_llm_error("AI对话", exc)
    assert "无法连接推理服务" in result


def test_connect_error():
    exc = Exception("Connect error: 127.0.0.1:1234")
    result = format_llm_error("AI对话", exc)
    assert "无法连接推理服务" in result


# ============== 鉴权错误 ==============

def test_invalid_api_key():
    exc = Exception("invalid_api_key: The key is invalid")
    result = format_llm_error("AI对话", exc)
    assert "API 鉴权未通过" in result
    assert "OPENAI_API_KEY" in result


def test_invalid_api_key_spaces():
    exc = Exception("Invalid API key provided")
    result = format_llm_error("AI生成笔记", exc)
    assert "API 鉴权未通过" in result


def test_authentication_error():
    exc = Exception("Authentication failed")
    result = format_llm_error("AI对话", exc)
    assert "API 鉴权未通过" in result


def test_unauthorized():
    exc = Exception("Unauthorized: 401")
    result = format_llm_error("AI翻译", exc)
    assert "API 鉴权未通过" in result


def test_401_status():
    exc = Exception("HTTP 401: Unauthorized")
    result = format_llm_error("AI对话", exc)
    assert "API 鉴权未通过" in result


def test_api_token_required():
    exc = Exception("API token is required")
    result = format_llm_error("AI分析", exc)
    assert "API 鉴权未通过" in result


def test_incorrect_api_key():
    exc = Exception("Incorrect API key provided")
    result = format_llm_error("AI对话", exc)
    assert "API 鉴权未通过" in result


# ============== 模型不存在错误 ==============

def test_model_not_found():
    exc = Exception("Model 'gpt-4' not found")
    result = format_llm_error("AI对话", exc)
    assert "模型不存在" in result
    assert "LM_STUDIO_MODEL" in result


def test_model_does_not_exist():
    exc = Exception("The model does not exist")
    result = format_llm_error("AI生成笔记", exc)
    assert "模型不存在" in result


def test_unknown_model():
    exc = Exception("Unknown model: llama-3")
    result = format_llm_error("AI翻译", exc)
    assert "模型不存在" in result


# ============== 通用错误 ==============

def test_generic_error_with_message():
    exc = Exception("Something went wrong in the API")
    result = format_llm_error("AI对话", exc)
    assert "AI对话失败" in result
    assert "Something went wrong" in result


def test_generic_error_empty_message():
    exc = Exception("")
    result = format_llm_error("AI对话", exc)
    assert "AI对话失败" in result
    assert "请稍后重试" in result


def test_generic_error_whitespace_message():
    exc = Exception("   ")
    result = format_llm_error("AI分析", exc)
    assert "请稍后重试" in result


def test_action_name_in_all_errors():
    for exc_msg in ["Connection error", "invalid_api_key", "Model not found", "Random error"]:
        result = format_llm_error("自定义动作", Exception(exc_msg))
        assert "自定义动作失败" in result


def test_rate_limit_error_fallback():
    # 速率限制错误不属于特定类型，走通用分支
    exc = Exception("Rate limit exceeded: 429")
    result = format_llm_error("AI对话", exc)
    assert "AI对话失败" in result
    assert "Rate limit exceeded" in result


def test_server_error_fallback():
    exc = Exception("Internal server error: 500")
    result = format_llm_error("AI对话", exc)
    assert "AI对话失败" in result
    assert "Internal server error" in result


def test_case_insensitive_matching():
    exc = Exception("CONNECTION ERROR")
    result = format_llm_error("AI对话", exc)
    assert "无法连接推理服务" in result

    exc2 = Exception("Invalid_Api_Key")
    result2 = format_llm_error("AI对话", exc2)
    assert "API 鉴权未通过" in result2
