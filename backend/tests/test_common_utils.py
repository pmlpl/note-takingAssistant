"""app.utils.common 工具函数测试"""

from app.utils.common import error_response, success_response


def test_success_response_default():
    result = success_response()
    assert result["code"] == 200
    assert result["message"] == "成功"
    assert result["data"] is None
    assert "timestamp" in result


def test_success_response_with_data_and_message():
    data = {"key": "value"}
    result = success_response(data=data, message="自定义消息")
    assert result["code"] == 200
    assert result["message"] == "自定义消息"
    assert result["data"] == data
    assert "timestamp" in result


def test_error_response_default():
    result = error_response()
    assert result["code"] == 500
    assert result["message"] == "失败"
    assert result["data"] is None
    assert "timestamp" in result


def test_error_response_custom():
    result = error_response(message="自定义错误", code=400)
    assert result["code"] == 400
    assert result["message"] == "自定义错误"
    assert result["data"] is None
    assert "timestamp" in result
