"""
ユーザー管理サービス
"""
import re
import bcrypt
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..models.user import User, UserType
from ..utils.result import Result

logger = logging.getLogger(__name__)


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

    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """ユーザープロファイル取得"""
        try:
            user_doc = await self.db_service.find_one('users', {'_id': user_id})
            if user_doc and user_doc.get('is_active', True):
                return user_doc.get('profile', {})
            return None
        except Exception as e:
            logger.error(f"プロファイル取得エラー: {e}")
            return None

    def validate_profile_data(self, profile_data: dict) -> Result[bool, ValidationError]:
        """プロファイルデータのバリデーション"""
        errors = {}

        # バイオ検証
        bio = profile_data.get('bio', '').strip()
        if bio and len(bio) > 500:
            errors['bio'] = ['Bio must be less than 500 characters']

        # スキル検証
        skills = profile_data.get('skills', [])
        if skills and not isinstance(skills, list):
            errors['skills'] = ['Skills must be a list']
        elif skills and any(not isinstance(skill, str) or not skill.strip() for skill in skills):
            errors['skills'] = ['All skills must be non-empty strings']

        # 経験年数検証
        experience_years = profile_data.get('experience_years')
        if experience_years is not None:
            if not isinstance(experience_years, int) or experience_years < 0 or experience_years > 50:
                errors['experience_years'] = ['Experience years must be between 0 and 50']

        # URL検証
        for url_field in ['linkedin_url', 'github_url', 'portfolio_url']:
            url = profile_data.get(url_field)
            if url and not self._is_valid_url(url):
                errors[url_field] = [f'Invalid {url_field.replace("_", " ")} format']

        if errors:
            return Result.failure(ValidationError(errors))

        return Result.success(True)

    async def update_user_profile(self, user_id: str, profile_data: dict) -> Result[bool, ValidationError]:
        """ユーザープロファイル更新"""
        # バリデーション
        validation_result = self.validate_profile_data(profile_data)
        if not validation_result.is_success:
            return Result.failure(validation_result.error)

        try:
            # ユーザー存在確認
            user_doc = await self.db_service.find_one('users', {'_id': user_id})
            if not user_doc:
                return Result.failure(ValidationError({'user': ['User not found']}))

            # プロファイル更新
            update_data = {
                'profile': profile_data,
                'updated_at': datetime.utcnow()
            }

            success = await self.db_service.update_one('users', {'_id': user_id}, update_data)
            if success:
                return Result.success(True)
            else:
                return Result.failure(ValidationError({'update': ['Profile update failed']}))

        except Exception as e:
            logger.error(f"プロファイル更新エラー: {e}")
            return Result.failure(ValidationError({'system': ['Profile update failed']}))

    async def search_users_by_skills(self, skills: List[str], limit: int = 10) -> List[Dict]:
        """スキルによるユーザー検索"""
        try:
            filter_dict = {
                'profile.skills': {'$in': skills},
                'is_active': True
            }

            users = await self.db_service.find_many('users', filter_dict, limit=limit)
            return users

        except Exception as e:
            logger.error(f"スキル検索エラー: {e}")
            return []

    async def search_users_by_location(self, location: str, limit: int = 10) -> List[Dict]:
        """地域によるユーザー検索"""
        try:
            filter_dict = {
                'profile.location': {'$regex': location, '$options': 'i'},
                'is_active': True
            }

            users = await self.db_service.find_many('users', filter_dict, limit=limit)
            return users

        except Exception as e:
            logger.error(f"地域検索エラー: {e}")
            return []

    async def search_users_by_experience(self, min_years: int = 0, max_years: int = 50) -> List[Dict]:
        """経験年数によるユーザー検索"""
        try:
            filter_dict = {
                'profile.experience_years': {'$gte': min_years, '$lte': max_years},
                'is_active': True
            }

            users = await self.db_service.find_many('users', filter_dict)
            return users

        except Exception as e:
            logger.error(f"経験年数検索エラー: {e}")
            return []

    async def get_company_members(self, company_id: str) -> List[Dict]:
        """企業メンバー取得"""
        try:
            filter_dict = {
                'company_id': company_id,
                'is_active': True
            }

            members = await self.db_service.find_many('users', filter_dict)
            return members

        except Exception as e:
            logger.error(f"企業メンバー取得エラー: {e}")
            return []

    async def update_user_company_info(self, user_id: str, company_id: str, position: str) -> Result[bool, ValidationError]:
        """ユーザーの企業情報更新"""
        try:
            # ユーザー存在確認
            user_doc = await self.db_service.find_one('users', {'_id': user_id})
            if not user_doc:
                return Result.failure(ValidationError({'user': ['User not found']}))

            # 企業情報更新
            update_data = {
                'company_id': company_id,
                'position': position,
                'user_type': 'company',
                'updated_at': datetime.utcnow()
            }

            success = await self.db_service.update_one('users', {'_id': user_id}, update_data)
            if success:
                return Result.success(True)
            else:
                return Result.failure(ValidationError({'update': ['Company info update failed']}))

        except Exception as e:
            logger.error(f"企業情報更新エラー: {e}")
            return Result.failure(ValidationError({'system': ['Company info update failed']}))

    async def bulk_create_users(self, users_data: List[dict]) -> Result[List[User], ValidationError]:
        """複数ユーザーの一括作成"""
        try:
            # 全データのバリデーション
            for user_data in users_data:
                validation_result = self.validate_registration_data(user_data)
                if not validation_result.is_success:
                    return Result.failure(validation_result.error)

            # メール重複チェック
            for user_data in users_data:
                email = user_data['email'].strip().lower()
                existing_user = await self.db_service.find_one('users', {'email': email})
                if existing_user:
                    return Result.failure(ValidationError({
                        'email': [f'Email "{email}" already exists']
                    }))

            # 一括挿入用ドキュメント準備
            docs = []
            for user_data in users_data:
                password_hash = self._hash_password(user_data['password'])
                doc = {
                    'email': user_data['email'].strip().lower(),
                    'password_hash': password_hash,
                    'name': user_data['name'].strip(),
                    'user_type': user_data['user_type'],
                    'company_id': user_data.get('company_id'),
                    'position': user_data.get('position'),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'is_active': True
                }
                docs.append(doc)

            # 一括挿入
            inserted_ids = await self.db_service.bulk_insert('users', docs)

            # Userオブジェクトリスト作成
            users = []
            for i, user_data in enumerate(users_data):
                user = User(
                    id=str(inserted_ids[i]),
                    email=user_data['email'].strip().lower(),
                    name=user_data['name'].strip(),
                    user_type=UserType(user_data['user_type']),
                    password_hash=docs[i]['password_hash'],
                    company_id=user_data.get('company_id'),
                    position=user_data.get('position')
                )
                users.append(user)

            return Result.success(users)

        except Exception as e:
            logger.error(f"bulk_create_users エラー: {e}")
            return Result.failure(ValidationError({'bulk': ['Bulk creation failed']}))

    async def bulk_update_user_status(self, user_ids: List[str], is_active: bool) -> int:
        """複数ユーザーの状態一括更新"""
        try:
            # UpdateOneオペレーション形式に変換
            bulk_updates = []
            for user_id in user_ids:
                bulk_updates.append({
                    'filter': {'_id': user_id},
                    'update': {'$set': {'is_active': is_active, 'updated_at': datetime.utcnow()}}
                })

            return await self.db_service.bulk_update('users', bulk_updates)

        except Exception as e:
            logger.error(f"bulk_update_user_status エラー: {e}")
            return 0

    async def create_user_indexes(self) -> bool:
        """ユーザーコレクションのインデックスを作成"""
        try:
            # メールアドレスの一意インデックス
            await self.db_service.create_index(
                'users',
                [('email', 1)],
                unique=True
            )

            # ユーザータイプによる検索インデックス
            await self.db_service.create_index(
                'users',
                [('user_type', 1)]
            )

            # 企業IDによる検索インデックス
            await self.db_service.create_index(
                'users',
                [('company_id', 1)]
            )

            # スキルによる検索インデックス
            await self.db_service.create_index(
                'users',
                [('profile.skills', 1)]
            )

            # 地域による検索インデックス
            await self.db_service.create_index(
                'users',
                [('profile.location', 1)]
            )

            # テキスト検索インデックス
            await self.db_service.create_index(
                'users',
                [('name', 'text'), ('profile.bio', 'text')]
            )

            # 複合インデックス（アクティブ + ユーザータイプ）
            await self.db_service.create_index(
                'users',
                [('is_active', 1), ('user_type', 1)]
            )

            return True

        except Exception as e:
            logger.error(f"インデックス作成エラー: {e}")
            return False

    async def search_users_by_text(self, search_text: str, limit: int = 10) -> List[Dict]:
        """テキスト検索によるユーザー検索"""
        try:
            pipeline = [
                {
                    '$match': {
                        '$text': {'$search': search_text},
                        'is_active': True
                    }
                },
                {
                    '$addFields': {
                        'score': {'$meta': 'textScore'}
                    }
                },
                {
                    '$sort': {'score': {'$meta': 'textScore'}}
                },
                {
                    '$limit': limit
                }
            ]

            users = await self.db_service.aggregate('users', pipeline)
            return users

        except Exception as e:
            logger.error(f"テキスト検索エラー: {e}")
            return []

    def _is_valid_url(self, url: str) -> bool:
        """URL形式の検証"""
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None