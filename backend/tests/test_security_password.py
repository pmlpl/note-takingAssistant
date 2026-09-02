"""不启动 HTTP 服务、不连数据库的轻量回归测试。"""

from app.core.security import get_password_hash, verify_password


def test_password_hash_roundtrip():
    h = get_password_hash("mySecret1!")
    assert verify_password("mySecret1!", h)
    assert not verify_password("wrong", h)
