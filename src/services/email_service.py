"""
Email Service
Task 5.2: メール送信とSMTP連携機能
"""
import logging
import os
import re
import smtplib
import html
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from ..utils.result import Result

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Email service error"""
    pass


class EmailService:
    """Email service for SMTP integration and email sending"""

    def __init__(self):
        """Initialize email service with SMTP configuration"""
        self._validate_smtp_config()
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'DxeeWorld Authentication')

        # Rate limiting storage (in production, use Redis or similar)
        self._rate_limit_cache = {}
        self.rate_limit_per_minute = int(os.getenv('EMAIL_RATE_LIMIT', '5'))

        # SMTP client will be initialized per send
        self.smtp_client = None

    def _validate_smtp_config(self):
        """Validate SMTP configuration"""
        required_configs = ['SMTP_HOST', 'SMTP_USERNAME', 'SMTP_PASSWORD']
        missing_configs = []

        for config in required_configs:
            if not os.getenv(config):
                missing_configs.append(config)

        if missing_configs:
            raise ValueError(f"SMTP configuration missing: {missing_configs}")

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _check_rate_limit(self, email: str) -> bool:
        """Check if email sending is rate limited"""
        now = datetime.now(timezone.utc)
        minute_key = f"{email}:{now.strftime('%Y%m%d%H%M')}"

        # Clean old entries
        old_keys = [k for k in self._rate_limit_cache.keys()
                   if (now - datetime.strptime(k.split(':')[1], '%Y%m%d%H%M').replace(tzinfo=timezone.utc)).seconds > 60]
        for old_key in old_keys:
            self._rate_limit_cache.pop(old_key, None)

        # Check current minute count
        count = self._rate_limit_cache.get(minute_key, 0)
        if count >= self.rate_limit_per_minute:
            return False

        # Increment counter
        self._rate_limit_cache[minute_key] = count + 1
        return True

    def _mask_email_for_logging(self, email: str) -> str:
        """Mask email for secure logging"""
        if '@' in email:
            local, domain = email.split('@', 1)
            masked_local = local[:2] + '***' if len(local) > 2 else '***'
            return f"{masked_local}@{domain}"
        return '***'

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content to prevent injection"""
        return html.escape(content)

    async def _create_verification_message(self, recipient: str, redirect_url: str) -> MIMEMultipart:
        """Create verification email message"""
        message = MIMEMultipart('alternative')
        message['From'] = f"{self.from_name} <{self.from_email}>"
        message['To'] = recipient
        message['Subject'] = Header("メールアドレスの確認", 'utf-8')

        # Sanitize redirect URL
        safe_redirect_url = self._sanitize_content(redirect_url)

        # Text version
        text_content = f"""
DxeeWorldにご登録いただき、ありがとうございます。

メールアドレスを確認するため、下記のリンクをクリックしてください：
{safe_redirect_url}

このリンクは1時間有効です。

※このメールに心当たりがない場合は、削除してください。

DxeeWorldチーム
"""

        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>メールアドレスの確認</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>DxeeWorldにご登録いただき、ありがとうございます</h2>

        <p>メールアドレスを確認するため、下記のボタンをクリックしてください：</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{safe_redirect_url}"
               style="background-color: #007bff; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                メールアドレスを確認
            </a>
        </div>

        <p>または、以下のURLをブラウザにコピーしてアクセスしてください：</p>
        <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 3px;">
            {safe_redirect_url}
        </p>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="font-size: 12px; color: #666;">
            このリンクは1時間有効です。<br>
            このメールに心当たりがない場合は、削除してください。<br><br>
            DxeeWorldチーム
        </p>
    </div>
</body>
</html>
"""

        # Attach both versions
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')

        message.attach(text_part)
        message.attach(html_part)

        return message

    async def _create_login_code_message(self, recipient: str, login_code: str) -> MIMEMultipart:
        """Create login code email message"""
        message = MIMEMultipart('alternative')
        message['From'] = f"{self.from_name} <{self.from_email}>"
        message['To'] = recipient
        message['Subject'] = Header("ログイン認証コード", 'utf-8')

        # Sanitize login code
        safe_login_code = self._sanitize_content(login_code)

        # Text version
        text_content = f"""
DxeeWorldログイン認証コード

認証コード: {safe_login_code}

このコードをログイン画面で入力してください。
コードの有効期限は5分間です。

※このメールに心当たりがない場合は、削除してください。

DxeeWorldチーム
"""

        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ログイン認証コード</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>DxeeWorldログイン認証コード</h2>

        <p>以下の認証コードをログイン画面で入力してください：</p>

        <div style="text-align: center; margin: 30px 0;">
            <div style="background-color: #f8f9fa; border: 2px solid #007bff;
                        padding: 20px; border-radius: 10px; display: inline-block;">
                <span style="font-size: 36px; font-weight: bold; color: #007bff;
                           letter-spacing: 8px; font-family: monospace;">
                    {safe_login_code}
                </span>
            </div>
        </div>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="font-size: 12px; color: #666;">
            コードの有効期限は5分間です。<br>
            このメールに心当たりがない場合は、削除してください。<br><br>
            DxeeWorldチーム
        </p>
    </div>
</body>
</html>
"""

        # Attach both versions
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')

        message.attach(text_part)
        message.attach(html_part)

        return message

    async def _send_email_with_retry(self, message: MIMEMultipart, max_retries: int = 3) -> Result[bool, EmailError]:
        """Send email with retry mechanism"""
        for attempt in range(max_retries):
            try:
                # Create new SMTP connection for each attempt
                smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)

                if self.smtp_use_tls:
                    smtp.starttls()

                smtp.login(self.smtp_username, self.smtp_password)
                smtp.send_message(message)
                smtp.quit()

                masked_recipient = self._mask_email_for_logging(message['To'])
                logger.info(f"Email sent successfully to {masked_recipient}")
                return Result.success(True)

            except Exception as e:
                logger.warning(f"Email send attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return Result.failure(EmailError(f"Failed to send email after {max_retries} attempts: {e}"))

        return Result.failure(EmailError("Unexpected error in email sending"))

    async def send_verification_email(self, recipient: str, redirect_url: str) -> Result[bool, EmailError]:
        """Send verification email with redirect URL"""
        try:
            # Validate email
            if not self._validate_email(recipient):
                return Result.failure(EmailError("Invalid email format"))

            # Check rate limit
            if not self._check_rate_limit(recipient):
                return Result.failure(EmailError("Rate limit exceeded"))

            # Create message
            message = await self._create_verification_message(recipient, redirect_url)

            # Send with retry
            return await self._send_email_with_retry(message)

        except Exception as e:
            logger.exception("Failed to send verification email: %s", e)
            return Result.failure(EmailError(f"Verification email failed: {e}"))

    async def send_login_code_email(self, recipient: str, login_code: str) -> Result[bool, EmailError]:
        """Send login code email"""
        try:
            # Validate email
            if not self._validate_email(recipient):
                return Result.failure(EmailError("Invalid email format"))

            # Check rate limit
            if not self._check_rate_limit(recipient):
                return Result.failure(EmailError("Rate limit exceeded"))

            # Create message
            message = await self._create_login_code_message(recipient, login_code)

            # Send with retry
            return await self._send_email_with_retry(message)

        except Exception as e:
            logger.exception("Failed to send login code email: %s", e)
            return Result.failure(EmailError(f"Login code email failed: {e}"))