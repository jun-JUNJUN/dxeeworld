"""
セッション管理と権限制御のテスト
"""
import unittest
import json
from unittest.mock import AsyncMock, patch
from src.services.session_service import SessionService, SessionExpiredError
from src.middleware.auth_middleware import AuthMiddleware, AuthenticationRequired
from src.handlers.base_handler import BaseHandler
from src.models.user import User, UserType
from src.utils.result import Result
import tornado.testing
import tornado.web


class TestSessionMiddleware(unittest.TestCase):
    """セッション管理と権限制御のユニットテスト"""
    
    def setUp(self):
        self.session_service = SessionService()
        self.auth_middleware = AuthMiddleware()
        self.mock_db_service = AsyncMock()
        self.session_service.db_service = self.mock_db_service
        self.auth_middleware.session_service = self.session_service
    
    async def test_validate_session_success(self):
        """有効なセッション検証成功のテスト"""
        session_data = {
            'user_id': '674f123456789012345678ab',
            'created_at': '2025-01-01T00:00:00Z',
            'expires_at': '2025-01-02T00:00:00Z',
            'metadata': {
                'user_agent': 'Mozilla/5.0',
                'ip_address': '127.0.0.1'
            }
        }
        
        # モック設定: 有効なセッション
        self.mock_db_service.find_one.return_value = session_data
        
        result = await self.session_service.validate_session('valid_session_123')
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data['user_id'], '674f123456789012345678ab')
    
    async def test_validate_session_expired(self):
        """期限切れセッション検証失敗のテスト"""
        session_data = {
            'user_id': '674f123456789012345678ab',
            'created_at': '2025-01-01T00:00:00Z',
            'expires_at': '2024-12-31T23:59:59Z',  # 期限切れ
            'metadata': {
                'user_agent': 'Mozilla/5.0',
                'ip_address': '127.0.0.1'
            }
        }
        
        # モック設定: 期限切れセッション
        self.mock_db_service.find_one.return_value = session_data
        self.mock_db_service.delete_one.return_value = True  # 期限切れセッション削除
        
        result = await self.session_service.validate_session('expired_session_123')
        
        self.assertFalse(result.is_success)
        self.assertIsInstance(result.error, SessionExpiredError)
    
    async def test_validate_session_not_found(self):
        """存在しないセッション検証失敗のテスト"""
        # モック設定: セッション未発見
        self.mock_db_service.find_one.return_value = None
        
        result = await self.session_service.validate_session('nonexistent_session')
        
        self.assertFalse(result.is_success)
        self.assertEqual(str(result.error), "Session not found")
    
    async def test_get_user_from_session_success(self):
        """セッションからユーザー取得成功のテスト"""
        session_data = {
            'user_id': '674f123456789012345678ab',
            'expires_at': '2025-12-31T23:59:59Z'  # 有効期限内
        }
        
        user_data = {
            '_id': '674f123456789012345678ab',
            'email': 'test@example.com',
            'name': 'Test User',
            'user_type': 'JOB_SEEKER',
            'password_hash': 'hashed',
            'is_active': True
        }
        
        # モック設定
        self.mock_db_service.find_one.side_effect = [session_data, user_data]
        
        result = await self.auth_middleware.get_user_from_session('valid_session')
        
        self.assertTrue(result.is_success)
        self.assertIsInstance(result.data, User)
        self.assertEqual(result.data.email, 'test@example.com')
    
    async def test_require_authentication_success(self):
        """認証要求成功のテスト"""
        user = User(
            id='674f123456789012345678ab',
            email='test@example.com',
            name='Test User',
            user_type=UserType.JOB_SEEKER,
            password_hash='hashed'
        )
        
        # モック設定: 有効なセッション
        self.auth_middleware.get_user_from_session = AsyncMock(return_value=Result.success(user))
        
        result = await self.auth_middleware.require_authentication('valid_session')
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data.email, 'test@example.com')
    
    async def test_require_authentication_no_session(self):
        """セッションなしでの認証要求失敗のテスト"""
        result = await self.auth_middleware.require_authentication(None)
        
        self.assertFalse(result.is_success)
        self.assertIsInstance(result.error, AuthenticationRequired)
    
    async def test_require_role_success(self):
        """ロール要求成功のテスト"""
        user = User(
            id='674f123456789012345678ab',
            email='recruiter@example.com',
            name='HR Manager',
            user_type=UserType.RECRUITER,
            password_hash='hashed'
        )
        
        result = await self.auth_middleware.require_role(user, UserType.RECRUITER)
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data, user)
    
    async def test_require_role_insufficient_permission(self):
        """権限不足でのロール要求失敗のテスト"""
        user = User(
            id='674f123456789012345678ab',
            email='jobseeker@example.com',
            name='Job Seeker',
            user_type=UserType.JOB_SEEKER,
            password_hash='hashed'
        )
        
        result = await self.auth_middleware.require_role(user, UserType.RECRUITER)
        
        self.assertFalse(result.is_success)
        self.assertEqual(str(result.error), "Insufficient permissions")


class ProtectedHandler(BaseHandler):
    """認証が必要なテスト用ハンドラー"""
    
    def initialize(self, auth_middleware=None):
        self.auth_middleware = auth_middleware or AuthMiddleware()
    
    async def get(self):
        # セッション取得
        session_id = self.get_secure_cookie('session_id')
        if session_id:
            session_id = session_id.decode('utf-8')
        
        # 認証チェック
        auth_result = await self.auth_middleware.require_authentication(session_id)
        
        if not auth_result.is_success:
            self.set_status(401)
            self.write({'status': 'error', 'message': 'Authentication required'})
            return
        
        user = auth_result.data
        self.write({'status': 'success', 'user': user.to_dict()})


class RecruiterOnlyHandler(BaseHandler):
    """RECRUITER専用のテスト用ハンドラー"""
    
    def initialize(self, auth_middleware=None):
        self.auth_middleware = auth_middleware or AuthMiddleware()
    
    async def get(self):
        # セッション取得
        session_id = self.get_secure_cookie('session_id')
        if session_id:
            session_id = session_id.decode('utf-8')
        
        # 認証チェック
        auth_result = await self.auth_middleware.require_authentication(session_id)
        
        if not auth_result.is_success:
            self.set_status(401)
            self.write({'status': 'error', 'message': 'Authentication required'})
            return
        
        user = auth_result.data
        
        # ロールチェック
        role_result = await self.auth_middleware.require_role(user, UserType.RECRUITER)
        
        if not role_result.is_success:
            self.set_status(403)
            self.write({'status': 'error', 'message': 'Recruiter access required'})
            return
        
        self.write({'status': 'success', 'message': 'Recruiter area accessed'})


class TestAuthenticationHandlers(tornado.testing.AsyncHTTPTestCase):
    """認証機能付きハンドラーの統合テスト"""
    
    def get_app(self):
        """テスト用アプリケーションを作成"""
        return tornado.web.Application([
            (r"/protected", ProtectedHandler),
            (r"/recruiter-only", RecruiterOnlyHandler),
        ], cookie_secret="test-secret-key")
    
    def test_protected_handler_no_session(self):
        """セッションなしでのアクセス拒否テスト"""
        response = self.fetch('/protected')
        self.assertEqual(response.code, 401)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Authentication required')
    
    @patch('src.middleware.auth_middleware.AuthMiddleware.require_authentication')
    def test_protected_handler_with_valid_session(self, mock_require_auth):
        """有効なセッションでのアクセス成功テスト"""
        # モック設定
        user = User(
            id='674f123456789012345678ab',
            email='test@example.com',
            name='Test User',
            user_type=UserType.JOB_SEEKER,
            password_hash='hashed'
        )
        mock_require_auth.return_value = Result.success(user)
        
        response = self.fetch('/protected', headers={'Cookie': 'session_id=valid_session'})
        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['user']['email'], 'test@example.com')
    
    def test_recruiter_only_no_session(self):
        """セッションなしでのRecruiter専用エリアアクセス拒否テスト"""
        response = self.fetch('/recruiter-only')
        self.assertEqual(response.code, 401)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['message'], 'Authentication required')
    
    @patch('src.middleware.auth_middleware.AuthMiddleware.require_authentication')
    @patch('src.middleware.auth_middleware.AuthMiddleware.require_role')
    def test_recruiter_only_insufficient_role(self, mock_require_role, mock_require_auth):
        """権限不足でのRecruiter専用エリアアクセス拒否テスト"""
        # モック設定: JOB_SEEKERユーザー
        user = User(
            id='674f123456789012345678ab',
            email='jobseeker@example.com',
            name='Job Seeker',
            user_type=UserType.JOB_SEEKER,
            password_hash='hashed'
        )
        mock_require_auth.return_value = Result.success(user)
        mock_require_role.return_value = Result.failure(Exception("Insufficient permissions"))
        
        response = self.fetch('/recruiter-only', headers={'Cookie': 'session_id=valid_session'})
        self.assertEqual(response.code, 403)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['message'], 'Recruiter access required')
    
    @patch('src.middleware.auth_middleware.AuthMiddleware.require_authentication')
    @patch('src.middleware.auth_middleware.AuthMiddleware.require_role')
    def test_recruiter_only_success(self, mock_require_role, mock_require_auth):
        """RECRUITERでのRecruiter専用エリアアクセス成功テスト"""
        # モック設定: RECRUITERユーザー
        user = User(
            id='674f123456789012345678ab',
            email='recruiter@example.com',
            name='HR Manager',
            user_type=UserType.RECRUITER,
            password_hash='hashed'
        )
        mock_require_auth.return_value = Result.success(user)
        mock_require_role.return_value = Result.success(user)
        
        response = self.fetch('/recruiter-only', headers={'Cookie': 'session_id=valid_session'})
        self.assertEqual(response.code, 200)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['message'], 'Recruiter area accessed')


if __name__ == '__main__':
    unittest.main()