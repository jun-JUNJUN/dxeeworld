"""
Facebook OAuth Handler
Task 4.1: Facebook OAuth2.0認証フローの構築
"""
import os
import secrets
import logging
from tornado.web import RequestHandler
from ..services.oauth2_service import OAuth2Service
from ..services.identity_service import IdentityService
from ..services.oauth_session_service import OAuthSessionService

logger = logging.getLogger(__name__)


class FacebookOAuthHandler(RequestHandler):
    """Facebook OAuth authentication handler"""

    def initialize(self):
        """Initialize handler with required services"""
        self.oauth2_service = OAuth2Service()
        self.identity_service = IdentityService()
        self.oauth_session_service = OAuthSessionService()

    async def get(self):
        """
        Handle GET requests for Facebook OAuth
        - Without code parameter: Generate and redirect to auth URL
        - With code parameter: Process OAuth callback
        """
        try:
            # Check HTTPS requirement in production
            if not self._is_https_secure():
                self.send_error(400, reason="HTTPS required")
                return

            # Check if this is a callback with authorization code
            code = self.get_argument('code', None)
            if code:
                await self._handle_callback()
            else:
                self._handle_auth_redirect()

        except Exception as e:
            logger.exception("Facebook OAuth error: %s", e)
            self.send_error(500, reason="Authentication error")

    def _is_https_secure(self) -> bool:
        """Check if HTTPS is required and properly configured"""
        debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
        if debug_mode:
            return True  # Allow HTTP in debug mode

        return self.request.protocol == 'https'

    def _handle_auth_redirect(self):
        """Generate OAuth authorization URL and redirect"""
        try:
            # Generate state parameter for CSRF protection
            state = secrets.token_urlsafe(32)

            # Store state in secure cookie
            self.set_secure_cookie('oauth_state', state, expires_days=1)

            # Build redirect URI
            redirect_uri = self._get_redirect_uri()

            # Get authorization URL from OAuth2Service
            auth_result = self.oauth2_service.get_authorization_url(
                provider='facebook',
                redirect_uri=redirect_uri,
                state=state
            )

            if not auth_result.is_success:
                logger.error("Failed to generate auth URL: %s", auth_result.error)
                self.send_error(500, reason="Authentication setup failed")
                return

            # Redirect to Facebook OAuth
            self.redirect(auth_result.data)

        except Exception as e:
            logger.exception("Auth redirect error: %s", e)
            self.send_error(500, reason="Authentication setup failed")

    async def _handle_callback(self):
        """Process OAuth callback with authorization code"""
        try:
            # Get callback parameters
            code = self.get_argument('code')
            state = self.get_argument('state', None)

            # Validate state parameter for CSRF protection
            if not self._validate_state(state):
                self.send_error(400, reason="Invalid state parameter")
                return

            # Clear state cookie after validation
            self.clear_cookie('oauth_state')

            # Exchange authorization code for user info
            redirect_uri = self._get_redirect_uri()
            token_result = self.oauth2_service.exchange_authorization_code(
                provider='facebook',
                code=code,
                redirect_uri=redirect_uri
            )

            if not token_result.is_success:
                logger.error("Token exchange failed: %s", token_result.error)
                self.send_error(401, reason="Authentication failed")
                return

            user_info = token_result.data

            # Create or update Identity
            identity_result = await self.identity_service.create_or_update_identity(
                auth_method='facebook',
                email=user_info['email'],
                user_type='user',
                provider_data=user_info
            )

            if not identity_result.is_success:
                logger.error("Identity creation failed: %s", identity_result.error)
                self.send_error(500, reason="Account setup failed")
                return

            identity = identity_result.data

            # Create OAuth session
            user_agent = self.request.headers.get('User-Agent', 'browser')
            ip_address = self.request.remote_ip or '127.0.0.1'
            session_result = await self.oauth_session_service.create_oauth_session(
                identity,
                user_agent,
                ip_address,
                auth_context='facebook_oauth_callback'
            )

            if not session_result.is_success:
                logger.error("Session creation failed: %s", session_result.error)
                self.send_error(500, reason="Session setup failed")
                return

            session_id = session_result.data['session_id']

            # Set session cookie
            self.set_secure_cookie('session_id', session_id, expires_days=30)

            # Redirect to success page
            success_url = self.get_argument('next', '/')
            self.redirect(success_url)

        except Exception as e:
            logger.exception("Callback processing error: %s", e)
            self.send_error(500, reason="Authentication processing failed")

    def _validate_state(self, provided_state: str) -> bool:
        """Validate state parameter against stored value"""
        if not provided_state:
            return False

        stored_state = self.get_secure_cookie('oauth_state')
        if not stored_state:
            return False

        # Convert bytes to string for comparison
        stored_state_str = stored_state.decode('utf-8')
        return provided_state == stored_state_str

    def _get_redirect_uri(self) -> str:
        """Build OAuth redirect URI from current request"""
        protocol = self.request.protocol
        host = self.request.host
        return f"{protocol}://{host}/auth/facebook/callback"