"""
Test Email Authentication Handlers
Task 5.3: メール認証新規登録フローの実装
Task 5.4: メール認証ログインフローの実装
TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from src.handlers.email_auth_handler import (
    EmailRegistrationHandler, EmailVerificationHandler, EmailLoginHandler,
    EmailCodeVerificationHandler, EmailCodeResendHandler
)
from src.utils.result import Result


class TestEmailRegistrationHandler(AsyncHTTPTestCase):
    """Test email registration handler for new user signup flow"""

    def get_app(self):
        return Application([
            (r"/auth/email/register", EmailRegistrationHandler),
        ])

    def setUp(self):
        super().setUp()
        # Mock all services
        self.mock_email_auth_service = MagicMock()
        self.mock_email_service = MagicMock()
        self.mock_identity_service = MagicMock()

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    def test_email_registration_form_display(self, mock_identity, mock_email, mock_auth):
        """Test GET request displays email registration form"""
        response = self.fetch('/auth/email/register')

        self.assertEqual(response.code, 200)
        self.assertIn(b'メール認証で新規登録', response.body)
        self.assertIn(b'メールアドレス', response.body)
        self.assertIn(b'ユーザータイプ', response.body)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    def test_email_registration_success(self, mock_identity, mock_email, mock_auth):
        """Test successful email registration flow"""
        # Mock services
        mock_auth_instance = mock_auth.return_value
        mock_email_instance = mock_email.return_value
        mock_identity_instance = mock_identity.return_value

        # Mock existing email check (should fail - email doesn't exist)
        mock_identity_instance.find_identity_by_email.return_value = Result.failure(
            Exception("Not found")
        )

        # Mock token generation
        mock_auth_instance.generate_verification_token.return_value = Result.success({
            'token': 'test_token_123',
            'expires_at': '2024-01-01T01:00:00Z'
        })

        # Mock email sending
        mock_email_instance.send_verification_email.return_value = Result.success(True)

        # Test registration
        body = {
            'email': 'test@example.com',
            'user_type': 'user'
        }
        response = self.fetch(
            '/auth/email/register',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('確認メールを送信しました', response_data['message'])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    def test_email_registration_existing_email(self, mock_identity, mock_email, mock_auth):
        """Test registration with existing email address"""
        mock_identity_instance = mock_identity.return_value

        # Mock existing email check (should succeed - email exists)
        mock_identity_instance.find_identity_by_email.return_value = Result.success({
            'id': 'existing_user',
            'email_hash': 'hash123'
        })

        body = {
            'email': 'existing@example.com',
            'user_type': 'user'
        }
        response = self.fetch(
            '/auth/email/register',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 409)
        response_data = json.loads(response.body)
        self.assertIn('既に登録されています', response_data['message'])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    def test_email_registration_invalid_email(self, mock_identity, mock_email, mock_auth):
        """Test registration with invalid email format"""
        body = {
            'email': '',
            'user_type': 'user'
        }
        response = self.fetch(
            '/auth/email/register',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 400)
        response_data = json.loads(response.body)
        self.assertIn('メールアドレスが必要', response_data['message'])


class TestEmailVerificationHandler(AsyncHTTPTestCase):
    """Test email verification handler for link confirmation"""

    def get_app(self):
        return Application([
            (r"/auth/email/verify", EmailVerificationHandler),
        ])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    def test_email_verification_success(self, mock_session, mock_identity, mock_auth):
        """Test successful email verification and account creation"""
        # Mock services
        mock_auth_instance = mock_auth.return_value
        mock_identity_instance = mock_identity.return_value
        mock_session_instance = mock_session.return_value

        # Mock token verification
        mock_auth_instance.verify_verification_token.return_value = Result.success({
            'email': 'test@example.com',
            'verification_type': 'registration'
        })

        # Mock identity creation
        mock_identity_instance.create_or_update_identity.return_value = Result.success({
            'id': 'new_user_123',
            'email_masked': 'test***@**le.com',
            'user_type': 'user'
        })

        # Mock session creation
        mock_session_instance.create_oauth_session.return_value = Result.success({
            'session_id': 'session_123'
        })

        response = self.fetch('/auth/email/verify?token=test_token&type=registration&user_type=user')

        self.assertEqual(response.code, 200)
        self.assertIn(b'認証成功', response.body)
        self.assertIn(b'登録とログインが完了しました', response.body)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    def test_email_verification_invalid_token(self, mock_auth):
        """Test email verification with invalid token"""
        mock_auth_instance = mock_auth.return_value

        # Mock token verification failure
        mock_auth_instance.verify_verification_token.return_value = Result.failure(
            Exception("Invalid token")
        )

        response = self.fetch('/auth/email/verify?token=invalid_token&type=registration')

        self.assertEqual(response.code, 200)
        self.assertIn(b'認証エラー', response.body)

    def test_email_verification_missing_token(self):
        """Test email verification without token"""
        response = self.fetch('/auth/email/verify')

        self.assertEqual(response.code, 200)
        self.assertIn(b'認証トークンが見つかりません', response.body)


class TestEmailLoginHandler(AsyncHTTPTestCase):
    """Test email login handler for returning users"""

    def get_app(self):
        return Application([
            (r"/auth/email/login", EmailLoginHandler),
        ])

    def test_email_login_form_display(self):
        """Test GET request displays email login form"""
        response = self.fetch('/auth/email/login')

        self.assertEqual(response.code, 200)
        self.assertIn(b'メール認証でログイン', response.body)
        self.assertIn(b'メールアドレス', response.body)

    def test_email_login_code_form_display(self):
        """Test GET request displays code verification form"""
        response = self.fetch('/auth/email/login?step=code&email=test@example.com')

        self.assertEqual(response.code, 200)
        self.assertIn(b'認証コード入力', response.body)
        self.assertIn(b'test***@**le.com', response.body)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    def test_email_login_send_code_success(self, mock_identity, mock_email, mock_auth):
        """Test successful login code sending"""
        # Mock services
        mock_auth_instance = mock_auth.return_value
        mock_email_instance = mock_email.return_value
        mock_identity_instance = mock_identity.return_value

        # Mock identity exists check
        mock_identity_instance.find_identity_by_email.return_value = Result.success({
            'id': 'user_123',
            'email_hash': 'hash123'
        })

        # Mock code generation
        mock_auth_instance.generate_login_code.return_value = Result.success({
            'code': '123456',
            'expires_at': '2024-01-01T00:05:00Z'
        })

        # Mock email sending
        mock_email_instance.send_login_code_email.return_value = Result.success(True)

        body = {'email': 'test@example.com'}
        response = self.fetch(
            '/auth/email/login',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('認証コードを送信しました', response_data['message'])

    @patch('src.handlers.email_auth_handler.IdentityService')
    def test_email_login_nonexistent_email(self, mock_identity):
        """Test login with non-existent email (security: don't reveal)"""
        mock_identity_instance = mock_identity.return_value

        # Mock identity doesn't exist
        mock_identity_instance.find_identity_by_email.return_value = Result.failure(
            Exception("Not found")
        )

        body = {'email': 'nonexistent@example.com'}
        response = self.fetch(
            '/auth/email/login',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        # Should still return success for security (don't reveal email existence)
        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')


class TestEmailCodeVerificationHandler(AsyncHTTPTestCase):
    """Test email code verification handler for login completion"""

    def get_app(self):
        return Application([
            (r"/auth/email/verify-code", EmailCodeVerificationHandler),
        ])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    def test_code_verification_success(self, mock_session, mock_identity, mock_auth):
        """Test successful code verification and login"""
        # Mock services
        mock_auth_instance = mock_auth.return_value
        mock_identity_instance = mock_identity.return_value
        mock_session_instance = mock_session.return_value

        # Mock code verification
        mock_auth_instance.verify_login_code.return_value = Result.success(True)

        # Mock identity retrieval
        mock_identity_instance.find_identity_by_email.return_value = Result.success({
            'id': 'user_123',
            'email_masked': 'test***@**le.com',
            'user_type': 'user'
        })

        # Mock session creation
        mock_session_instance.create_oauth_session.return_value = Result.success({
            'session_id': 'session_123'
        })

        body = {
            'email': 'test@example.com',
            'code': '123456'
        }
        response = self.fetch(
            '/auth/email/verify-code',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('ログインが完了しました', response_data['message'])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    def test_code_verification_invalid_code(self, mock_auth):
        """Test code verification with invalid code"""
        mock_auth_instance = mock_auth.return_value

        # Mock code verification failure
        mock_auth_instance.verify_login_code.return_value = Result.failure(
            Exception("Invalid code")
        )

        body = {
            'email': 'test@example.com',
            'code': '000000'
        }
        response = self.fetch(
            '/auth/email/verify-code',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 400)
        response_data = json.loads(response.body)
        self.assertIn('error', response_data['status'])

    def test_code_verification_missing_data(self):
        """Test code verification with missing email or code"""
        body = {'email': 'test@example.com'}  # Missing code
        response = self.fetch(
            '/auth/email/verify-code',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(body)
        )

        self.assertEqual(response.code, 400)
        response_data = json.loads(response.body)
        self.assertIn('メールアドレスと認証コードが必要', response_data['message'])


class TestEmailCodeResendHandler(AsyncHTTPTestCase):
    """Test email code resend handler for code regeneration"""

    def get_app(self):
        return Application([
            (r"/auth/email/resend-code", EmailCodeResendHandler),
        ])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    def test_code_resend_success(self, mock_email, mock_auth):
        """Test successful code resending"""
        # Mock services
        mock_auth_instance = mock_auth.return_value
        mock_email_instance = mock_email.return_value

        # Mock code generation
        mock_auth_instance.generate_login_code.return_value = Result.success({
            'code': '654321',
            'expires_at': '2024-01-01T00:05:00Z'
        })

        # Mock email sending
        mock_email_instance.send_login_code_email.return_value = Result.success(True)

        response = self.fetch(
            '/auth/email/resend-code',
            method='POST',
            body='email=test@example.com'
        )

        # Should redirect back to code form
        self.assertEqual(response.code, 302)
        self.assertIn(b'/auth/email/login?step=code&email=test@example.com', response.headers.get('Location').encode())

    def test_code_resend_missing_email(self):
        """Test code resend without email"""
        response = self.fetch(
            '/auth/email/resend-code',
            method='POST',
            body=''
        )

        self.assertEqual(response.code, 400)


class TestEmailAuthIntegration:
    """Integration tests for complete email authentication flows"""

    @pytest.mark.asyncio
    async def test_complete_email_registration_flow(self):
        """Integration test: Complete email registration flow"""
        # This would test the complete flow from registration to verification
        # In a real scenario, this would involve:
        # 1. POST /auth/email/register with email
        # 2. Check verification email was sent
        # 3. GET /auth/email/verify with token
        # 4. Verify identity was created and session established
        pass

    @pytest.mark.asyncio
    async def test_complete_email_login_flow(self):
        """Integration test: Complete email login flow"""
        # This would test the complete flow from login to verification
        # In a real scenario, this would involve:
        # 1. POST /auth/email/login with email
        # 2. Check login code email was sent
        # 3. POST /auth/email/verify-code with code
        # 4. Verify session was created
        pass

    @pytest.mark.asyncio
    async def test_email_auth_error_handling(self):
        """Integration test: Error handling across email auth flow"""
        # Test various error scenarios:
        # - SMTP failures
        # - Token expiration
        # - Rate limiting
        # - Invalid codes
        pass

    @pytest.mark.asyncio
    async def test_email_auth_security_measures(self):
        """Integration test: Security measures in email auth"""
        # Test security features:
        # - Email masking in responses
        # - Rate limiting
        # - Token expiration
        # - Attempt limiting
        pass