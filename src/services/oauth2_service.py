"""
OAuth2 Service
Handles OAuth2.0 authentication flows for multiple providers
"""
import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import requests
from ..utils.result import Result

logger = logging.getLogger(__name__)


class OAuth2Error(Exception):
    """OAuth2 service error"""
    pass


class OAuth2Service:
    """OAuth2.0 authentication service for multiple providers"""

    def __init__(self):
        """Initialize OAuth2 service with provider configurations"""
        self.google_config = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'auth_url': 'https://accounts.google.com/o/oauth2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scope': 'email profile'
        }

        self.facebook_config = {
            'client_id': os.getenv('FACEBOOK_CLIENT_ID'),
            'client_secret': os.getenv('FACEBOOK_CLIENT_SECRET'),
            'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
            'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
            'userinfo_url': 'https://graph.facebook.com/v18.0/me',
            'scope': 'email'
        }

        # Validate required configuration
        if not self.google_config['client_id'] or not self.google_config['client_secret']:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required")

        if not self.facebook_config['client_id'] or not self.facebook_config['client_secret']:
            raise ValueError("FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET are required")

    def get_authorization_url(self, provider: str, redirect_uri: str, state: str, **kwargs) -> Result[str, OAuth2Error]:
        """Generate OAuth authorization URL for specified provider"""
        try:
            if provider == 'google':
                return self._get_google_auth_url(redirect_uri, state)
            elif provider == 'facebook':
                return self._get_facebook_auth_url(redirect_uri, state)
            else:
                return Result.failure(OAuth2Error(f"Unsupported provider: {provider}"))

        except Exception as e:
            logger.exception("Failed to generate auth URL for %s: %s", provider, e)
            return Result.failure(OAuth2Error(f"Auth URL generation failed: {e}"))

    def exchange_authorization_code(self, provider: str, code: str, redirect_uri: str, **kwargs) -> Result[Dict[str, Any], OAuth2Error]:
        """Exchange authorization code for access token and user information"""
        try:
            if provider == 'google':
                return self._exchange_google_code(code, redirect_uri)
            elif provider == 'facebook':
                return self._exchange_facebook_code(code, redirect_uri)
            else:
                return Result.failure(OAuth2Error(f"Unsupported provider: {provider}"))

        except Exception as e:
            logger.exception("Failed to exchange code for %s: %s", provider, e)
            return Result.failure(OAuth2Error(f"Code exchange failed: {e}"))

    def _get_google_auth_url(self, redirect_uri: str, state: str) -> Result[str, OAuth2Error]:
        """Generate Google OAuth authorization URL"""
        params = {
            'client_id': self.google_config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': self.google_config['scope'],
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }

        auth_url = f"{self.google_config['auth_url']}?{urlencode(params)}"
        return Result.success(auth_url)

    def _exchange_google_code(self, code: str, redirect_uri: str) -> Result[Dict[str, Any], OAuth2Error]:
        """Exchange Google authorization code for access token and user info"""
        try:
            # Exchange code for access token
            token_data = {
                'client_id': self.google_config['client_id'],
                'client_secret': self.google_config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }

            token_response = requests.post(
                self.google_config['token_url'],
                data=token_data,
                timeout=10
            )
            token_response.raise_for_status()
            token_info = token_response.json()

            if 'access_token' not in token_info:
                return Result.failure(OAuth2Error("No access token received"))

            access_token = token_info['access_token']

            # Get user information
            userinfo_response = requests.get(
                self.google_config['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()

            # Standardize user info format
            standardized_info = {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'provider_id': user_info.get('id'),
                'provider': 'google',
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email', False)
            }

            # Validate required fields
            if not standardized_info['email']:
                return Result.failure(OAuth2Error("No email address received from Google"))

            return Result.success(standardized_info)

        except requests.RequestException as e:
            logger.error("Google API request failed: %s", e)
            return Result.failure(OAuth2Error(f"Google API error: {e}"))
        except (KeyError, ValueError) as e:
            logger.error("Invalid Google API response: %s", e)
            return Result.failure(OAuth2Error(f"Invalid response format: {e}"))

    def _get_facebook_auth_url(self, redirect_uri: str, state: str) -> Result[str, OAuth2Error]:
        """Generate Facebook OAuth authorization URL"""
        params = {
            'client_id': self.facebook_config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': self.facebook_config['scope'],
            'response_type': 'code',
            'state': state
        }

        auth_url = f"{self.facebook_config['auth_url']}?{urlencode(params)}"
        return Result.success(auth_url)

    def _exchange_facebook_code(self, code: str, redirect_uri: str) -> Result[Dict[str, Any], OAuth2Error]:
        """Exchange Facebook authorization code for access token and user info"""
        try:
            # Exchange code for access token
            token_data = {
                'client_id': self.facebook_config['client_id'],
                'client_secret': self.facebook_config['client_secret'],
                'code': code,
                'redirect_uri': redirect_uri
            }

            token_response = requests.post(
                self.facebook_config['token_url'],
                data=token_data,
                timeout=10
            )
            token_response.raise_for_status()
            token_info = token_response.json()

            if 'access_token' not in token_info:
                return Result.failure(OAuth2Error("No access token received"))

            access_token = token_info['access_token']

            # Get user information
            userinfo_params = {
                'access_token': access_token,
                'fields': 'id,name,email'
            }
            userinfo_response = requests.get(
                self.facebook_config['userinfo_url'],
                params=userinfo_params,
                timeout=10
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()

            # Standardize user info format
            standardized_info = {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'provider_id': user_info.get('id'),
                'provider': 'facebook'
            }

            # Validate required fields
            if not standardized_info['email']:
                return Result.failure(OAuth2Error("No email address received from Facebook"))

            return Result.success(standardized_info)

        except requests.RequestException as e:
            logger.error("Facebook API request failed: %s", e)
            return Result.failure(OAuth2Error(f"Facebook API error: {e}"))
        except (KeyError, ValueError) as e:
            logger.error("Invalid Facebook API response: %s", e)
            return Result.failure(OAuth2Error(f"Invalid response format: {e}"))