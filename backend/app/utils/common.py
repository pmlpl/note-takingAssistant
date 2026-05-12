from datetime import datetime
from typing import Any, Dict


def success_response(data: Any = None, message: str = "成功") -> Dict:
    """成功响应格式"""
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


def error_response(message: str = "失败", code: int = 500) -> Dict:
    """错误响应格式"""
    return {
        "code": code,
        "message": message,
        "data": None,
        "timestamp": datetime.now().isoformat()
    }
