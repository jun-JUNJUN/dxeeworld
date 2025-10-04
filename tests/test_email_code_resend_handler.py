"""
ワンタイムコード送信機能のテスト
Task 5.4.2: ワンタイムコード送信機能
"""
import pytest
import tornado.testing
import tornado.web
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.email_auth_handler import EmailCodeResendHandler


class TestEmailCodeResendHandler(tornado.testing.AsyncHTTPTestCase):
    """認証コード再送信ハンドラーのテスト"""

    def get_app(self):
        """テスト用Tornadoアプリケーションを作成"""
        return tornado.web.Application([
            (r"/auth/email/resend-code", EmailCodeResendHandler),
        ], cookie_secret="test-secret-key")

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_successful_code_resend(self, mock_error_handler, mock_email_service, mock_email_auth_service):
        """認証コードの再送信が成功することをテスト"""
        # モックの設定
        mock_code_result = Mock()
        mock_code_result.is_success = True
        mock_code_result.data = {'code': '123456'}
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_email_result = Mock()
        mock_email_result.is_success = True
        mock_email_service.return_value.send_login_code_email = AsyncMock(return_value=mock_email_result)

        body = 'email=test@example.com'
        response = self.fetch('/auth/email/resend-code', method='POST', body=body, follow_redirects=False)

        self.assertEqual(response.code, 302)  # Redirect back to code form
        self.assertIn('/auth/email/login?step=code&email=test@example.com', response.headers['Location'])

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_empty_email_rejection(self, mock_error_handler, mock_email_service, mock_email_auth_service):
        """空のメールアドレスを拒否することをテスト"""
        body = 'email='
        response = self.fetch('/auth/email/resend-code', method='POST', body=body)

        self.assertEqual(response.code, 400)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_code_generation_failure(self, mock_error_handler, mock_email_service, mock_email_auth_service):
        """認証コード生成が失敗することをテスト"""
        # モックの設定
        mock_code_result = Mock()
        mock_code_result.is_success = False
        mock_code_result.error = "Code generation failed"
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_error_result = Mock()
        mock_error_result.user_message = "認証コード生成に失敗しました"
        mock_error_handler.return_value.handle_email_error.return_value = mock_error_result

        body = 'email=test@example.com'
        response = self.fetch('/auth/email/resend-code', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_email_sending_failure(self, mock_error_handler, mock_email_service, mock_email_auth_service):
        """メール送信が失敗することをテスト"""
        # モックの設定
        mock_code_result = Mock()
        mock_code_result.is_success = True
        mock_code_result.data = {'code': '123456'}
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_email_result = Mock()
        mock_email_result.is_success = False
        mock_email_result.error = "SMTP Error"
        mock_email_service.return_value.send_login_code_email = AsyncMock(return_value=mock_email_result)

        mock_error_result = Mock()
        mock_error_result.user_message = "メール送信に失敗しました"
        mock_error_handler.return_value.handle_email_error.return_value = mock_error_result

        body = 'email=test@example.com'
        response = self.fetch('/auth/email/resend-code', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_exception_handling(self, mock_error_handler, mock_email_service, mock_email_auth_service):
        """例外処理のテスト"""
        # モックの設定
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(side_effect=Exception("Database error"))

        mock_error_result = Mock()
        mock_error_result.user_message = "システムエラーが発生しました"
        mock_error_handler.return_value.make_user_friendly.return_value = mock_error_result

        body = 'email=test@example.com'
        response = self.fetch('/auth/email/resend-code', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_whitespace_email_handling(self, mock_error_handler, mock_email_service, mock_email_auth_service):
        """メールアドレスの空白処理をテスト"""
        # モックの設定
        mock_code_result = Mock()
        mock_code_result.is_success = True
        mock_code_result.data = {'code': '123456'}
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_email_result = Mock()
        mock_email_result.is_success = True
        mock_email_service.return_value.send_login_code_email = AsyncMock(return_value=mock_email_result)

        body = 'email=  Test@Example.COM  '  # With whitespace and mixed case
        response = self.fetch('/auth/email/resend-code', method='POST', body=body, follow_redirects=False)

        self.assertEqual(response.code, 302)
        # Verify the email was normalized to lowercase and trimmed
        mock_email_auth_service.return_value.generate_login_code.assert_called_once_with('test@example.com')


if __name__ == '__main__':
    pytest.main([__file__])