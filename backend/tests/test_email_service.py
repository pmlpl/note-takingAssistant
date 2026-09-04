"""app.services.email_service 测试

通过 mock settings 和 smtplib 来测试邮件发送功能，不依赖真实 SMTP 服务器。
"""

from unittest.mock import MagicMock, patch

from app.services import email_service


# ============== send_email ==============

def test_send_email_skipped_when_smtp_not_configured():
    with patch.object(email_service.settings, "SMTP_HOST", None), \
         patch.object(email_service.settings, "SMTP_USER", None), \
         patch.object(email_service.settings, "SMTP_PASSWORD", None):
        result = email_service.send_email("to@example.com", "主题", "<p>内容</p>")
        assert result is False


def test_send_email_skipped_when_partial_config():
    with patch.object(email_service.settings, "SMTP_HOST", "smtp.example.com"), \
         patch.object(email_service.settings, "SMTP_USER", None), \
         patch.object(email_service.settings, "SMTP_PASSWORD", "pwd"):
        result = email_service.send_email("to@example.com", "主题", "<p>内容</p>")
        assert result is False


def test_send_email_success_with_ssl():
    mock_server = MagicMock()
    with patch.object(email_service.settings, "SMTP_HOST", "smtp.example.com"), \
         patch.object(email_service.settings, "SMTP_PORT", 465), \
         patch.object(email_service.settings, "SMTP_USER", "user@example.com"), \
         patch.object(email_service.settings, "SMTP_PASSWORD", "password"), \
         patch.object(email_service.settings, "SMTP_FROM_NAME", "NoteMind"), \
         patch.object(email_service.smtplib, "SMTP_SSL", return_value=mock_server) as mock_ssl:
        result = email_service.send_email("to@example.com", "测试主题", "<p>测试内容</p>")
        assert result is True
        mock_ssl.assert_called_once_with("smtp.example.com", 465, timeout=30)
        mock_server.login.assert_called_once_with("user@example.com", "password")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()


def test_send_email_success_with_starttls():
    mock_server = MagicMock()
    with patch.object(email_service.settings, "SMTP_HOST", "smtp.example.com"), \
         patch.object(email_service.settings, "SMTP_PORT", 587), \
         patch.object(email_service.settings, "SMTP_USER", "user@example.com"), \
         patch.object(email_service.settings, "SMTP_PASSWORD", "password"), \
         patch.object(email_service.settings, "SMTP_FROM_NAME", "NoteMind"), \
         patch.object(email_service.smtplib, "SMTP", return_value=mock_server) as mock_smtp:
        result = email_service.send_email("to@example.com", "测试主题", "<p>测试内容</p>")
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()


def test_send_email_failure_exception():
    mock_server = MagicMock()
    mock_server.login.side_effect = Exception("Authentication failed")
    with patch.object(email_service.settings, "SMTP_HOST", "smtp.example.com"), \
         patch.object(email_service.settings, "SMTP_PORT", 465), \
         patch.object(email_service.settings, "SMTP_USER", "user@example.com"), \
         patch.object(email_service.settings, "SMTP_PASSWORD", "wrong"), \
         patch.object(email_service.settings, "SMTP_FROM_NAME", "NoteMind"), \
         patch.object(email_service.smtplib, "SMTP_SSL", return_value=mock_server):
        result = email_service.send_email("to@example.com", "主题", "<p>内容</p>")
        assert result is False


def test_send_email_sendmail_exception():
    mock_server = MagicMock()
    mock_server.sendmail.side_effect = Exception("SMTPDataError")
    with patch.object(email_service.settings, "SMTP_HOST", "smtp.example.com"), \
         patch.object(email_service.settings, "SMTP_PORT", 465), \
         patch.object(email_service.settings, "SMTP_USER", "user@example.com"), \
         patch.object(email_service.settings, "SMTP_PASSWORD", "pwd"), \
         patch.object(email_service.settings, "SMTP_FROM_NAME", "NoteMind"), \
         patch.object(email_service.smtplib, "SMTP_SSL", return_value=mock_server):
        result = email_service.send_email("to@example.com", "主题", "<p>内容</p>")
        assert result is False


# ============== send_verification_code_email ==============

def test_send_verification_code_email_success():
    with patch.object(email_service, "send_email", return_value=True) as mock_send:
        result = email_service.send_verification_code_email("user@example.com", "123456")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert args[0][0] == "user@example.com"
        assert "验证码" in args[0][1]
        assert "123456" in args[0][2]


def test_send_verification_code_email_contains_code():
    captured = {}
    def fake_send(to, subject, html):
        captured["html"] = html
        return True
    with patch.object(email_service, "send_email", side_effect=fake_send):
        email_service.send_verification_code_email("test@example.com", "ABCDEF")
        assert "ABCDEF" in captured["html"]
        assert "NoteMind" in captured["html"]


def test_send_verification_code_email_failure():
    with patch.object(email_service, "send_email", return_value=False):
        result = email_service.send_verification_code_email("user@example.com", "123456")
        assert result is False
