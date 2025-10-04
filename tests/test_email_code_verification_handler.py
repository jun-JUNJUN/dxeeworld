"""
ワンタイムコード認証とログインのテスト
Task 5.4.3: ワンタイムコード認証とログイン
"""
import pytest
import tornado.testing
import tornado.web
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.email_auth_handler import EmailCodeVerificationHandler


class TestEmailCodeVerificationHandler(tornado.testing.AsyncHTTPTestCase):
    """メール認証コード確認ハンドラーのテスト"""

    def get_app(self):
        """テスト用Tornadoアプリケーションを作成"""
        return tornado.web.Application([
            (r"/auth/email/verify-code", EmailCodeVerificationHandler),
        ], cookie_secret="test-secret-key")

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_successful_code_verification_and_login(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """認証コードの確認とログインが成功することをテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {
            'id': 'user123',
            'email_masked': 'te***@example.com',
            'user_type': 'user'
        }
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_session_result = Mock()
        mock_session_result.is_success = True
        mock_session_result.data = {'session_id': 'session123'}
        mock_session_service.return_value.create_oauth_session = AsyncMock(return_value=mock_session_result)

        body = 'email=test@example.com&code=123456'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)

        self.assertEqual(response.code, 200)
        response_body = response.body.decode('utf-8')
        self.assertIn('ログインが完了しました', response_body)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_invalid_code_rejection(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """無効な認証コードを拒否することをテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = False
        mock_verification_result.error = "Invalid code"
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(return_value=mock_verification_result)

        mock_error_result = Mock()
        mock_error_result.user_message = "認証コードが無効です"
        mock_error_handler.return_value.handle_email_error.return_value = mock_error_result

        body = 'email=test@example.com&code=invalid'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)

        self.assertEqual(response.code, 400)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_missing_email_or_code(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """メールアドレスまたは認証コードが欠如している場合をテスト"""
        # Set up mock for user-friendly error handling
        mock_error_result = Mock()
        mock_error_result.user_message = "メールアドレスと認証コードが必要です"
        mock_error_handler.return_value.make_user_friendly.return_value = mock_error_result

        # Test missing email
        body = 'code=123456'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)
        self.assertEqual(response.code, 500)  # Exception handler converts to 500

        # Test missing code
        body = 'email=test@example.com'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)
        self.assertEqual(response.code, 500)  # Exception handler converts to 500

        # Test both missing
        body = ''
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)
        self.assertEqual(response.code, 500)  # Exception handler converts to 500

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_user_not_found_after_verification(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """認証後にユーザーが見つからない場合をテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = False
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        body = 'email=test@example.com&code=123456'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)

        self.assertEqual(response.code, 404)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_session_creation_failure(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """セッション作成が失敗することをテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {
            'id': 'user123',
            'email_masked': 'te***@example.com',
            'user_type': 'user'
        }
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_session_result = Mock()
        mock_session_result.is_success = False
        mock_session_service.return_value.create_oauth_session = AsyncMock(return_value=mock_session_result)

        body = 'email=test@example.com&code=123456'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_json_request_format(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """JSON形式のリクエストも処理できることをテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {
            'id': 'user123',
            'email_masked': 'te***@example.com',
            'user_type': 'user'
        }
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_session_result = Mock()
        mock_session_result.is_success = True
        mock_session_result.data = {'session_id': 'session123'}
        mock_session_service.return_value.create_oauth_session = AsyncMock(return_value=mock_session_result)

        request_data = {'email': 'test@example.com', 'code': '123456'}
        body = json.dumps(request_data)
        response = self.fetch('/auth/email/verify-code', method='POST', body=body,
                            headers={'Content-Type': 'application/json'})

        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertTrue(response_data['success'])
        self.assertIn('ログインが完了しました', response_data['message'])
        self.assertEqual(response_data['user']['id'], 'user123')

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_exception_handling(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """例外処理のテスト"""
        # モックの設定
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(side_effect=Exception("Database error"))

        mock_error_result = Mock()
        mock_error_result.user_message = "システムエラーが発生しました"
        mock_error_handler.return_value.make_user_friendly.return_value = mock_error_result

        body = 'email=test@example.com&code=123456'
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_email_normalization(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_auth_service):
        """メールアドレスの正規化をテスト"""
        # モックの設定
        mock_verification_result = Mock()
        mock_verification_result.is_success = True
        mock_email_auth_service.return_value.verify_login_code = AsyncMock(return_value=mock_verification_result)

        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {
            'id': 'user123',
            'email_masked': 'te***@example.com',
            'user_type': 'user'
        }
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_session_result = Mock()
        mock_session_result.is_success = True
        mock_session_result.data = {'session_id': 'session123'}
        mock_session_service.return_value.create_oauth_session = AsyncMock(return_value=mock_session_result)

        # Test with whitespace and mixed case
        body = 'email=  Test@Example.COM  &code=  123456  '
        response = self.fetch('/auth/email/verify-code', method='POST', body=body)

        self.assertEqual(response.code, 200)
        # Verify the email was normalized
        mock_email_auth_service.return_value.verify_login_code.assert_called_once_with('test@example.com', '123456')


if __name__ == '__main__':
    pytest.main([__file__])