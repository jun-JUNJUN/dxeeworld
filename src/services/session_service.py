"""
セッション管理サービス
"""
import secrets
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..utils.result import Result
from ..models.user import User

logger = logging.getLogger(__name__)


class SessionExpiredError(Exception):
    """セッション期限切れエラー"""
    pass


class SessionService:
    """セッション管理サービス"""
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.session_duration = timedelta(days=1)  # 24時間
    
    async def create_session(self, user: User, user_agent: str, ip_address: str) -> Result[str, Exception]:
        """セッションを作成"""
        try:
            # セッションIDを生成（32文字の安全なランダム文字列）
            session_id = secrets.token_urlsafe(24)  # 32文字
            
            now = datetime.utcnow()
            expires_at = now + self.session_duration
            
            session_doc = {
                '_id': session_id,
                'user_id': user.id,
                'created_at': now,
                'expires_at': expires_at,
                'metadata': {
                    'user_agent': user_agent,
                    'ip_address': ip_address
                }
            }
            
            # データベースに保存
            await self.db_service.create('sessions', session_doc)
            
            logger.info(f"セッション作成成功: {session_id[:8]}... for user {user.email}")
            return Result.success(session_id)
            
        except Exception as e:
            logger.error(f"セッション作成エラー: {e}")
            return Result.failure(e)
    
    async def validate_session(self, session_id: str) -> Result[Dict, Exception]:
        """セッションを検証"""
        try:
            if not session_id:
                return Result.failure(Exception("Session ID is required"))
            
            # セッション検索
            session_doc = await self.db_service.find_one('sessions', {'_id': session_id})
            
            if not session_doc:
                return Result.failure(Exception("Session not found"))
            
            # 期限切れチェック
            expires_at = session_doc['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            if datetime.utcnow() > expires_at:
                # 期限切れセッションを削除
                await self.db_service.delete_one('sessions', {'_id': session_id})
                return Result.failure(SessionExpiredError("Session expired"))
            
            return Result.success(session_doc)
            
        except Exception as e:
            logger.error(f"セッション検証エラー: {e}")
            return Result.failure(e)
    
    async def invalidate_session(self, session_id: str) -> Result[bool, Exception]:
        """セッションを無効化（削除）"""
        try:
            if not session_id:
                return Result.success(True)  # 既に無効
            
            # セッションを削除
            result = await self.db_service.delete_one('sessions', {'_id': session_id})
            
            logger.info(f"セッション無効化: {session_id[:8]}...")
            return Result.success(True)
            
        except Exception as e:
            logger.error(f"セッション無効化エラー: {e}")
            return Result.failure(e)
    
    async def get_user_id_from_session(self, session_id: str) -> Result[str, Exception]:
        """セッションからユーザーIDを取得"""
        session_result = await self.validate_session(session_id)
        
        if not session_result.is_success:
            return Result.failure(session_result.error)
        
        user_id = session_result.data.get('user_id')
        if not user_id:
            return Result.failure(Exception("User ID not found in session"))
        
        return Result.success(user_id)