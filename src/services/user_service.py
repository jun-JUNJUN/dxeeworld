"""
ユーザー管理サービス
"""
import re
import bcrypt
from typing import Dict, List, Optional
from datetime import datetime
from ..models.user import User, UserType
from ..utils.result import Result


class ValidationError(Exception):
    """バリデーションエラー"""
    
    def __init__(self, field_errors: Dict[str, List[str]]):
        self.field_errors = field_errors
        super().__init__(f"Validation failed: {field_errors}")


class AuthenticationError(Exception):
    """認証エラー"""
    pass


class UserService:
    """ユーザー管理サービス"""
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def validate_registration_data(self, user_data: dict) -> Result[bool, ValidationError]:
        """ユーザー登録データの検証"""
        errors = {}
        
        # メールアドレス検証
        email = user_data.get('email', '').strip()
        if not email:
            errors['email'] = ['Email is required']
        elif not self._is_valid_email(email):
            errors['email'] = ['Invalid email format']
        
        # パスワード検証
        password = user_data.get('password', '')
        if not password:
            errors['password'] = ['Password is required']
        elif not self._is_strong_password(password):
            errors['password'] = ['Password must be at least 8 characters with letters, numbers and special characters']
        
        # 名前検証
        name = user_data.get('name', '').strip()
        if not name:
            errors['name'] = ['Name is required']
        elif len(name) < 2:
            errors['name'] = ['Name must be at least 2 characters']
        
        # ユーザータイプ検証
        user_type = user_data.get('user_type')
        try:
            UserType(user_type)
        except (ValueError, TypeError):
            errors['user_type'] = ['Invalid user type']
        
        if errors:
            return Result.failure(ValidationError(errors))
        
        return Result.success(True)
    
    async def register_user(self, user_data: dict) -> Result[User, ValidationError]:
        """ユーザー登録"""
        # バリデーション
        validation_result = self.validate_registration_data(user_data)
        if not validation_result.is_success:
            return Result.failure(validation_result.error)
        
        # メール重複チェック
        email = user_data['email'].strip().lower()
        existing_user = await self.db_service.find_one('users', {'email': email})
        if existing_user:
            return Result.failure(ValidationError({'email': ['Email already exists']}))
        
        # パスワードハッシュ化
        password_hash = self._hash_password(user_data['password'])
        
        # ユーザーオブジェクト作成
        user_doc = {
            'email': email,
            'password_hash': password_hash,
            'name': user_data['name'].strip(),
            'user_type': user_data['user_type'],
            'company_id': user_data.get('company_id'),
            'position': user_data.get('position'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }
        
        # データベースに保存
        user_id = await self.db_service.create('users', user_doc)
        
        # Userオブジェクト作成
        user = User(
            id=str(user_id),
            email=email,
            name=user_data['name'].strip(),
            user_type=UserType(user_data['user_type']),
            password_hash=password_hash,
            company_id=user_data.get('company_id'),
            position=user_data.get('position')
        )
        
        return Result.success(user)
    
    async def authenticate_user(self, credentials: dict) -> Result[User, AuthenticationError]:
        """ユーザー認証"""
        try:
            email = credentials.get('email', '').strip().lower()
            password = credentials.get('password', '')
            
            if not email or not password:
                return Result.failure(AuthenticationError("Email and password are required"))
            
            # ユーザー検索
            user_doc = await self.db_service.find_one('users', {'email': email})
            if not user_doc:
                return Result.failure(AuthenticationError("Invalid credentials"))
            
            # アクティブアカウントチェック
            if not user_doc.get('is_active', True):
                return Result.failure(AuthenticationError("Account is inactive"))
            
            # パスワード検証
            stored_hash = user_doc['password_hash']
            if not self._verify_password(password, stored_hash):
                return Result.failure(AuthenticationError("Invalid credentials"))
            
            # Userオブジェクト作成
            user = User.from_dict(user_doc)
            return Result.success(user)
            
        except Exception as e:
            logger.error(f"認証エラー: {e}")
            return Result.failure(AuthenticationError("Authentication failed"))
    
    def _is_valid_email(self, email: str) -> bool:
        """メールアドレス形式の検証"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_strong_password(self, password: str) -> bool:
        """強いパスワードの検証"""
        if len(password) < 8:
            return False
        
        has_letter = re.search(r'[a-zA-Z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        
        return bool(has_letter and has_digit and has_special)
    
    def _hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """パスワードを検証"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False