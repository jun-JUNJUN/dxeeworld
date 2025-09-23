"""
OAuth Configuration Service
OAuth認証設定の管理とバリデーション
"""
import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
from ..config import OAuthConfig

logger = logging.getLogger(__name__)


class OAuthConfigService:
    """OAuth configuration management service"""

    def __init__(self):
        self._config = None
        self.load_config()

    def load_config(self):
        """Load OAuth configuration"""
        try:
            self._config = OAuthConfig()
        except ValueError as e:
            logger.error(f"Failed to load OAuth config: {e}")
            raise

    def refresh_config(self):
        """Refresh configuration from environment"""
        self.load_config()

    def get_google_oauth_config(self) -> Dict[str, str]:
        """Get Google OAuth configuration"""
        return {
            'client_id': self._config.GOOGLE_CLIENT_ID,
            'client_secret': self._config.GOOGLE_CLIENT_SECRET,
            'redirect_uri': self._config.GOOGLE_REDIRECT_URI
        }

    def get_facebook_oauth_config(self) -> Dict[str, str]:
        """Get Facebook OAuth configuration"""
        return {
            'app_id': self._config.FACEBOOK_APP_ID,
            'app_secret': self._config.FACEBOOK_APP_SECRET,
            'redirect_uri': self._config.FACEBOOK_REDIRECT_URI
        }

    def get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration"""
        return {
            'host': self._config.SMTP_HOST,
            'port': self._config.SMTP_PORT,
            'username': self._config.SMTP_USERNAME,
            'password': self._config.SMTP_PASSWORD,
            'use_tls': self._config.SMTP_USE_TLS
        }

    def get_encryption_config(self) -> Dict[str, str]:
        """Get encryption configuration"""
        return {
            'encryption_key': self._config.EMAIL_ENCRYPTION_KEY,
            'hash_salt': self._config.EMAIL_HASH_SALT
        }

    def parse_access_control_rules(self) -> List[Dict[str, Any]]:
        """Parse access control rules from environment"""
        rules_str = self._config.ACCESS_CONTROL_RULES
        if not rules_str:
            return []

        rules = []
        # Format: "/path1,perm1,perm2;/path2,perm3,perm4"
        rule_pairs = rules_str.split(';')

        for rule_pair in rule_pairs:
            if not rule_pair.strip():
                continue

            parts = rule_pair.split(',')
            if len(parts) < 2:
                continue

            url_pattern = parts[0].strip()
            required_permissions = [perm.strip() for perm in parts[1:]]

            rules.append({
                'url_pattern': url_pattern,
                'required_permissions': required_permissions
            })

        return rules

    def validate_encryption_key(self) -> bool:
        """Validate encryption key format and length"""
        encryption_key = self._config.EMAIL_ENCRYPTION_KEY
        if not encryption_key:
            raise ValueError("EMAIL_ENCRYPTION_KEY is required")

        # 暗号化キーは最低32バイト必要
        if len(encryption_key.encode('utf-8')) < 32:
            raise ValueError("Encryption key must be at least 32 bytes")

        return True

    def load_dotenv_config(self, dotenv_path: str = '.env'):
        """Load configuration from .env file"""
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path, override=True)
            self.refresh_config()
        else:
            logger.warning(f"Dotenv file not found: {dotenv_path}")

    def validate_all_configs(self) -> Dict[str, bool]:
        """Validate all configuration sections"""
        validation_results = {}

        try:
            # Google OAuth validation
            google_config = self.get_google_oauth_config()
            validation_results['google_oauth'] = bool(
                google_config['client_id'] and google_config['client_secret']
            )
        except Exception as e:
            logger.error(f"Google OAuth validation failed: {e}")
            validation_results['google_oauth'] = False

        try:
            # SMTP validation
            smtp_config = self.get_smtp_config()
            validation_results['smtp'] = bool(
                smtp_config['host'] and smtp_config['port']
            )
        except Exception as e:
            logger.error(f"SMTP validation failed: {e}")
            validation_results['smtp'] = False

        try:
            # Encryption validation
            validation_results['encryption'] = self.validate_encryption_key()
        except Exception as e:
            logger.error(f"Encryption validation failed: {e}")
            validation_results['encryption'] = False

        return validation_results