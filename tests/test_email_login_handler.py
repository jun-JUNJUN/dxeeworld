"""
メール認証ログインフォームのテスト
Task 5.4.1: メール認証ログインフォーム
"""
import pytest
import tornado.testing
import tornado.web
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.email_auth_handler import EmailLoginHandler


class TestEmailLoginHandler(tornado.testing.AsyncHTTPTestCase):
    """メール認証ログインハンドラーのテスト"""

    def get_app(self):
        """テスト用Tornadoアプリケーションを作成"""
        return tornado.web.Application([
            (r"/auth/email/login", EmailLoginHandler),
        ], cookie_secret="test-secret-key")

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_login_form_display(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """ログインフォームが正しく表示されることをテスト"""
        response = self.fetch('/auth/email/login', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('メール認証でログイン', response.body.decode('utf-8'))
        self.assertIn('input', response.body.decode('utf-8'))
        self.assertIn('email', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_code_form_display(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """認証コードフォームが正しく表示されることをテスト"""
        response = self.fetch('/auth/email/login?step=code&email=test@example.com', method='GET')

        self.assertEqual(response.code, 200)
        self.assertIn('認証コード入力', response.body.decode('utf-8'))
        self.assertIn('te***@example.com', response.body.decode('utf-8'))  # Masked email
        self.assertIn('6桁の認証コード', response.body.decode('utf-8'))

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_valid_email_sends_code(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """有効なメールアドレスで認証コードが送信されることをテスト"""
        # モックの設定
        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {"email": "test@example.com"}
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_code_result = Mock()
        mock_code_result.is_success = True
        mock_code_result.data = {'code': '123456'}
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_email_result = Mock()
        mock_email_result.is_success = True
        mock_email_service.return_value.send_login_code_email = AsyncMock(return_value=mock_email_result)

        body = 'email=test@example.com'
        response = self.fetch('/auth/email/login', method='POST', body=body)

        # The POST operation either redirects to code form or renders it directly
        if response.code == 302:
            # Redirect case
            self.assertIn('/auth/email/login?step=code&email=test@example.com', response.headers['Location'])
        else:
            # Direct render case
            self.assertEqual(response.code, 200)
            response_body = response.body.decode('utf-8')
            self.assertIn('認証コード入力', response_body)
            self.assertIn('te***@example.com', response_body)  # Masked email

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_nonexistent_email_security_response(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """存在しないメールアドレスでもセキュリティのため成功レスポンスを返すテスト"""
        # モックの設定（ユーザーが存在しない）
        mock_identity_result = Mock()
        mock_identity_result.is_success = False
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        body = 'email=nonexistent@example.com'
        response = self.fetch('/auth/email/login', method='POST', body=body,
                            headers={'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'})

        self.assertEqual(response.code, 200)
        # セキュリティのため、メールが存在しないことを明かさない
        response_data = response.body.decode('utf-8')
        self.assertIn('認証コードを送信しました', response_data)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_empty_email_rejection(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """空のメールアドレスを拒否することをテスト"""
        body = 'email='
        response = self.fetch('/auth/email/login', method='POST', body=body)

        self.assertEqual(response.code, 400)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_code_generation_failure(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """認証コード生成が失敗することをテスト"""
        # モックの設定
        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {"email": "test@example.com"}
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_code_result = Mock()
        mock_code_result.is_success = False
        mock_code_result.error = "Code generation failed"
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_error_result = Mock()
        mock_error_result.user_message = "認証コード生成に失敗しました"
        mock_error_handler.return_value.handle_email_error.return_value = mock_error_result

        body = 'email=test@example.com'
        response = self.fetch('/auth/email/login', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_email_sending_failure(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """メール送信が失敗することをテスト"""
        # モックの設定
        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {"email": "test@example.com"}
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

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
        response = self.fetch('/auth/email/login', method='POST', body=body)

        self.assertEqual(response.code, 500)

    @patch('src.handlers.email_auth_handler.EmailAuthService')
    @patch('src.handlers.email_auth_handler.EmailService')
    @patch('src.handlers.email_auth_handler.IdentityService')
    @patch('src.handlers.email_auth_handler.OAuthSessionService')
    @patch('src.handlers.email_auth_handler.AuthErrorHandler')
    def test_json_request_format(self, mock_error_handler, mock_session_service, mock_identity_service, mock_email_service, mock_email_auth_service):
        """JSON形式のリクエストも処理できることをテスト"""
        # モックの設定
        mock_identity_result = Mock()
        mock_identity_result.is_success = True
        mock_identity_result.data = {"email": "test@example.com"}
        mock_identity_service.return_value.find_identity_by_email = AsyncMock(return_value=mock_identity_result)

        mock_code_result = Mock()
        mock_code_result.is_success = True
        mock_code_result.data = {'code': '123456'}
        mock_email_auth_service.return_value.generate_login_code = AsyncMock(return_value=mock_code_result)

        mock_email_result = Mock()
        mock_email_result.is_success = True
        mock_email_service.return_value.send_login_code_email = AsyncMock(return_value=mock_email_result)

        import json
        body = json.dumps({'email': 'test@example.com'})
        response = self.fetch('/auth/email/login', method='POST', body=body,
                            headers={'Content-Type': 'application/json'})

        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertTrue(response_data['success'])
        self.assertIn('認証コードを送信しました', response_data['message'])


if __name__ == '__main__':
    pytest.main([__file__])