"""
メール認証トークン確認機能のテスト
Task 5.3.2: メール認証トークン確認機能
"""
import pytest
import tornado.testing
import tornado.web
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.email_auth_handler import EmailVerificationHandler


class TestEmailVerificationHandler(tornado.testing.AsyncHTTPTestCase):
    """メール認証トークン確認ハンドラーのテスト"""

    def get_app(self):
        """テスト用Tornadoアプリケーションを作成"""
        return tornado.web.Application([
            (r"/auth/email/verify", EmailVerificationHandler),
        ], cookie_secret="test-secret-key")

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_verification_token_missing(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """認証トークンが欠如している場合のテスト"""
        response = self.fetch('/auth/email/verify', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('認証トークンが見つかりません', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_invalid_verification_token(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """無効な認証トークンのテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = False
        mock_verification_result.error = "Invalid token"
        mock_email_auth_service.return_value.verify_verification_token = AsyncMock(return_value=mock_verification_result)

        mock_error_result = Mock()
        mock_error_result.user_message = "認証トークンが無効です"
        mock_error_handler.return_value.handle_email_error.return_value = mock_error_result

        response = self.fetch('/auth/email/verify?token=invalid_token&type=registration', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('認証トークンが無効です', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_successful_registration_verification(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """登録の認証が成功するテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_verification_result.data = {"email": "test@example.com"}
        mock_email_auth_service.return_value.verify_verification_token = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {"id": "user123", "email": "test@example.com"}
        mock_identity_service.return_value.create_or_update_identity = AsyncMock(return_value=mock_identity_result)

        mock_session_result = Mock()
        mock_session_result.is_success = True
        mock_session_result.data = {"session_id": "session123"}
        mock_session_service.return_value.create_oauth_session = AsyncMock(return_value=mock_session_result)

        response = self.fetch('/auth/email/verify?token=valid_token&type=registration&user_type=user', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('メールアドレスの確認が完了しました', response.body.decode('utf-8'))
        self.assertIn('登録とログインが完了しました', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_identity_creation_failure(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """アカウント作成が失敗するテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_verification_result.data = {"email": "test@example.com"}
        mock_email_auth_service.return_value.verify_verification_token = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = False
        mock_identity_service.return_value.create_or_update_identity = AsyncMock(return_value=mock_identity_result)

        response = self.fetch('/auth/email/verify?token=valid_token&type=registration&user_type=user', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('アカウント作成に失敗しました', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_successful_verification_without_registration(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """登録以外の認証が成功するテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_verification_result.data = {"email": "test@example.com"}
        mock_email_auth_service.return_value.verify_verification_token = AsyncMock(return_value=mock_verification_result)

        response = self.fetch('/auth/email/verify?token=valid_token&type=password_reset', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('メールアドレスの確認が完了しました', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_session_creation_failure_still_succeeds(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """セッション作成が失敗しても認証は成功するテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_verification_result.data = {"email": "test@example.com"}
        mock_email_auth_service.return_value.verify_verification_token = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {"id": "user123", "email": "test@example.com"}
        mock_identity_service.return_value.create_or_update_identity = AsyncMock(return_value=mock_identity_result)

        mock_session_result = Mock()
        mock_session_result.is_success = False
        mock_session_service.return_value.create_oauth_session = AsyncMock(return_value=mock_session_result)

        response = self.fetch('/auth/email/verify?token=valid_token&type=registration&user_type=user', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('メールアドレスの確認が完了しました', response.body.decode('utf-8'))
        # セッション作成に失敗してもメール認証自体は成功

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_exception_handling(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """例外処理のテスト"""
        # モックの設定
        mock_email_auth_service.return_value.verify_verification_token = AsyncMock(side_effect=Exception("Database error"))

        mock_error_result = Mock()
        mock_error_result.user_message = "システムエラーが発生しました"
        mock_error_handler.return_value.make_user_friendly.return_value = mock_error_result

        response = self.fetch('/auth/email/verify?token=valid_token&type=registration', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('システムエラーが発生しました', response.body.decode('utf-8'))


if __name__ == '__main__':
    pytest.main([__file__])