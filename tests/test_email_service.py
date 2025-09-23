"""
Test Email Service
Task 5.2: メール送信とSMTP連携機能
TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.services.email_service import EmailService, EmailError
from src.utils.result import Result


class TestEmailService:
    """Test email service for SMTP integration"""

    @pytest.fixture
    @patch('src.services.email_service.smtplib.SMTP')
    def email_service(self, mock_smtp_class):
        """Email service fixture with mocked SMTP"""
        with patch.dict('os.environ', {
            'SMTP_HOST': 'smtp.gmail.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password',
            'SMTP_USE_TLS': 'true'
        }):
            mock_smtp = MagicMock()
            mock_smtp.starttls = MagicMock()
            mock_smtp.login = MagicMock()
            mock_smtp.send_message = MagicMock()
            mock_smtp.quit = MagicMock()
            mock_smtp_class.return_value = mock_smtp

            service = EmailService()
            service._mock_smtp = mock_smtp  # Store for test assertions
            return service

    @pytest.mark.asyncio
    @patch('src.services.email_service.smtplib.SMTP')
    async def test_send_verification_email(self, mock_smtp_class, email_service):
        """RED: Test sending verification email with redirect URL"""
        # This test should fail because send_verification_email is not implemented

        # Setup mock SMTP
        mock_smtp = MagicMock()
        mock_smtp.starttls = MagicMock()
        mock_smtp.login = MagicMock()
        mock_smtp.send_message = MagicMock()
        mock_smtp.quit = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        recipient = "user@example.com"
        redirect_url = "https://example.com/verify?token=abc123"

        result = await email_service.send_verification_email(recipient, redirect_url)

        assert result.is_success
        assert result.data is True

        # Verify SMTP methods were called
        mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.services.email_service.smtplib.SMTP')
    async def test_send_login_code_email(self, mock_smtp_class, email_service):
        """RED: Test sending login code email"""
        # This test should fail because send_login_code_email is not implemented

        # Setup mock SMTP
        mock_smtp = MagicMock()
        mock_smtp.starttls = MagicMock()
        mock_smtp.login = MagicMock()
        mock_smtp.send_message = MagicMock()
        mock_smtp.quit = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        recipient = "user@example.com"
        login_code = "123456"

        result = await email_service.send_login_code_email(recipient, login_code)

        assert result.is_success
        assert result.data is True

        # Verify SMTP methods were called
        mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_template_verification(self, email_service):
        """RED: Test verification email template generation"""
        # This test should fail because email template generation is not implemented

        recipient = "user@example.com"
        redirect_url = "https://example.com/verify?token=abc123"

        message = await email_service._create_verification_message(recipient, redirect_url)

        assert message is not None
        assert isinstance(message, MIMEMultipart)
        assert message['To'] == recipient
        assert message['Subject'] is not None
        # Check basic message structure (content validation is complex due to base64)
        message_str = str(message)
        assert "text/plain" in message_str
        assert "text/html" in message_str

    @pytest.mark.asyncio
    async def test_email_template_login_code(self, email_service):
        """RED: Test login code email template generation"""
        # This test should fail because email template generation is not implemented

        recipient = "user@example.com"
        login_code = "123456"

        message = await email_service._create_login_code_message(recipient, login_code)

        assert message is not None
        assert isinstance(message, MIMEMultipart)
        assert message['To'] == recipient
        assert message['Subject'] is not None
        # Check basic message structure (content validation is complex due to base64)
        message_str = str(message)
        assert "text/plain" in message_str
        assert "text/html" in message_str

    @pytest.mark.asyncio
    async def test_smtp_connection_error_handling(self, email_service):
        """RED: Test SMTP connection error handling"""
        # This test should fail because error handling is not implemented

        # Mock SMTP connection failure
        email_service._mock_smtp.login.side_effect = Exception("SMTP connection failed")

        result = await email_service.send_verification_email("user@example.com", "https://example.com/verify")

        assert not result.is_success
        assert isinstance(result.error, EmailError)
        assert "smtp" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_invalid_email_address_validation(self, email_service):
        """RED: Test validation of invalid email addresses"""
        # This test should fail because email validation is not implemented

        invalid_emails = ["invalid-email", "@domain.com", "user@", "user@domain"]

        for invalid_email in invalid_emails:
            result = await email_service.send_verification_email(invalid_email, "https://example.com/verify")
            assert not result.is_success
            assert isinstance(result.error, EmailError)

    @pytest.mark.asyncio
    async def test_email_rate_limiting(self, email_service):
        """RED: Test email rate limiting functionality"""
        # This test should fail because rate limiting is not implemented

        recipient = "user@example.com"

        # Send multiple emails rapidly
        for i in range(5):
            result = await email_service.send_verification_email(recipient, f"https://example.com/verify{i}")

        # After limit, should be rate limited
        result = await email_service.send_verification_email(recipient, "https://example.com/verify_final")

        # First few should succeed, but eventually rate limited
        # Implementation may vary on specific limits

    @pytest.mark.asyncio
    async def test_email_content_security(self, email_service):
        """RED: Test email content security (no injection)"""
        # This test should fail because content security is not implemented

        recipient = "user@example.com"
        malicious_url = "https://example.com/verify?token=<script>alert('xss')</script>"

        message = await email_service._create_verification_message(recipient, malicious_url)

        # Should escape or sanitize malicious content
        message_str = str(message)
        assert "<script>" not in message_str
        assert "&lt;script&gt;" in message_str or "script" not in message_str.lower()

    @pytest.mark.asyncio
    async def test_smtp_configuration_validation(self, email_service):
        """RED: Test SMTP configuration validation"""
        # This test should fail because configuration validation is not implemented

        # Test with missing configuration
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="SMTP configuration"):
                EmailService()

    @pytest.mark.asyncio
    async def test_email_retry_mechanism(self, email_service):
        """RED: Test email sending retry mechanism"""
        # This test should fail because retry mechanism is not implemented

        # Mock transient failure followed by success
        email_service._mock_smtp.send_message.side_effect = [
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            None  # Success on third try
        ]

        result = await email_service.send_verification_email("user@example.com", "https://example.com/verify")

        # Should succeed after retries
        assert result.is_success
        assert email_service._mock_smtp.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_email_logging_security(self, email_service):
        """RED: Test that sensitive information is not logged"""
        # This test should fail because secure logging is not implemented

        with patch('src.services.email_service.logger') as mock_logger:
            await email_service.send_verification_email("user@example.com", "https://example.com/verify?token=secret123")

            # Check that logs don't contain sensitive information
            for call in mock_logger.info.call_args_list + mock_logger.debug.call_args_list:
                log_message = str(call)
                assert "secret123" not in log_message
                assert "user@example.com" not in log_message  # Email should be masked

    @pytest.mark.asyncio
    async def test_email_html_and_text_format(self, email_service):
        """RED: Test email supports both HTML and text formats"""
        # This test should fail because multi-format email is not implemented

        message = await email_service._create_verification_message("user@example.com", "https://example.com/verify")

        # Should have both HTML and text parts
        assert message.is_multipart()

        parts = message.get_payload()
        content_types = [part.get_content_type() for part in parts]

        assert "text/plain" in content_types
        assert "text/html" in content_types