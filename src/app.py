"""
メインアプリケーション
"""
import os
import logging
import tornado.web
import tornado.ioloop
from tornado.options import define, options
from .config import get_app_config
from .handlers.home_handler import HomeHandler
from .handlers.health_handler import HealthCheckHandler
from .handlers.auth_handler import RegisterHandler, LoginHandler, LogoutHandler

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Tornadoアプリケーションを作成"""
    config = get_app_config()
    
    # 静的ファイルディレクトリを作成（存在しない場合）
    static_path = config['static_path']
    os.makedirs(static_path, exist_ok=True)
    os.makedirs(os.path.join(static_path, 'css'), exist_ok=True)
    os.makedirs(os.path.join(static_path, 'js'), exist_ok=True)
    
    # URLルーティング設定
    handlers = [
        (r"/", HomeHandler),
        (r"/register", RegisterHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/health", HealthCheckHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {
            "path": static_path,
            "default_filename": None
        }),
    ]
    
    # アプリケーション設定
    settings = {
        "debug": config['debug'],
        "static_path": static_path,
        "static_url_prefix": "/static/",
        "autoreload": config['debug'],
        # 静的ファイルのキャッシュ設定
        "static_hash_cache": not config['debug'],
        # セキュアクッキー用シークレット
        "cookie_secret": "your-secret-key-here-change-in-production",
    }
    
    app = tornado.web.Application(handlers, **settings)
    logger.info("Tornadoアプリケーションが作成されました")
    
    return app


def main():
    """メイン関数 - サーバー起動"""
    config = get_app_config()
    
    # コマンドライン引数の定義
    define("port", default=config['port'], help="サーバーポート番号")
    define("debug", default=config['debug'], help="デバッグモード")
    
    # アプリケーション作成
    app = create_app()
    
    # サーバー起動
    app.listen(options.port)
    logger.info(f"サーバーが起動しました: http://localhost:{options.port}")
    
    # イベントループ開始
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()