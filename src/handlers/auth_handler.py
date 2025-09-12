"""
認証関連のHTTPハンドラー
"""
import json
import logging
import tornado.web
from ..services.user_service import UserService, ValidationError, AuthenticationError
from ..services.session_service import SessionService
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class RegisterHandler(BaseHandler):
    """ユーザー登録ハンドラー"""
    
    def initialize(self, db_service=None):
        """ハンドラー初期化"""
        from ..database import DatabaseService
        if db_service is None:
            db_service = DatabaseService()
        self.user_service = UserService(db_service)
    
    def get(self):
        """登録フォーム表示"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>User Registration</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>User Registration</h1>
            <form method="post" action="/register">
                <div>
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div>
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div>
                    <label for="user_type">User Type:</label>
                    <select id="user_type" name="user_type" required>
                        <option value="JOB_SEEKER">Job Seeker</option>
                        <option value="RECRUITER">Recruiter</option>
                    </select>
                </div>
                <div>
                    <label for="company_id">Company ID (optional):</label>
                    <input type="text" id="company_id" name="company_id">
                </div>
                <div>
                    <label for="position">Position (optional):</label>
                    <input type="text" id="position" name="position">
                </div>
                <button type="submit">Register</button>
            </form>
        </body>
        </html>
        """
        self.write(html)
    
    async def post(self):
        """ユーザー登録処理"""
        try:
            # JSON形式とform形式の両方を受け付け
            if self.request.headers.get('Content-Type', '').startswith('application/json'):
                data = json.loads(self.request.body)
            else:
                data = {
                    'email': self.get_argument('email'),
                    'password': self.get_argument('password'),
                    'name': self.get_argument('name'),
                    'user_type': self.get_argument('user_type'),
                    'company_id': self.get_argument('company_id', None),
                    'position': self.get_argument('position', None)
                }
            
            # ユーザー登録
            result = await self.user_service.register_user(data)
            
            if result.is_success:
                self.set_status(201)
                self.set_header('Content-Type', 'application/json')
                self.write({
                    'status': 'success',
                    'message': 'User registered successfully',
                    'user': result.data.to_dict()
                })
            else:
                self.set_status(400)
                self.set_header('Content-Type', 'application/json')
                self.write({
                    'status': 'error',
                    'message': 'Registration failed',
                    'errors': result.error.field_errors
                })
                
        except ValidationError as e:
            self.set_status(400)
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'error',
                'message': 'Validation failed',
                'errors': e.field_errors
            })
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'error',
                'message': 'Internal server error'
            })


class LoginHandler(BaseHandler):
    """ログインハンドラー"""
    
    def initialize(self, db_service=None):
        """ハンドラー初期化"""
        from ..database import DatabaseService
        if db_service is None:
            db_service = DatabaseService()
        self.user_service = UserService(db_service)
        self.session_service = SessionService(db_service)
    
    def get(self):
        """ログインフォーム表示"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>User Login</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>User Login</h1>
            <form method="post" action="/login">
                <div>
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
            <p><a href="/register">Don't have an account? Register here</a></p>
        </body>
        </html>
        """
        self.write(html)
    
    async def post(self):
        """ログイン処理"""
        try:
            # JSON形式とform形式の両方を受け付け
            if self.request.headers.get('Content-Type', '').startswith('application/json'):
                data = json.loads(self.request.body)
            else:
                data = {
                    'email': self.get_argument('email'),
                    'password': self.get_argument('password')
                }
            
            # ユーザー認証
            auth_result = await self.user_service.authenticate_user(data)
            
            if not auth_result.is_success:
                self.set_status(401)
                self.set_header('Content-Type', 'application/json')
                self.write({
                    'status': 'error',
                    'message': 'Invalid credentials'
                })
                return
            
            user = auth_result.data
            
            # セッション作成
            user_agent = self.request.headers.get('User-Agent', '')
            ip_address = self.get_client_ip()
            
            session_result = await self.session_service.create_session(user, user_agent, ip_address)
            
            if not session_result.is_success:
                self.set_status(500)
                self.set_header('Content-Type', 'application/json')
                self.write({
                    'status': 'error',
                    'message': 'Failed to create session'
                })
                return
            
            session_id = session_result.data
            
            # セッションクッキー設定
            self.set_secure_cookie('session_id', session_id, expires_days=1)
            
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'success',
                'message': 'Login successful',
                'user': user.to_dict()
            })
            
        except AuthenticationError as e:
            self.set_status(401)
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'error',
                'message': str(e)
            })
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'error',
                'message': 'Internal server error'
            })
    
    def get_client_ip(self):
        """クライアントIPアドレスを取得"""
        return (self.request.headers.get('X-Forwarded-For') or 
                self.request.headers.get('X-Real-IP') or 
                self.request.remote_ip or 
                '127.0.0.1')


class LogoutHandler(BaseHandler):
    """ログアウトハンドラー"""
    
    def initialize(self, db_service=None):
        """ハンドラー初期化"""
        from ..database import DatabaseService
        if db_service is None:
            db_service = DatabaseService()
        self.session_service = SessionService(db_service)
    
    async def post(self):
        """ログアウト処理"""
        try:
            # セッションID取得
            session_id = self.get_secure_cookie('session_id')
            if session_id:
                session_id = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
                
                # セッション無効化
                await self.session_service.invalidate_session(session_id)
            
            # セッションクッキークリア
            self.clear_cookie('session_id')
            
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'success',
                'message': 'Logout successful'
            })
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write({
                'status': 'error',
                'message': 'Internal server error'
            })