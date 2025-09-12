"""
ログイン・ログアウト機能のテスト
"""
import unittest
import json
from unittest.mock import AsyncMock, patch
import bcrypt
from src.services.user_service import UserService, AuthenticationError
from src.services.session_service import SessionService
from src.handlers.auth_handler import LoginHandler, LogoutHandler
from src.models.user import User, UserType
from src.utils.result import Result
import tornado.testing
import tornado.web
import tornado.escape


class TestLoginLogoutService(unittest.TestCase):
    """ログイン・ログアウトサービスのユニットテスト"""
    
    def setUp(self):
        self.user_service = UserService()
        self.session_service = SessionService()
        self.mock_db_service = AsyncMock()
        self.user_service.db_service = self.mock_db_service
        self.session_service.db_service = self.mock_db_service
    
    async def test_authenticate_user_success(self):
        """正常なログイン認証のテスト"""
        # テスト用ユーザーデータ
        password = "SecurePass123!"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = {
            '_id': '674f123456789012345678ab',
            'email': 'test@example.com',
            'password_hash': hashed_password,
            'name': 'Test User',
            'user_type': 'JOB_SEEKER',
            'is_active': True
        }
        
        # モック設定: ユーザー検索成功
        self.mock_db_service.find_one.return_value = user_data
        
        credentials = {
            'email': 'test@example.com',
            'password': password
        }
        
        result = await self.user_service.authenticate_user(credentials)
        
        self.assertTrue(result.is_success)
        self.assertIsInstance(result.data, User)
        self.assertEqual(result.data.email, 'test@example.com')
    
    async def test_authenticate_user_invalid_email(self):
        """存在しないメールアドレスでの認証失敗"""
        # モック設定: ユーザー検索失敗
        self.mock_db_service.find_one.return_value = None
        
        credentials = {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }
        
        result = await self.user_service.authenticate_user(credentials)
        
        self.assertFalse(result.is_success)
        self.assertIsInstance(result.error, AuthenticationError)
    
    async def test_authenticate_user_invalid_password(self):
        """間違ったパスワードでの認証失敗"""
        # テスト用ユーザーデータ
        correct_password = "SecurePass123!"
        hashed_password = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = {
            '_id': '674f123456789012345678ab',
            'email': 'test@example.com',
            'password_hash': hashed_password,
            'name': 'Test User',
            'user_type': 'JOB_SEEKER',
            'is_active': True
        }
        
        # モック設定: ユーザー検索成功
        self.mock_db_service.find_one.return_value = user_data
        
        credentials = {
            'email': 'test@example.com',
            'password': 'WrongPassword!'
        }
        
        result = await self.user_service.authenticate_user(credentials)
        
        self.assertFalse(result.is_success)
        self.assertIsInstance(result.error, AuthenticationError)
    
    async def test_authenticate_user_inactive_account(self):
        """無効化されたアカウントでの認証失敗"""
        password = "SecurePass123!"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = {
            '_id': '674f123456789012345678ab',
            'email': 'test@example.com',
            'password_hash': hashed_password,
            'name': 'Test User',
            'user_type': 'JOB_SEEKER',
            'is_active': False  # 無効化されたアカウント
        }
        
        # モック設定: ユーザー検索成功
        self.mock_db_service.find_one.return_value = user_data
        
        credentials = {
            'email': 'test@example.com',
            'password': password
        }
        
        result = await self.user_service.authenticate_user(credentials)
        
        self.assertFalse(result.is_success)
        self.assertIsInstance(result.error, AuthenticationError)
    
    async def test_create_session_success(self):
        """セッション作成成功のテスト"""
        user = User(
            id='674f123456789012345678ab',
            email='test@example.com',
            name='Test User',
            user_type=UserType.JOB_SEEKER,
            password_hash='hashed'
        )
        
        # モック設定: セッション作成成功
        self.mock_db_service.create.return_value = 'session_abc123'
        
        result = await self.session_service.create_session(user, 'Mozilla/5.0', '127.0.0.1')
        
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.data), 32)  # セッションIDの長さ確認
    
    async def test_validate_session_success(self):
        """有効なセッション検証のテスト"""
        session_id = 'valid_session_123'
        session_data = {
            'user_id': '674f123456789012345678ab',
            'created_at': '2025-01-01T00:00:00Z',
            'expires_at': '2025-01-02T00:00:00Z',  # 有効期限内
            'metadata': {
                'user_agent': 'Mozilla/5.0',
                'ip_address': '127.0.0.1'
            }
        }
        
        # モック設定: セッション検索成功
        self.mock_db_service.find_one.return_value = session_data
        
        result = await self.session_service.validate_session(session_id)
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data['user_id'], '674f123456789012345678ab')
    
    async def test_invalidate_session_success(self):
        """セッション無効化成功のテスト"""
        session_id = 'session_to_invalidate'
        
        # モック設定: セッション削除成功
        self.mock_db_service.delete_one.return_value = True
        
        result = await self.session_service.invalidate_session(session_id)
        
        self.assertTrue(result.is_success)
        self.assertTrue(result.data)


class TestLoginLogoutHandlers(tornado.testing.AsyncHTTPTestCase):
    """LoginHandler, LogoutHandlerの統合テスト"""
    
    def get_app(self):
        """テスト用アプリケーションを作成"""
        return tornado.web.Application([
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
        ], cookie_secret="test-secret-key")
    
    def test_get_login_form(self):
        """ログインフォーム表示のテスト"""
        response = self.fetch('/login')
        self.assertEqual(response.code, 200)
        self.assertIn(b'<form', response.body)
        self.assertIn(b'email', response.body)
        self.assertIn(b'password', response.body)
    
    @patch('src.handlers.auth_handler.UserService')
    @patch('src.handlers.auth_handler.SessionService')
    def test_post_login_success(self, mock_session_service, mock_user_service):
        """ログイン成功のテスト"""
        # モック設定
        mock_user_instance = AsyncMock()
        mock_session_instance = AsyncMock()
        mock_user_service.return_value = mock_user_instance
        mock_session_service.return_value = mock_session_instance
        
        mock_user = User(
            id='674f123456789012345678ab',
            email='test@example.com',
            name='Test User',
            user_type=UserType.JOB_SEEKER,
            password_hash='hashed'
        )
        
        mock_user_instance.authenticate_user.return_value = Result.success(mock_user)
        mock_session_instance.create_session.return_value = Result.success('session_abc123')
        
        # POSTリクエスト送信
        body = json.dumps({
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        response = self.fetch('/login', method='POST', body=body,
                            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        # Cookieヘッダーでセッション設定を確認
        cookie_header = response.headers.get('Set-Cookie', '')
        self.assertIn('session_id=', cookie_header)
    
    @patch('src.handlers.auth_handler.UserService')
    def test_post_login_invalid_credentials(self, mock_user_service):
        """無効な認証情報でのログイン失敗テスト"""
        # モック設定
        mock_user_instance = AsyncMock()
        mock_user_service.return_value = mock_user_instance
        
        auth_error = AuthenticationError("Invalid credentials")
        mock_user_instance.authenticate_user.return_value = Result.failure(auth_error)
        
        # 無効なデータでPOSTリクエスト
        body = json.dumps({
            'email': 'test@example.com',
            'password': 'WrongPassword!'
        })
        
        response = self.fetch('/login', method='POST', body=body,
                            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.code, 401)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('message', response_data)
    
    @patch('src.handlers.auth_handler.SessionService')
    def test_post_logout_success(self, mock_session_service):
        """ログアウト成功のテスト"""
        # モック設定
        mock_session_instance = AsyncMock()
        mock_session_service.return_value = mock_session_instance
        mock_session_instance.invalidate_session.return_value = Result.success(True)
        
        # セッションクッキー付きでリクエスト
        response = self.fetch('/logout', method='POST', body='',
                            headers={'Cookie': 'session_id=test_session_123'})
        
        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        # Cookieクリアのヘッダー確認
        cookie_header = response.headers.get('Set-Cookie', '')
        self.assertIn('session_id=""', cookie_header)  # 空の値でクリア


if __name__ == '__main__':
    unittest.main()