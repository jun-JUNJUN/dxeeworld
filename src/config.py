"""
アプリケーション設定管理
"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


class Config:
    """アプリケーション設定クラス"""
    
    # サーバー設定
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 8202))
    HOST = os.getenv('HOST', 'localhost')
    
    # MongoDB設定
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'dxeeworld')
    
    # セキュリティ設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'development-secret-key-change-in-production')
    
    # 静的ファイル設定
    STATIC_PATH = os.path.join(os.path.dirname(__file__), '..', 'static')


class OAuthConfig:
    """OAuth認証サービス設定クラス"""

    def __init__(self):
        # Google OAuth設定 (必須)
        self.GOOGLE_CLIENT_ID = self._get_required_env('GOOGLE_CLIENT_ID')
        self.GOOGLE_CLIENT_SECRET = self._get_required_env('GOOGLE_CLIENT_SECRET')
        self.GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'https://localhost:8202/auth/google/callback')

        # Facebook OAuth設定 (必須)
        self.FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
        self.FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
        self.FACEBOOK_REDIRECT_URI = os.getenv('FACEBOOK_REDIRECT_URI', 'https://localhost:8202/auth/facebook/callback')

        # SMTP設定 (必須)
        self.SMTP_HOST = self._get_required_env('SMTP_HOST')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
        self.SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'

        # アクセス制御設定
        self.ACCESS_CONTROL_RULES = os.getenv('ACCESS_CONTROL_RULES', '')

        # 暗号化設定
        self.EMAIL_ENCRYPTION_KEY = os.getenv('EMAIL_ENCRYPTION_KEY', '')
        self.EMAIL_HASH_SALT = os.getenv('EMAIL_HASH_SALT', '')

    def _get_required_env(self, key: str) -> str:
        """必須環境変数を取得"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"{key} is required")
        return value


def get_app_config():
    """アプリケーション設定を取得"""
    return {
        'debug': Config.DEBUG,
        'port': Config.PORT,
        'host': Config.HOST,
        'static_path': Config.STATIC_PATH
    }


def get_database_connection():
    """データベース接続設定を取得"""
    return {
        'uri': Config.MONGODB_URI,
        'db_name': Config.MONGODB_DB_NAME
    }