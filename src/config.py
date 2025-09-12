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
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'startup_platform')
    
    # セキュリティ設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'development-secret-key-change-in-production')
    
    # 静的ファイル設定
    STATIC_PATH = os.path.join(os.path.dirname(__file__), '..', 'static')


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