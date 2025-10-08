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
from .handlers.auth_handler import LoginHandler, LogoutHandler
from .handlers.company_handler import (
    CompanyListHandler,
    CompanyDetailHandler,
    CompanyJobsHandler,
    JobsListHandler,
)
from .handlers.review_handler import ReviewListHandler, ReviewCreateHandler, ReviewEditHandler
from .handlers.email_auth_handler import (
    EmailRegistrationHandler,
    EmailVerificationHandler,
    EmailLoginHandler,
    EmailCodeVerificationHandler,
    EmailCodeResendHandler,
)
from .handlers.simple_auth_handler import SimpleLoginHandler, SimpleLogoutHandler

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    """Tornadoアプリケーションを作成"""
    config = get_app_config()

    # 静的ファイルディレクトリを作成（存在しない場合）
    static_path = config["static_path"]
    os.makedirs(static_path, exist_ok=True)
    os.makedirs(os.path.join(static_path, "css"), exist_ok=True)
    os.makedirs(os.path.join(static_path, "js"), exist_ok=True)

    # URLルーティング設定
    handlers = [
        (r"/", HomeHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/auth/login", LoginHandler),  # Alias for /login
        (r"/auth/logout", LogoutHandler),  # Alias for /logout
        (r"/health", HealthCheckHandler),
        (r"/jobs", JobsListHandler),
        (r"/companies", CompanyListHandler),
        (r"/companies/([^/]+)", CompanyDetailHandler),
        (r"/companies/([^/]+)/jobs", CompanyJobsHandler),
        # レビュー関連ルート
        (r"/review", ReviewListHandler),
        (r"/companies/([^/]+)/reviews/new", ReviewCreateHandler),
        (r"/reviews/([^/]+)/edit", ReviewEditHandler),
        # メール認証関連ルート (Task 5.3, 5.4)
        (r"/auth/email/register", EmailRegistrationHandler),
        (r"/auth/email/verify", EmailVerificationHandler),
        (r"/auth/email/login", EmailLoginHandler),
        (r"/auth/email/verify-code", EmailCodeVerificationHandler),
        (r"/auth/email/resend-code", EmailCodeResendHandler),
        # 簡単認証ルート（テスト用）
        (r"/simple-login", SimpleLoginHandler),
        (r"/simple-logout", SimpleLogoutHandler),
        (
            r"/static/(.*)",
            tornado.web.StaticFileHandler,
            {"path": static_path, "default_filename": None},
        ),
    ]

    # テンプレートディレクトリを作成（存在しない場合）
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    os.makedirs(template_path, exist_ok=True)

    # アプリケーション設定
    settings = {
        "debug": config["debug"],
        "static_path": static_path,
        "static_url_prefix": "/static/",
        "template_path": template_path,
        "autoreload": config["debug"],
        "compiled_template_cache": False,  # テンプレートキャッシュを無効化
        # 静的ファイルのキャッシュ設定
        "static_hash_cache": not config["debug"],
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
    define("port", default=config["port"], help="サーバーポート番号")
    define("debug", default=config["debug"], help="デバッグモード")

    # アプリケーション作成
    app = create_app()

    # サーバー起動
    app.listen(options.port)
    logger.info(f"サーバーが起動しました: http://localhost:{options.port}")

    # イベントループ開始
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
