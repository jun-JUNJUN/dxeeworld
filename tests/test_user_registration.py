"""
ユーザー登録機能のテスト
"""
import unittest
import asyncio
import bcrypt
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.user_service import UserService, ValidationError, AuthenticationError
from src.handlers.auth_handler import RegisterHandler
from src.models.user import User, UserType
import tornado.testing
import tornado.web
import json


class TestUserRegistration(unittest.TestCase):
    """ユーザー登録機能のユニットテスト"""
    
    def setUp(self):
        self.user_service = UserService()
        self.mock_db_service = AsyncMock()
        self.user_service.db_service = self.mock_db_service
    
    def test_validate_user_registration_data_valid(self):
        """有効なユーザー登録データの検証"""
        user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'name': 'Test User',
            'user_type': UserType.JOB_SEEKER.value,
            'company_id': None,
            'position': None
        }
        
        result = self.user_service.validate_registration_data(user_data)
        self.assertTrue(result.is_success)
    
    def test_validate_user_registration_data_invalid_email(self):
        """無効なメールアドレスでの検証失敗"""
        user_data = {
            'email': 'invalid-email',
            'password': 'SecurePass123!',
            'name': 'Test User',
            'user_type': UserType.JOB_SEEKER.value
        }
        
        result = self.user_service.validate_registration_data(user_data)
        self.assertFalse(result.is_success)
        self.assertIn('email', result.error.field_errors)
    
    def test_validate_user_registration_data_weak_password(self):
        """弱いパスワードでの検証失敗"""
        user_data = {
            'email': 'test@example.com',
            'password': '123',
            'name': 'Test User',
            'user_type': UserType.JOB_SEEKER.value
        }
        
        result = self.user_service.validate_registration_data(user_data)
        self.assertFalse(result.is_success)
        self.assertIn('password', result.error.field_errors)
    
    def test_validate_user_registration_data_missing_name(self):
        """名前が空での検証失敗"""
        user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'name': '',
            'user_type': UserType.JOB_SEEKER.value
        }
        
        result = self.user_service.validate_registration_data(user_data)
        self.assertFalse(result.is_success)
        self.assertIn('name', result.error.field_errors)
    
    async def test_register_user_success(self):
        """ユーザー登録成功のテスト"""
        user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'name': 'Test User',
            'user_type': UserType.JOB_SEEKER.value,
            'company_id': None,
            'position': None
        }
        
        # モック設定: メール重複チェック（重複なし）
        self.mock_db_service.find_one.return_value = None
        # モック設定: ユーザー作成成功
        self.mock_db_service.create.return_value = '674f123456789012345678ab'
        
        result = await self.user_service.register_user(user_data)
        
        self.assertTrue(result.is_success)
        self.assertIsInstance(result.data, User)
        self.assertEqual(result.data.email, 'test@example.com')
        self.assertEqual(result.data.name, 'Test User')
        # パスワードはハッシュ化されている
        self.assertTrue(bcrypt.checkpw('SecurePass123!'.encode('utf-8'), result.data.password_hash.encode('utf-8')))
    
    async def test_register_user_duplicate_email(self):
        """重複メールアドレスでの登録失敗"""
        user_data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'name': 'Test User',
            'user_type': UserType.JOB_SEEKER.value
        }
        
        # モック設定: メール重複チェック（重複あり）
        self.mock_db_service.find_one.return_value = {'email': 'existing@example.com'}
        
        result = await self.user_service.register_user(user_data)
        
        self.assertFalse(result.is_success)
        self.assertIsInstance(result.error, ValidationError)
        self.assertIn('email', result.error.field_errors)
    
    async def test_register_user_with_company(self):
        """企業所属ユーザーの登録成功"""
        user_data = {
            'email': 'recruiter@company.com',
            'password': 'SecurePass123!',
            'name': 'HR Manager',
            'user_type': UserType.RECRUITER.value,
            'company_id': '674f123456789012345678cd',
            'position': 'Human Resources Manager'
        }
        
        # モック設定
        self.mock_db_service.find_one.return_value = None
        self.mock_db_service.create.return_value = '674f123456789012345678ab'
        
        result = await self.user_service.register_user(user_data)
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data.company_id, '674f123456789012345678cd')
        self.assertEqual(result.data.position, 'Human Resources Manager')


class TestRegisterHandler(tornado.testing.AsyncHTTPTestCase):
    """RegisterHandlerの統合テスト"""
    
    def get_app(self):
        """テスト用アプリケーションを作成"""
        return tornado.web.Application([
            (r"/register", RegisterHandler),
        ])
    
    def test_get_register_form(self):
        """登録フォーム表示のテスト"""
        response = self.fetch('/register')
        self.assertEqual(response.code, 200)
        self.assertIn(b'<form', response.body)
        self.assertIn(b'email', response.body)
        self.assertIn(b'password', response.body)
        self.assertIn(b'name', response.body)
    
    @patch('src.handlers.auth_handler.UserService')
    def test_post_register_success(self, mock_user_service):
        """ユーザー登録成功のテスト"""
        # モック設定
        mock_service_instance = AsyncMock()
        mock_user_service.return_value = mock_service_instance
        
        mock_user = User(
            id='674f123456789012345678ab',
            email='test@example.com',
            name='Test User',
            user_type=UserType.JOB_SEEKER,
            password_hash='$2b$12$hashedpassword'
        )
        
        from src.utils.result import Result
        mock_service_instance.register_user.return_value = Result.success(mock_user)
        
        # POSTリクエスト送信
        body = json.dumps({
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'name': 'Test User',
            'user_type': 'JOB_SEEKER'
        })
        
        response = self.fetch('/register', method='POST', body=body,
                            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.code, 201)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['user']['email'], 'test@example.com')
    
    @patch('src.handlers.auth_handler.UserService')
    def test_post_register_validation_error(self, mock_user_service):
        """バリデーションエラーのテスト"""
        # モック設定
        mock_service_instance = AsyncMock()
        mock_user_service.return_value = mock_service_instance
        
        validation_error = ValidationError({'email': ['Invalid email format']})
        from src.utils.result import Result
        mock_service_instance.register_user.return_value = Result.failure(validation_error)
        
        # 無効なデータでPOSTリクエスト
        body = json.dumps({
            'email': 'invalid-email',
            'password': '123',
            'name': '',
            'user_type': 'INVALID_TYPE'
        })
        
        response = self.fetch('/register', method='POST', body=body,
                            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.code, 400)
        response_data = json.loads(response.body)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('errors', response_data)


if __name__ == '__main__':
    # asyncioのイベントループでテスト実行
    unittest.main()