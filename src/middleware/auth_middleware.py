"""
認証・認可ミドルウェア
"""
import logging
from typing import Optional
from datetime import datetime
from ..services.session_service import SessionService
from ..services.user_service import UserService
from ..models.user import User, UserType
from ..utils.result import Result

logger = logging.getLogger(__name__)


class AuthenticationRequired(Exception):
    """認証が必要なエラー"""
    pass


class InsufficientPermissions(Exception):
    """権限不足エラー"""
    pass


class AuthMiddleware:
    """認証・認可ミドルウェア"""
    
    def __init__(self, db_service=None):
        from ..database import DatabaseService
        if db_service is None:
            db_service = DatabaseService()
        self.session_service = SessionService(db_service)
        self.user_service = UserService(db_service)
    
    async def get_user_from_session(self, session_id: str) -> Result[User, Exception]:
        """セッションからユーザーを取得"""
        try:
            if not session_id:
                return Result.failure(Exception("No session ID provided"))
            
            # セッション検証
            session_result = await self.session_service.validate_session(session_id)
            if not session_result.is_success:
                return Result.failure(session_result.error)
            
            # ユーザー情報取得
            user_id = session_result.data['user_id']
            user_doc = await self.session_service.db_service.find_one('users', {'_id': user_id})
            
            if not user_doc:
                return Result.failure(Exception("User not found"))
            
            if not user_doc.get('is_active', True):
                return Result.failure(Exception("User account is inactive"))
            
            # Userオブジェクト作成
            user = User.from_dict(user_doc)
            return Result.success(user)
            
        except Exception as e:
            logger.error(f"セッションからのユーザー取得エラー: {e}")
            return Result.failure(e)
    
    async def require_authentication(self, session_id: Optional[str]) -> Result[User, AuthenticationRequired]:
        """認証を要求"""
        if not session_id:
            return Result.failure(AuthenticationRequired("Authentication required"))
        
        user_result = await self.get_user_from_session(session_id)
        
        if not user_result.is_success:
            return Result.failure(AuthenticationRequired("Invalid or expired session"))
        
        return Result.success(user_result.data)
    
    async def require_role(self, user: User, required_role: UserType) -> Result[User, Exception]:
        """特定のロールを要求"""
        if user.user_type != required_role:
            return Result.failure(Exception("Insufficient permissions"))
        
        return Result.success(user)
    
    async def can_access_resource(self, user: User, resource_user_id: str) -> Result[bool, Exception]:
        """リソースへのアクセス権限をチェック"""
        # ユーザーは自分のリソースにアクセス可能
        if user.id == resource_user_id:
            return Result.success(True)
        
        # RECRUITERは同一企業のリソースにアクセス可能
        if user.user_type == UserType.RECRUITER and user.company_id:
            # リソース所有者の情報を取得
            resource_user_doc = await self.user_service.db_service.find_one('users', {'_id': resource_user_id})
            if (resource_user_doc and 
                resource_user_doc.get('company_id') == user.company_id):
                return Result.success(True)
        
        return Result.failure(Exception("Access denied to resource"))
    
    def get_current_user_context(self, user: User) -> dict:
        """現在のユーザーコンテキストを取得"""
        return {
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'user_type': user.user_type.value,
            'company_id': user.company_id,
            'position': user.position,
            'is_recruiter': user.user_type == UserType.RECRUITER,
            'is_job_seeker': user.user_type == UserType.JOB_SEEKER
        }