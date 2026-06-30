import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from app.core.config import settings
from app.core.logger import app_logger as logger


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP 未配置，跳过发送邮件")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_USER))
        msg["To"] = to_email
        msg["Subject"] = subject

        part = MIMEText(html_content, "html", "utf-8")
        msg.attach(part)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        server.quit()

        logger.info(f"邮件发送成功: to={to_email}, subject={subject}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def send_verification_code_email(to_email: str, code: str) -> bool:
    html = f"""
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h2 style="color: white; margin: 0;">NoteMind</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">邮箱验证码</p>
        </div>
        <div style="background: #ffffff; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <p style="color: #333; font-size: 16px; margin: 0 0 20px 0;">您好，</p>
            <p style="color: #555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                您正在使用邮箱验证码登录/注册NoteMind。<br>
                验证码有效期为 5 分钟，请勿泄露给他人。
            </p>
            <div style="background: #f7f8fc; padding: 25px; border-radius: 8px; text-align: center;">
                <span style="font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 8px;">{code}</span>
            </div>
            <p style="color: #999; font-size: 13px; margin: 20px 0 0 0;">
                如果这不是您本人的操作，请忽略此邮件。
            </p>
        </div>
        <div style="text-align: center; color: #aaa; font-size: 12px; margin-top: 20px;">
            © 2026 NoteMind
        </div>
    </div>
    """
    return send_email(to_email, "NoteMind - 邮箱验证码", html)
