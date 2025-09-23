"""
Test OAuth2Service Facebook Integration
Task 4.1: Facebook OAuth2.0認証フローの構築
"""
import pytest
import os
from unittest.mock import patch, MagicMock
import requests
from src.services.oauth2_service import OAuth2Service


class TestOAuth2ServiceFacebook:
    """Test OAuth2Service Facebook integration"""

    @pytest.fixture
    def oauth2_service(self):
        """OAuth2 service fixture with Facebook config"""
        mock_env = {
            'GOOGLE_CLIENT_ID': 'test_google_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
            'FACEBOOK_CLIENT_ID': 'test_facebook_client_id',
            'FACEBOOK_CLIENT_SECRET': 'test_facebook_client_secret'
        }
        with patch.dict(os.environ, mock_env):
            return OAuth2Service()

    def test_facebook_authorization_url_generation(self, oauth2_service):
        """Test Facebook authorization URL generation"""
        # RED: テスト先行 - Facebook認証URL生成がまだ実装されていない

        redirect_uri = "http://localhost:8202/auth/facebook/callback"
        state = "test_state_123"

        result = oauth2_service.get_authorization_url(
            provider='facebook',
            redirect_uri=redirect_uri,
            state=state
        )

        assert result.is_success
        auth_url = result.data

        # Verify URL contains required Facebook OAuth parameters
        assert 'https://www.facebook.com/v18.0/dialog/oauth' in auth_url
        assert 'client_id=test_facebook_client_id' in auth_url
        assert 'redirect_uri=http%3A%2F%2Flocalhost%3A8202%2Fauth%2Ffacebook%2Fcallback' in auth_url  # URL encoded
        assert 'scope=email' in auth_url
        assert 'response_type=code' in auth_url
        assert f'state={state}' in auth_url

    @patch('requests.post')
    @patch('requests.get')
    def test_facebook_authorization_code_exchange(self, mock_get, mock_post, oauth2_service):
        """Test Facebook authorization code exchange"""
        # RED: テスト先行 - Facebook認証コード交換がまだ実装されていない

        # Mock token exchange response
        mock_token_response = MagicMock()
        mock_token_response.raise_for_status.return_value = None
        mock_token_response.json.return_value = {
            'access_token': 'facebook_access_token_123',
            'token_type': 'bearer'
        }
        mock_post.return_value = mock_token_response

        # Mock user info response
        mock_userinfo_response = MagicMock()
        mock_userinfo_response.raise_for_status.return_value = None
        mock_userinfo_response.json.return_value = {
            'id': 'facebook_user_123',
            'name': 'Facebook Test User',
            'email': 'user@facebook.com'
        }
        mock_get.return_value = mock_userinfo_response

        # Execute code exchange
        result = oauth2_service.exchange_authorization_code(
            provider='facebook',
            code='test_facebook_code',
            redirect_uri='http://localhost:8202/auth/facebook/callback'
        )

        assert result.is_success
        user_info = result.data

        # Verify standardized user info format
        assert user_info['email'] == 'user@facebook.com'
        assert user_info['name'] == 'Facebook Test User'
        assert user_info['provider_id'] == 'facebook_user_123'
        assert user_info['provider'] == 'facebook'

        # Verify correct API calls were made
        assert mock_post.called
        assert mock_get.called

        # Verify token exchange URL
        token_call = mock_post.call_args
        assert 'https://graph.facebook.com/v18.0/oauth/access_token' in token_call[0][0]

        # Verify user info URL
        userinfo_call = mock_get.call_args
        assert 'https://graph.facebook.com/v18.0/me' in userinfo_call[0][0]

    def test_facebook_configuration_validation(self):
        """Test Facebook configuration validation"""
        # RED: テスト先行 - Facebook設定検証がまだ実装されていない

        # Test missing Facebook client ID
        incomplete_env = {
            'GOOGLE_CLIENT_ID': 'test_google_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
            'FACEBOOK_CLIENT_SECRET': 'test_facebook_client_secret'
            # Missing FACEBOOK_CLIENT_ID
        }

        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValueError, match="FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET are required"):
                OAuth2Service()

    def test_facebook_error_handling(self, oauth2_service):
        """Test Facebook OAuth error handling"""
        # RED: テスト先行 - Facebookエラーハンドリングがまだ実装されていない

        with patch('requests.post') as mock_post:
            # Mock failed token exchange
            mock_post.side_effect = requests.RequestException("Facebook API error")

            result = oauth2_service.exchange_authorization_code(
                provider='facebook',
                code='invalid_code',
                redirect_uri='http://localhost:8202/auth/facebook/callback'
            )

            assert not result.is_success
            assert "Facebook API error" in str(result.error)

    def test_facebook_scope_configuration(self, oauth2_service):
        """Test Facebook scope configuration"""
        # RED: テスト先行 - Facebookスコープ設定がまだ実装されていない

        result = oauth2_service.get_authorization_url(
            provider='facebook',
            redirect_uri='http://localhost:8202/auth/facebook/callback',
            state='test_state'
        )

        assert result.is_success
        auth_url = result.data

        # Verify Facebook-specific scope is included
        assert 'scope=email' in auth_url

    @patch('requests.post')
    @patch('requests.get')
    def test_facebook_user_info_without_email(self, mock_get, mock_post, oauth2_service):
        """Test handling Facebook user info without email"""
        # RED: テスト先行 - メールアドレスなしFacebookユーザー処理がまだ実装されていない

        # Mock successful token exchange
        mock_token_response = MagicMock()
        mock_token_response.raise_for_status.return_value = None
        mock_token_response.json.return_value = {
            'access_token': 'facebook_access_token_123'
        }
        mock_post.return_value = mock_token_response

        # Mock user info response without email
        mock_userinfo_response = MagicMock()
        mock_userinfo_response.raise_for_status.return_value = None
        mock_userinfo_response.json.return_value = {
            'id': 'facebook_user_123',
            'name': 'Facebook Test User'
            # No email field
        }
        mock_get.return_value = mock_userinfo_response

        result = oauth2_service.exchange_authorization_code(
            provider='facebook',
            code='test_code',
            redirect_uri='http://localhost:8202/auth/facebook/callback'
        )

        assert not result.is_success
        assert "No email address received from Facebook" in str(result.error)