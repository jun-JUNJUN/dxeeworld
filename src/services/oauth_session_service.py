"""
OAuth Session Service
Task 6.1-6.2: セッション管理システムの統合
OAuth認証に特化したセッション管理
"""
import logging
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from ..database import get_db_service
from ..utils.result import Result

logger = logging.getLogger(__name__)


class OAuthSessionError(Exception):
    """OAuth session service error"""
    pass


class OAuthSessionService:
    """OAuth session management service"""

    COLLECTION_NAME = "auth_sessions"
    DEFAULT_SESSION_DURATION = timedelta(days=30)
    MAX_CONCURRENT_SESSIONS = 3  # Maximum concurrent sessions per identity
    SESSION_RENEWAL_THRESHOLD = timedelta(days=7)  # Renew if less than 7 days remaining

    def __init__(self):
        """Initialize OAuth session service with required dependencies"""
        self.db_service = get_db_service()

    async def create_oauth_session(
        self,
        identity: Dict[str, Any],
        user_agent: str,
        ip_address: str,
        auth_context: str = "oauth_callback"
    ) -> Result[Dict[str, Any], OAuthSessionError]:
        """Create new OAuth session for Identity"""
        try:
            # Generate secure session ID
            session_id = secrets.token_urlsafe(32)

            # Calculate expiry time
            expires_at = datetime.now(timezone.utc) + self.DEFAULT_SESSION_DURATION

            # Create session document
            session_data = {
                'session_id': session_id,
                'identity_id': identity['id'],
                'auth_method': identity['auth_method'],
                'email_masked': identity.get('email_masked', ''),
                'user_type': identity.get('user_type', 'user'),
                'user_agent': user_agent,
                'ip_address': ip_address,
                'auth_context': auth_context,
                'is_active': True,
                'created_at': datetime.now(timezone.utc),
                'expires_at': expires_at,
                'last_accessed': datetime.now(timezone.utc)
            }

            # Enforce concurrent session limit
            await self._enforce_session_limit(identity['id'])

            # Save session to database
            await self.db_service.create(self.COLLECTION_NAME, session_data)

            logger.info(f"OAuth session created for identity {identity['id'][:8]}...")

            return Result.success({
                'session_id': session_id,
                'expires_at': expires_at,
                'auth_method': identity['auth_method'],
                'user_type': identity.get('user_type', 'user'),
                'email_masked': identity.get('email_masked', ''),
                'user_agent': user_agent,
                'ip_address': ip_address,
                'created_at': datetime.now(timezone.utc)
            })

        except Exception as e:
            logger.exception("Failed to create OAuth session: %s", e)
            return Result.failure(OAuthSessionError(f"Session creation failed: {e}"))

    async def validate_oauth_session(
        self,
        session_id: str,
        ip_address: Optional[str] = None
    ) -> Result[Dict[str, Any], OAuthSessionError]:
        """Validate OAuth session and return session info"""
        try:
            # Find session by ID
            session = await self.db_service.find_one(
                self.COLLECTION_NAME,
                {'session_id': session_id, 'is_active': True}
            )

            if not session:
                return Result.failure(OAuthSessionError("Session not found"))

            # Check expiration - MongoDB returns timezone-naive datetime, treat as UTC
            now = datetime.now(timezone.utc)
            expires_at = session['expires_at']
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < now:
                # Mark session as expired
                await self._expire_session(session_id)
                return Result.failure(OAuthSessionError("Session expired"))

            # Security validation: IP address check (optional)
            if ip_address and session.get('ip_address') != ip_address:
                logger.warning(f"IP address mismatch for session {session_id[:8]}...")
                return Result.failure(OAuthSessionError("Session security validation failed"))

            # Update last accessed time
            await self.db_service.update_one(
                self.COLLECTION_NAME,
                {'session_id': session_id},
                {'last_accessed': now}
            )

            return Result.success({
                'session_id': session_id,
                'identity_id': session['identity_id'],
                'auth_method': session['auth_method'],
                'user_type': session['user_type'],
                'email_masked': session['email_masked'],
                'created_at': session['created_at'],
                'expires_at': session['expires_at'],
                'last_accessed': now
            })

        except Exception as e:
            logger.exception("Failed to validate OAuth session: %s", e)
            return Result.failure(OAuthSessionError(f"Session validation failed: {e}"))

    async def logout_session(self, session_id: str) -> Result[bool, OAuthSessionError]:
        """Logout/invalidate OAuth session"""
        try:
            result = await self.db_service.update_one(
                self.COLLECTION_NAME,
                {'session_id': session_id},
                {
                    '$set': {
                        'is_active': False,
                        'invalidated_at': datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Session {session_id[:8]}... logged out")
                return Result.success(True)
            else:
                return Result.failure(OAuthSessionError("Session not found or already inactive"))

        except Exception as e:
            logger.exception("Failed to logout session: %s", e)
            return Result.failure(OAuthSessionError(f"Session logout failed: {e}"))

    async def renew_session(self, session_id: str) -> Result[Dict[str, Any], OAuthSessionError]:
        """Renew/extend OAuth session expiration"""
        try:
            # Calculate new expiry time
            new_expires_at = datetime.now(timezone.utc) + self.DEFAULT_SESSION_DURATION

            result = await self.db_service.update_one(
                self.COLLECTION_NAME,
                {'session_id': session_id, 'is_active': True},
                {
                    '$set': {
                        'expires_at': new_expires_at,
                        'renewed_at': datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Session {session_id[:8]}... renewed")
                return Result.success({'new_expires_at': new_expires_at})
            else:
                return Result.failure(OAuthSessionError("Session not found or inactive"))

        except Exception as e:
            logger.exception("Failed to renew session: %s", e)
            return Result.failure(OAuthSessionError(f"Session renewal failed: {e}"))

    async def get_active_sessions_for_identity(self, identity_id: str) -> Result[List[Dict[str, Any]], OAuthSessionError]:
        """Get all active sessions for identity"""
        try:
            cursor = self.db_service.find(
                self.COLLECTION_NAME,
                {
                    'identity_id': identity_id,
                    'is_active': True,
                    'expires_at': {'$gt': datetime.now(timezone.utc)}
                }
            )
            sessions = await cursor.to_list(None)

            session_list = []
            for session in sessions:
                session_list.append({
                    'session_id': session['session_id'][:8] + '...',  # Masked for security
                    'created_at': session['created_at'],
                    'last_accessed': session['last_accessed'],
                    'ip_address': session.get('ip_address', 'unknown'),
                    'user_agent': session.get('user_agent', 'unknown')[:50]  # Truncated
                })

            return Result.success(session_list)

        except Exception as e:
            logger.exception("Failed to get active sessions: %s", e)
            return Result.failure(OAuthSessionError(f"Get active sessions failed: {e}"))

    async def invalidate_all_sessions_for_identity(self, identity_id: str) -> Result[int, OAuthSessionError]:
        """Invalidate all sessions for identity"""
        try:
            result = await self.db_service.update_many(
                self.COLLECTION_NAME,
                {'identity_id': identity_id, 'is_active': True},
                {
                    '$set': {
                        'is_active': False,
                        'invalidated_at': datetime.now(timezone.utc)
                    }
                }
            )

            logger.info(f"Invalidated {result.modified_count} sessions for identity {identity_id[:8]}...")
            return Result.success(result.modified_count)

        except Exception as e:
            logger.exception("Failed to invalidate all sessions: %s", e)
            return Result.failure(OAuthSessionError(f"Invalidate all sessions failed: {e}"))

    async def cleanup_expired_sessions(self) -> Result[int, OAuthSessionError]:
        """Cleanup expired sessions"""
        try:
            current_time = datetime.now(timezone.utc)

            # Delete expired sessions
            result = await self.db_service.delete_many(
                self.COLLECTION_NAME,
                {
                    '$or': [
                        {'expires_at': {'$lt': current_time}},
                        {'is_active': False}
                    ]
                }
            )

            deleted_count = result.deleted_count if result else 0
            logger.info(f"Cleaned up {deleted_count} expired sessions")

            return Result.success(deleted_count)

        except Exception as e:
            logger.exception("Failed to cleanup expired sessions: %s", e)
            return Result.failure(OAuthSessionError(f"Cleanup failed: {e}"))

    async def _enforce_session_limit(self, identity_id: str):
        """Enforce maximum concurrent sessions per identity"""
        try:
            # Get active sessions count
            cursor = self.db_service.find(
                self.COLLECTION_NAME,
                {
                    'identity_id': identity_id,
                    'is_active': True,
                    'expires_at': {'$gt': datetime.now(timezone.utc)}
                }
            )
            active_sessions = await cursor.to_list(None)

            if len(active_sessions) >= self.MAX_CONCURRENT_SESSIONS:
                # Sort by last_accessed and invalidate oldest sessions
                active_sessions.sort(key=lambda x: x['last_accessed'])
                sessions_to_invalidate = active_sessions[:-self.MAX_CONCURRENT_SESSIONS + 1]

                for session in sessions_to_invalidate:
                    await self.db_service.update_one(
                        self.COLLECTION_NAME,
                        {'session_id': session['session_id']},
                        {
                            '$set': {
                                'is_active': False,
                                'invalidated_at': datetime.now(timezone.utc),
                                'invalidation_reason': 'session_limit_exceeded'
                            }
                        }
                    )

                logger.info(f"Invalidated {len(sessions_to_invalidate)} old sessions for identity {identity_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to enforce session limit: {e}")

    async def _expire_session(self, session_id: str):
        """Mark session as expired (internal method)"""
        try:
            await self.db_service.update_one(
                self.COLLECTION_NAME,
                {'session_id': session_id},
                {
                    '$set': {
                        'is_active': False,
                        'expired_at': datetime.now(timezone.utc)
                    }
                }
            )
        except Exception as e:
            logger.error("Failed to mark session as expired: %s", e)