"""
Session Service
Session management for authenticated users
"""
import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from ..database import get_db_service
from ..utils.result import Result

logger = logging.getLogger(__name__)


class SessionError(Exception):
    """Session service error"""
    pass


class SessionService:
    """Session management service"""

    def __init__(self, db_service=None):
        """Initialize session service"""
        if db_service is None:
            self.db_service = get_db_service()
        else:
            self.db_service = db_service
        self.session_duration = timedelta(days=30)  # Default session duration

    async def create_session(self, user, user_agent: str, ip_address: str) -> Result[str, SessionError]:
        """Create new session for user"""
        try:
            # Generate secure session ID
            session_id = secrets.token_urlsafe(32)

            # Session data
            session_data = {
                'session_id': session_id,
                'user_id': str(user.id) if hasattr(user, 'id') else str(user.get('id', user.get('_id'))),
                'user_email': user.email if hasattr(user, 'email') else user.get('email'),
                'user_agent': user_agent,
                'ip_address': ip_address,
                'created_at': datetime.now(timezone.utc),
                'last_accessed': datetime.now(timezone.utc),
                'expires_at': datetime.now(timezone.utc) + self.session_duration,
                'is_active': True
            }

            # Save session to database
            await self.db_service.create('sessions', session_data)

            logger.info(f"Session created for user {session_data['user_email']}: {session_id}")
            return Result.success(session_id)

        except Exception as e:
            logger.exception("Failed to create session: %s", e)
            return Result.failure(SessionError(f"Session creation failed: {e}"))
    async def validate_session(self, session_id: str) -> Result[Dict[str, Any], SessionError]:
        """Validate session and return session info"""
        try:
            # Find session by ID
            session = await self.db_service.find_one('sessions', {'session_id': session_id})
            if not session:
                return Result.failure(SessionError("Session not found"))

            # Check if session is active
            if not session.get('is_active', False):
                return Result.failure(SessionError("Session is inactive"))

            # Check if session has expired
            now = datetime.now(timezone.utc)
            expires_at = session.get('expires_at')
            if expires_at:
                # Ensure expires_at is timezone-aware
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if now > expires_at:
                    # Mark session as expired
                    await self._expire_session(session_id)
                    return Result.failure(SessionError("Session has expired"))

            # Update last accessed time
            await self.db_service.update_one(
                'sessions',
                {'session_id': session_id},
                {'last_accessed': now}
            )

            return Result.success(session)

        except Exception as e:
            logger.exception("Failed to validate session: %s", e)
            return Result.failure(SessionError(f"Session validation failed: {e}"))

    async def invalidate_session(self, session_id: str) -> Result[bool, SessionError]:
        """Invalidate/logout session"""
        try:
            result = await self.db_service.update_one(
                'sessions',
                {'session_id': session_id},
                {
                    'is_active': False,
                    'invalidated_at': datetime.now(timezone.utc)
                }
            )

            return Result.success(result)

        except Exception as e:
            logger.exception("Failed to invalidate session: %s", e)
            return Result.failure(SessionError(f"Session invalidation failed: {e}"))

    async def _expire_session(self, session_id: str):
        """Mark session as expired (internal method)"""
        try:
            await self.db_service.update_one(
                'sessions',
                {'session_id': session_id},
                {
                    'is_active': False,
                    'expired_at': datetime.now(timezone.utc)
                }
            )
        except Exception as e:
            logger.error("Failed to mark session as expired: %s", e)

    async def get_current_user_from_session(self, session_id: str) -> Result[str, SessionError]:
        """Get current user ID from session"""
        session_result = await self.validate_session(session_id)
        if not session_result.is_success:
            return Result.failure(session_result.error)

        session_data = session_result.data
        user_id = session_data.get('user_id')
        if not user_id:
            return Result.failure(SessionError("No user ID in session"))

        return Result.success(user_id)