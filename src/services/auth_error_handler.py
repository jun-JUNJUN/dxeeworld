"""
Authentication Error Handler
Task 9.1: 認証フロー統合とエラーハンドリング
"""
import logging
import re
import uuid
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AuthErrorType(Enum):
    """Authentication error types"""
    INVALID_GRANT = "invalid_grant"
    INVALID_TOKEN = "invalid_token"
    TOKEN_EXPIRED = "token_expired"
    NETWORK_ERROR = "network_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMITED = "rate_limited"
    SECURITY_ERROR = "security_error"
    PERMISSION_DENIED = "permission_denied"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class AuthErrorResult:
    """Authentication error result with user-friendly information"""

    def __init__(
        self,
        error_type: AuthErrorType,
        user_message: str,
        technical_message: str,
        retry_allowed: bool = True,
        suggested_action: str = 'retry',
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.error_type = error_type
        self.user_message = user_message
        self.technical_message = technical_message
        self.retry_allowed = retry_allowed
        self.suggested_action = suggested_action
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)


class AuthErrorHandler:
    """Unified authentication error handler"""

    def __init__(self):
        """Initialize error handler"""
        self.error_patterns = self._initialize_error_patterns()

    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error pattern matching rules"""
        return {
            # OAuth errors
            'invalid_grant': {
                'type': AuthErrorType.INVALID_GRANT,
                'message': '認証コードが無効または期限切れです。もう一度お試しください。',
                'action': 'retry_auth'
            },
            'invalid_client': {
                'type': AuthErrorType.CONFIGURATION_ERROR,
                'message': '認証設定に問題があります。管理者にお問い合わせください。',
                'action': 'reconfigure_client',
                'retry': False
            },
            'access_denied': {
                'type': AuthErrorType.PERMISSION_DENIED,
                'message': 'アクセスが拒否されました。権限を確認してください。',
                'action': 'contact_admin',
                'retry': False
            },

            # Network errors
            'connection': {
                'type': AuthErrorType.NETWORK_ERROR,
                'message': 'ネットワーク接続に問題があります。しばらくしてからお試しください。',
                'action': 'retry_later'
            },
            'timeout': {
                'type': AuthErrorType.NETWORK_ERROR,
                'message': '接続がタイムアウトしました。もう一度お試しください。',
                'action': 'retry_later'
            },

            # Service errors
            'service unavailable': {
                'type': AuthErrorType.SERVICE_UNAVAILABLE,
                'message': 'サービスが一時的に利用できません。しばらくしてからお試しください。',
                'action': 'retry_later'
            },
            'rate limit': {
                'type': AuthErrorType.RATE_LIMITED,
                'message': 'リクエストが多すぎます。しばらくお待ちください。',
                'action': 'retry_later'
            },

            # Token errors
            'expired': {
                'type': AuthErrorType.TOKEN_EXPIRED,
                'message': '認証コードの有効期限が切れました。新しいコードを取得してください。',
                'action': 'resend_code'
            },
            'invalid token': {
                'type': AuthErrorType.INVALID_TOKEN,
                'message': '認証トークンが無効です。もう一度認証を行ってください。',
                'action': 'retry_auth'
            },

            # Security errors
            'csrf': {
                'type': AuthErrorType.SECURITY_ERROR,
                'message': 'セキュリティエラーが発生しました。ページを更新して再度お試しください。',
                'action': 'restart_auth',
                'retry': False
            },
            'security': {
                'type': AuthErrorType.SECURITY_ERROR,
                'message': 'セキュリティ検証に失敗しました。認証を最初からやり直してください。',
                'action': 'restart_auth',
                'retry': False
            }
        }

    def handle_oauth_error(self, provider: str, error: Exception) -> AuthErrorResult:
        """Handle OAuth provider errors (Google, Facebook)"""
        error_message = str(error).lower()
        error_id = str(uuid.uuid4()).replace('-', '')[:12]

        logger.error(f"OAuth error [{error_id}] for {provider}: {error}")

        # Check for specific patterns
        for pattern, config in self.error_patterns.items():
            if pattern in error_message:
                return AuthErrorResult(
                    error_type=config['type'],
                    user_message=config['message'],
                    technical_message=str(error),
                    retry_allowed=config.get('retry', True),
                    suggested_action=config['action'],
                    metadata={
                        'error_id': error_id,
                        'provider': provider,
                        'context': {'auth_method': provider}
                    }
                )

        # Default OAuth error handling
        return AuthErrorResult(
            error_type=AuthErrorType.UNKNOWN_ERROR,
            user_message=f'{provider.title()}認証中に問題が発生しました。もう一度お試しください。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry_auth',
            metadata={
                'error_id': error_id,
                'provider': provider,
                'context': {'auth_method': provider}
            }
        )

    def handle_email_error(self, error: Exception) -> AuthErrorResult:
        """Handle email authentication errors"""
        error_message = str(error).lower()
        error_id = str(uuid.uuid4())[:8]

        logger.error(f"Email auth error [{error_id}]: {error}")

        # SMTP-specific errors
        if 'smtp' in error_message or 'mail' in error_message:
            return AuthErrorResult(
                error_type=AuthErrorType.SERVICE_UNAVAILABLE,
                user_message='メール送信サービスに問題があります。しばらくしてからお試しください。',
                technical_message=str(error),
                retry_allowed=True,
                suggested_action='check_config',
                metadata={
                    'error_id': error_id,
                    'context': {'auth_method': 'email'},
                    'recovery_steps': ['SMTP設定確認', 'メールサーバー状態確認']
                }
            )

        # Check for general patterns
        result = self._match_error_pattern(error_message, error_id)
        if result:
            result.metadata['context'] = {'auth_method': 'email'}
            if result.error_type == AuthErrorType.TOKEN_EXPIRED:
                result.suggested_action = 'resend_code'
            return result

        # Default email error
        return AuthErrorResult(
            error_type=AuthErrorType.UNKNOWN_ERROR,
            user_message='メール認証中に問題が発生しました。もう一度お試しください。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry_auth',
            metadata={
                'error_id': error_id,
                'context': {'auth_method': 'email'}
            }
        )

    def handle_network_error(self, error: Exception) -> AuthErrorResult:
        """Handle network-related errors"""
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Network error [{error_id}]: {error}")

        return AuthErrorResult(
            error_type=AuthErrorType.NETWORK_ERROR,
            user_message='ネットワーク接続に問題があります。インターネット接続を確認してもう一度お試しください。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry_later',
            metadata={
                'error_id': error_id,
                'recovery_steps': ['インターネット接続確認', '数分後に再試行']
            }
        )

    def handle_service_error(self, error: Exception) -> AuthErrorResult:
        """Handle service unavailability errors"""
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Service error [{error_id}]: {error}")

        return AuthErrorResult(
            error_type=AuthErrorType.SERVICE_UNAVAILABLE,
            user_message='サービスが一時的に利用できません。しばらくしてからお試しください。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry_later',
            metadata={
                'error_id': error_id,
                'recovery_steps': ['5-10分後に再試行', 'サービス状況確認']
            }
        )

    def handle_rate_limit_error(self, error: Exception, retry_after: int = 60) -> AuthErrorResult:
        """Handle rate limiting errors"""
        error_id = str(uuid.uuid4())[:8]
        logger.warning(f"Rate limit error [{error_id}]: {error}")

        return AuthErrorResult(
            error_type=AuthErrorType.RATE_LIMITED,
            user_message=f'リクエストが多すぎます。{retry_after}秒後に再度お試しください。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry_later',
            metadata={
                'error_id': error_id,
                'retry_after': retry_after,
                'recovery_steps': [f'{retry_after}秒待機', '再試行']
            }
        )

    def handle_security_error(self, error: Exception) -> AuthErrorResult:
        """Handle security-related errors"""
        error_id = str(uuid.uuid4())[:8]
        logger.warning(f"Security error [{error_id}]: {error}")

        return AuthErrorResult(
            error_type=AuthErrorType.SECURITY_ERROR,
            user_message='セキュリティエラーが発生しました。ページを更新して認証をやり直してください。',
            technical_message=str(error),
            retry_allowed=False,
            suggested_action='restart_auth',
            metadata={
                'error_id': error_id,
                'recovery_steps': ['ページ更新', '認証最初からやり直し']
            }
        )

    def handle_session_error(self, error: Exception) -> AuthErrorResult:
        """Handle session-related errors"""
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Session error [{error_id}]: {error}")

        return AuthErrorResult(
            error_type=AuthErrorType.TOKEN_EXPIRED,
            user_message='セッションの有効期限が切れました。再度ログインしてください。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='relogin',
            metadata={
                'error_id': error_id,
                'recovery_steps': ['ログアウト', '再ログイン']
            }
        )

    def handle_permission_error(self, error: Exception) -> AuthErrorResult:
        """Handle permission-related errors"""
        error_id = str(uuid.uuid4())[:8]
        logger.warning(f"Permission error [{error_id}]: {error}")

        return AuthErrorResult(
            error_type=AuthErrorType.PERMISSION_DENIED,
            user_message='この操作を実行する権限がありません。管理者にお問い合わせください。',
            technical_message=str(error),
            retry_allowed=False,
            suggested_action='contact_admin',
            metadata={
                'error_id': error_id,
                'recovery_steps': ['権限確認', '管理者連絡']
            }
        )

    def make_user_friendly(self, error: Exception) -> AuthErrorResult:
        """Convert technical error to user-friendly message"""
        error_message = str(error).lower()
        error_id = str(uuid.uuid4())[:8]

        logger.error(f"Generic error [{error_id}]: {error}")

        # Remove technical details
        user_message = 'システムで問題が発生しました。'

        if 'network' in error_message or 'connection' in error_message:
            user_message = 'ネットワーク接続に問題があります。'
        elif 'timeout' in error_message:
            user_message = '処理に時間がかかりすぎています。'
        elif 'permission' in error_message:
            user_message = 'アクセス権限に問題があります。'
        elif 'config' in error_message:
            user_message = 'システム設定に問題があります。'

        user_message += 'しばらくしてからもう一度お試しください。'

        return AuthErrorResult(
            error_type=AuthErrorType.UNKNOWN_ERROR,
            user_message=user_message,
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry',
            metadata={
                'error_id': error_id,
                'recovery_steps': ['数分待機', '再試行', '問題が続く場合は管理者連絡']
            }
        )

    def handle_error_with_context(self, error: Exception, context: Dict[str, Any]) -> AuthErrorResult:
        """Handle error with additional context"""
        auth_method = context.get('auth_method', 'unknown')

        if auth_method in ['google', 'facebook']:
            result = self.handle_oauth_error(auth_method, error)
        elif auth_method == 'email':
            result = self.handle_email_error(error)
        else:
            result = self.make_user_friendly(error)

        # Add safe context (no sensitive data)
        result.metadata['context'] = {
            'auth_method': context.get('auth_method'),
            'step': context.get('step')
        }

        return result

    def categorize_error(self, error: Exception) -> AuthErrorResult:
        """Automatically categorize error type"""
        error_message = str(error).lower()
        error_id = str(uuid.uuid4())[:8]

        result = self._match_error_pattern(error_message, error_id)
        if result:
            return result

        # Default categorization
        return AuthErrorResult(
            error_type=AuthErrorType.UNKNOWN_ERROR,
            user_message='予期しないエラーが発生しました。',
            technical_message=str(error),
            retry_allowed=True,
            suggested_action='retry',
            metadata={'error_id': error_id}
        )

    def _match_error_pattern(self, error_message: str, error_id: str) -> Optional[AuthErrorResult]:
        """Match error message against known patterns"""
        for pattern, config in self.error_patterns.items():
            if pattern in error_message:
                return AuthErrorResult(
                    error_type=config['type'],
                    user_message=config['message'],
                    technical_message=error_message,
                    retry_allowed=config.get('retry', True),
                    suggested_action=config['action'],
                    metadata={'error_id': error_id}
                )
        return None