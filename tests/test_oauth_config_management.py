"""
Test Environment Configuration Management for OAuth
Task 1.2: 環境設定とコンフィギュレーション管理の実装
"""
import pytest
import os
from unittest.mock import patch, mock_open
from src.config import OAuthConfig
from src.services.oauth_config_service import OAuthConfigService


class TestOAuthConfigManagement:
    """Test OAuth configuration management"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing"""
        env_vars = {
            # Google OAuth settings
            'GOOGLE_CLIENT_ID': 'test_google_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
            'GOOGLE_REDIRECT_URI': 'https://localhost:8202/auth/google/callback',

            # Facebook OAuth settings
            'FACEBOOK_APP_ID': 'test_facebook_app_id',
            'FACEBOOK_APP_SECRET': 'test_facebook_app_secret',
            'FACEBOOK_REDIRECT_URI': 'https://localhost:8202/auth/facebook/callback',

            # SMTP settings
            'SMTP_HOST': 'smtp.gmail.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password',
            'SMTP_USE_TLS': 'True',

            # Access control settings
            'ACCESS_CONTROL_RULES': '/reviews/details,user,admin,ally;/reviews/submit,user,admin',

            # Encryption settings
            'EMAIL_ENCRYPTION_KEY': 'test_encryption_key_32_bytes_long!',
            'EMAIL_HASH_SALT': 'test_salt_for_hashing'
        }
        return env_vars

    @pytest.fixture
    def oauth_config_service(self, mock_env_vars):
        """OAuth config service fixture"""
        with patch.dict(os.environ, mock_env_vars):
            return OAuthConfigService()

    def test_oauth_config_class_initialization(self, mock_env_vars):
        """Test OAuthConfig class initializes with environment variables"""
        # RED: テスト先行 - OAuthConfigクラスがまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            config = OAuthConfig()

            # Google OAuth settings
            assert config.GOOGLE_CLIENT_ID == 'test_google_client_id'
            assert config.GOOGLE_CLIENT_SECRET == 'test_google_client_secret'
            assert config.GOOGLE_REDIRECT_URI == 'https://localhost:8202/auth/google/callback'

            # Facebook OAuth settings
            assert config.FACEBOOK_APP_ID == 'test_facebook_app_id'
            assert config.FACEBOOK_APP_SECRET == 'test_facebook_app_secret'
            assert config.FACEBOOK_REDIRECT_URI == 'https://localhost:8202/auth/facebook/callback'

    def test_smtp_config_validation(self, mock_env_vars):
        """Test SMTP configuration validation"""
        # RED: テスト先行 - SMTP設定バリデーションがまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            config = OAuthConfig()

            assert config.SMTP_HOST == 'smtp.gmail.com'
            assert config.SMTP_PORT == 587  # 数値に変換されることを確認
            assert config.SMTP_USERNAME == 'test@example.com'
            assert config.SMTP_PASSWORD == 'test_password'
            assert config.SMTP_USE_TLS is True  # ブール値に変換されることを確認

    def test_access_control_rules_parsing(self, oauth_config_service, mock_env_vars):
        """Test access control rules parsing from environment"""
        # RED: テスト先行 - アクセス制御ルール解析がまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            rules = oauth_config_service.parse_access_control_rules()

            expected_rules = [
                {
                    'url_pattern': '/reviews/details',
                    'required_permissions': ['user', 'admin', 'ally']
                },
                {
                    'url_pattern': '/reviews/submit',
                    'required_permissions': ['user', 'admin']
                }
            ]

            assert rules == expected_rules

    def test_encryption_key_validation(self, oauth_config_service, mock_env_vars):
        """Test encryption key validation and format"""
        # RED: テスト先行 - 暗号化キーバリデーションがまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            is_valid = oauth_config_service.validate_encryption_key()

            # 32バイト以上のキーが必要
            assert is_valid is True

    def test_encryption_key_too_short_validation(self, mock_env_vars):
        """Test encryption key validation fails for short keys"""
        # RED: テスト先行 - 短い暗号化キーの検証がまだ実装されていない

        short_key_env = dict(mock_env_vars)
        short_key_env['EMAIL_ENCRYPTION_KEY'] = 'short_key'

        with patch.dict(os.environ, short_key_env):
            service = OAuthConfigService()
            with pytest.raises(ValueError, match="Encryption key must be at least 32 bytes"):
                service.validate_encryption_key()

    def test_required_oauth_config_missing_google_client_id(self):
        """Test error when required Google OAuth config is missing"""
        # RED: テスト先行 - 必須設定の検証がまだ実装されていない

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID is required"):
                OAuthConfig()

    def test_required_oauth_config_missing_smtp_host(self):
        """Test error when required SMTP config is missing"""
        # RED: テスト先行 - SMTP必須設定の検証がまだ実装されていない

        incomplete_env = {
            'GOOGLE_CLIENT_ID': 'test_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_client_secret',
            # SMTP_HOST missing
        }
        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValueError, match="SMTP_HOST is required"):
                OAuthConfig()

    def test_config_service_get_google_oauth_config(self, oauth_config_service, mock_env_vars):
        """Test getting Google OAuth configuration"""
        # RED: テスト先行 - Google OAuth設定取得がまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            google_config = oauth_config_service.get_google_oauth_config()

            expected_config = {
                'client_id': 'test_google_client_id',
                'client_secret': 'test_google_client_secret',
                'redirect_uri': 'https://localhost:8202/auth/google/callback'
            }

            assert google_config == expected_config

    def test_config_service_get_facebook_oauth_config(self, oauth_config_service, mock_env_vars):
        """Test getting Facebook OAuth configuration"""
        # RED: テスト先行 - Facebook OAuth設定取得がまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            facebook_config = oauth_config_service.get_facebook_oauth_config()

            expected_config = {
                'app_id': 'test_facebook_app_id',
                'app_secret': 'test_facebook_app_secret',
                'redirect_uri': 'https://localhost:8202/auth/facebook/callback'
            }

            assert facebook_config == expected_config

    def test_config_service_get_smtp_config(self, oauth_config_service, mock_env_vars):
        """Test getting SMTP configuration"""
        # RED: テスト先行 - SMTP設定取得がまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            smtp_config = oauth_config_service.get_smtp_config()

            expected_config = {
                'host': 'smtp.gmail.com',
                'port': 587,
                'username': 'test@example.com',
                'password': 'test_password',
                'use_tls': True
            }

            assert smtp_config == expected_config

    def test_config_service_get_encryption_config(self, oauth_config_service, mock_env_vars):
        """Test getting encryption configuration"""
        # RED: テスト先行 - 暗号化設定取得がまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            encryption_config = oauth_config_service.get_encryption_config()

            expected_config = {
                'encryption_key': 'test_encryption_key_32_bytes_long!',
                'hash_salt': 'test_salt_for_hashing'
            }

            assert encryption_config == expected_config

    def test_access_control_rules_empty_environment(self, mock_env_vars):
        """Test access control rules with empty environment"""
        # RED: テスト先行 - 空の環境変数での処理がまだ実装されていない

        empty_env = dict(mock_env_vars)
        empty_env['ACCESS_CONTROL_RULES'] = ''

        with patch.dict(os.environ, empty_env):
            service = OAuthConfigService()
            rules = service.parse_access_control_rules()

            # 空の場合はデフォルトルールを返す
            assert rules == []

    def test_config_refresh_capability(self, oauth_config_service, mock_env_vars):
        """Test configuration refresh capability"""
        # RED: テスト先行 - 設定再読み込み機能がまだ実装されていない

        with patch.dict(os.environ, mock_env_vars):
            # 初期設定を読み込み
            initial_config = oauth_config_service.get_google_oauth_config()

            # 環境変数を変更
            new_env = dict(mock_env_vars)
            new_env['GOOGLE_CLIENT_ID'] = 'updated_client_id'

            with patch.dict(os.environ, new_env):
                # 設定を再読み込み
                oauth_config_service.refresh_config()
                refreshed_config = oauth_config_service.get_google_oauth_config()

                assert refreshed_config['client_id'] == 'updated_client_id'
                assert refreshed_config['client_id'] != initial_config['client_id']

    def test_dotenv_file_loading(self, oauth_config_service):
        """Test loading configuration from .env file"""
        # RED: テスト先行 - .envファイル読み込み機能がまだ実装されていない

        dotenv_content = """
GOOGLE_CLIENT_ID=dotenv_google_client_id
GOOGLE_CLIENT_SECRET=dotenv_google_client_secret
SMTP_HOST=dotenv_smtp_host
"""

        with patch("builtins.open", mock_open(read_data=dotenv_content)):
            with patch("os.path.exists", return_value=True):
                oauth_config_service.load_dotenv_config('.env')

                # .envファイルから読み込まれた設定が使用されることを確認
                google_config = oauth_config_service.get_google_oauth_config()
                assert google_config['client_id'] == 'dotenv_google_client_id'