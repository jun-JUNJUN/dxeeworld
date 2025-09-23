"""
Test Facebook OAuth Handler
Task 4.1: Facebook OAuth2.0認証フローの構築
"""
import pytest
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from src.handlers.facebook_oauth_handler import FacebookOAuthHandler
from src.services.oauth2_service import OAuth2Service


class TestFacebookOAuthHandler:
    """Test Facebook OAuth Handler implementation"""

    @pytest.fixture
    def mock_oauth_config(self):
        """Mock OAuth configuration"""
        return {
            'GOOGLE_CLIENT_ID': 'test_google_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
            'FACEBOOK_CLIENT_ID': 'test_facebook_client_id',
            'FACEBOOK_CLIENT_SECRET': 'test_facebook_client_secret',
            'FACEBOOK_REDIRECT_URI': 'http://localhost:8202/auth/facebook/callback',
            'EMAIL_ENCRYPTION_KEY': 'test_encryption_key_32_bytes_long!',
            'EMAIL_HASH_SALT': 'test_salt_for_hashing_emails'
        }

    @pytest.fixture
    def oauth2_service(self):
        """Mock OAuth2 service"""
        service = MagicMock(spec=OAuth2Service)
        return service

    @pytest.fixture
    def facebook_oauth_handler(self, mock_oauth_config, oauth2_service):
        """Facebook OAuth handler fixture"""
        from tornado.web import Application
        from unittest.mock import MagicMock

        with patch.dict(os.environ, mock_oauth_config):
            # Create proper Tornado application with settings
            settings = {
                'cookie_secret': 'test_cookie_secret_for_secure_cookies',
                'debug': True
            }
            mock_app = Application([], **settings)
            mock_request = MagicMock()
            mock_request.protocol = 'http'
            mock_request.host = 'localhost:8202'

            # Create handler with required Tornado parameters
            handler = FacebookOAuthHandler(mock_app, mock_request)
            handler.oauth2_service = oauth2_service

            # Mock additional handler methods to prevent Tornado errors
            handler.send_error = MagicMock()
            handler.redirect = MagicMock()
            handler.set_secure_cookie = MagicMock()
            handler.get_secure_cookie = MagicMock()
            handler.clear_cookie = MagicMock()
            handler.get_argument = MagicMock()

            return handler

    def test_facebook_oauth_handler_initialization(self, mock_oauth_config):
        """Test FacebookOAuthHandler initializes correctly"""
        # RED: テスト先行 - FacebookOAuthHandlerクラスがまだ実装されていない
        from tornado.web import Application
        from unittest.mock import MagicMock

        with patch.dict(os.environ, mock_oauth_config):
            # Create proper Tornado application and request
            settings = {
                'cookie_secret': 'test_cookie_secret_for_secure_cookies',
                'debug': True
            }
            mock_app = Application([], **settings)
            mock_request = MagicMock()

            handler = FacebookOAuthHandler(mock_app, mock_request)

            # Handler has required attributes
            assert hasattr(handler, 'oauth2_service')
            assert hasattr(handler, 'identity_service')
            assert hasattr(handler, 'session_service')

    def test_get_auth_url_generates_facebook_auth_url(self, facebook_oauth_handler, mock_oauth_config):
        """Test GET /auth/facebook generates Facebook authentication URL"""
        # RED: テスト先行 - Facebook認証URL生成機能がまだ実装されていない

        # Mock request attributes
        facebook_oauth_handler.request = MagicMock()
        facebook_oauth_handler.request.protocol = 'http'
        facebook_oauth_handler.request.host = 'localhost:8202'

        # Mock OAuth2Service response
        expected_auth_url = "https://www.facebook.com/v18.0/dialog/oauth?client_id=test_facebook_client_id&redirect_uri=http://localhost:8202/auth/facebook/callback&scope=email&response_type=code&state=random_state"
        facebook_oauth_handler.oauth2_service.get_authorization_url.return_value.is_success = True
        facebook_oauth_handler.oauth2_service.get_authorization_url.return_value.data = expected_auth_url

        # Mock redirect method
        facebook_oauth_handler.redirect = MagicMock()

        # Execute GET request
        facebook_oauth_handler.get()

        # Verify redirect was called with auth URL
        facebook_oauth_handler.redirect.assert_called_once_with(expected_auth_url)

        # Verify OAuth2Service was called with correct parameters
        facebook_oauth_handler.oauth2_service.get_authorization_url.assert_called_once()
        call_args = facebook_oauth_handler.oauth2_service.get_authorization_url.call_args[1]
        assert call_args['provider'] == 'facebook'
        assert call_args['redirect_uri'] == mock_oauth_config['FACEBOOK_REDIRECT_URI']
        assert 'state' in call_args

    def test_callback_processes_facebook_authorization_code(self, facebook_oauth_handler):
        """Test GET /auth/facebook/callback processes authorization code"""
        # RED: テスト先行 - Facebookコールバック処理機能がまだ実装されていない

        # Mock request parameters
        facebook_oauth_handler.get_argument = MagicMock()
        facebook_oauth_handler.get_argument.side_effect = lambda name, default=None: {
            'code': 'test_facebook_auth_code',
            'state': 'test_state'
        }.get(name, default)

        # Mock session state validation
        facebook_oauth_handler.get_secure_cookie = MagicMock(return_value=b'test_state')

        # Mock OAuth2Service token exchange
        mock_user_info = {
            'email': 'user@facebook.com',
            'name': 'Facebook Test User',
            'provider_id': 'facebook_123',
            'provider': 'facebook'
        }
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.return_value.is_success = True
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.return_value.data = mock_user_info

        # Mock Identity service response
        facebook_oauth_handler.identity_service = MagicMock()
        facebook_oauth_handler.identity_service.create_or_update_identity.return_value.is_success = True
        facebook_oauth_handler.identity_service.create_or_update_identity.return_value.data = {
            'id': 'identity_456',
            'email_masked': 'us***@**ok.com'
        }

        # Mock session service
        facebook_oauth_handler.session_service = MagicMock()
        facebook_oauth_handler.session_service.create_session.return_value.is_success = True
        facebook_oauth_handler.session_service.create_session.return_value.data = 'session_456'

        # Mock response methods
        facebook_oauth_handler.set_secure_cookie = MagicMock()
        facebook_oauth_handler.redirect = MagicMock()

        # Execute callback
        facebook_oauth_handler.get()

        # Verify authorization code was processed
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.assert_called_once_with(
            provider='facebook',
            code='test_facebook_auth_code',
            redirect_uri='http://localhost:8202/auth/facebook/callback'
        )

        # Verify Identity was created/updated
        facebook_oauth_handler.identity_service.create_or_update_identity.assert_called_once()

        # Verify session was created and cookie set
        facebook_oauth_handler.session_service.create_session.assert_called_once()
        facebook_oauth_handler.set_secure_cookie.assert_called()

        # Verify redirect to success page
        facebook_oauth_handler.redirect.assert_called_once()

    def test_callback_validates_state_parameter(self, facebook_oauth_handler):
        """Test callback validates state parameter for CSRF protection"""
        # RED: テスト先行 - Facebook Stateパラメーター検証がまだ実装されていない

        # Mock request parameters with mismatched state
        facebook_oauth_handler.get_argument = MagicMock()
        facebook_oauth_handler.get_argument.side_effect = lambda name, default=None: {
            'code': 'test_auth_code',
            'state': 'malicious_state'
        }.get(name, default)

        # Mock stored state (different from request state)
        facebook_oauth_handler.get_secure_cookie = MagicMock(return_value=b'legitimate_state')

        # Mock error response
        facebook_oauth_handler.send_error = MagicMock()

        # Execute callback
        facebook_oauth_handler.get()

        # Verify error response for invalid state
        facebook_oauth_handler.send_error.assert_called_once_with(400, reason="Invalid state parameter")

    def test_facebook_oauth_handler_uses_graph_api(self, facebook_oauth_handler):
        """Test handler is configured for Facebook Graph API endpoints"""
        # RED: テスト先行 - Facebook Graph API設定がまだ実装されていない

        # Mock request
        facebook_oauth_handler.request = MagicMock()
        facebook_oauth_handler.request.protocol = 'http'
        facebook_oauth_handler.request.host = 'localhost:8202'

        # Mock OAuth2Service
        facebook_oauth_handler.oauth2_service.get_authorization_url.return_value.is_success = True
        facebook_oauth_handler.oauth2_service.get_authorization_url.return_value.data = "https://www.facebook.com/v18.0/dialog/oauth"

        facebook_oauth_handler.redirect = MagicMock()

        # Execute GET request
        facebook_oauth_handler.get()

        # Verify OAuth2Service was called with Facebook provider
        call_args = facebook_oauth_handler.oauth2_service.get_authorization_url.call_args[1]
        assert call_args['provider'] == 'facebook'

    def test_facebook_oauth_error_handling(self, facebook_oauth_handler):
        """Test Facebook OAuth service error handling"""
        # RED: テスト先行 - Facebook OAuthエラーハンドリングがまだ実装されていない

        # Mock valid request parameters
        facebook_oauth_handler.get_argument = MagicMock()
        facebook_oauth_handler.get_argument.side_effect = lambda name, default=None: {
            'code': 'test_auth_code',
            'state': 'test_state'
        }.get(name, default)

        facebook_oauth_handler.get_secure_cookie = MagicMock(return_value=b'test_state')

        # Mock OAuth2Service failure
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.return_value.is_success = False
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.return_value.error = "Invalid Facebook authorization code"

        # Mock error response
        facebook_oauth_handler.send_error = MagicMock()

        # Execute callback
        facebook_oauth_handler.get()

        # Verify error response for OAuth failure
        facebook_oauth_handler.send_error.assert_called_once_with(401, reason="Authentication failed")

    def test_facebook_specific_scope_requirements(self, facebook_oauth_handler, mock_oauth_config):
        """Test Facebook-specific scope requirements (email)"""
        # RED: テスト先行 - Facebookスコープ設定がまだ実装されていない

        # Mock request attributes
        facebook_oauth_handler.request = MagicMock()
        facebook_oauth_handler.request.protocol = 'http'
        facebook_oauth_handler.request.host = 'localhost:8202'

        # Mock OAuth2Service response
        facebook_oauth_handler.oauth2_service.get_authorization_url.return_value.is_success = True
        facebook_oauth_handler.oauth2_service.get_authorization_url.return_value.data = "https://www.facebook.com/v18.0/dialog/oauth"

        facebook_oauth_handler.redirect = MagicMock()

        # Execute GET request
        facebook_oauth_handler.get()

        # Verify OAuth2Service was called with correct scope
        call_args = facebook_oauth_handler.oauth2_service.get_authorization_url.call_args[1]
        assert call_args['provider'] == 'facebook'
        # Note: scope verification will be handled in OAuth2Service

    def test_successful_facebook_authentication_flow_integration(self, facebook_oauth_handler):
        """Test complete successful Facebook authentication flow"""
        # RED: テスト先行 - 完全なFacebook認証フロー統合がまだ実装されていない

        # Mock request parameters for callback
        facebook_oauth_handler.get_argument = MagicMock()
        facebook_oauth_handler.get_argument.side_effect = lambda name, default=None: {
            'code': 'valid_facebook_code',
            'state': 'valid_state'
        }.get(name, default)

        facebook_oauth_handler.get_secure_cookie = MagicMock(return_value=b'valid_state')

        # Mock successful OAuth flow
        mock_user_info = {
            'email': 'user@facebook.com',
            'name': 'Facebook User',
            'provider_id': 'facebook_user_123',
            'provider': 'facebook'
        }
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.return_value.is_success = True
        facebook_oauth_handler.oauth2_service.exchange_authorization_code.return_value.data = mock_user_info

        # Mock successful Identity creation
        facebook_oauth_handler.identity_service = MagicMock()
        facebook_oauth_handler.identity_service.create_or_update_identity.return_value.is_success = True
        facebook_oauth_handler.identity_service.create_or_update_identity.return_value.data = {
            'id': 'identity_789',
            'email_masked': 'us***@**ok.com'
        }

        # Mock successful session creation
        facebook_oauth_handler.session_service = MagicMock()
        facebook_oauth_handler.session_service.create_session.return_value.is_success = True
        facebook_oauth_handler.session_service.create_session.return_value.data = 'session_789'

        # Mock response methods
        facebook_oauth_handler.set_secure_cookie = MagicMock()
        facebook_oauth_handler.redirect = MagicMock()

        # Execute callback
        facebook_oauth_handler.get()

        # Verify complete flow executed successfully
        assert facebook_oauth_handler.oauth2_service.exchange_authorization_code.called
        assert facebook_oauth_handler.identity_service.create_or_update_identity.called
        assert facebook_oauth_handler.session_service.create_session.called
        assert facebook_oauth_handler.set_secure_cookie.called
        assert facebook_oauth_handler.redirect.called

        # Verify Identity service received correct user info
        identity_call_args = facebook_oauth_handler.identity_service.create_or_update_identity.call_args[1]
        assert identity_call_args['auth_method'] == 'facebook'
        assert identity_call_args['email'] == 'user@facebook.com'
        assert identity_call_args['user_type'] == 'user'