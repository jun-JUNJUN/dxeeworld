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
from .handlers.user_info_handler import UserInfoHandler
from .handlers.review_detail_handler import ReviewDetailHandler
from .handlers.category_review_list_handler import CategoryReviewListHandler
from .database import get_db_service
from .services.review_anonymization_service import ReviewAnonymizationService
from .services.locale_detection_service import LocaleDetectionService
from .services.i18n_service import I18nService
from .services.url_language_service import URLLanguageService

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def initialize_i18n_services():
    """多言語サービスの初期化（非同期）"""
    # LocaleDetectionServiceの初期化
    locale_detection_service = LocaleDetectionService()
    init_result = await locale_detection_service.initialize()
    if not init_result.is_success:
        logger.warning(
            "GeoIP2データベースの初期化に失敗しました。デフォルト言語(en)で動作します。"
        )

    # I18nServiceの初期化
    i18n_service = I18nService()
    load_result = await i18n_service.load_translations()
    if not load_result.is_success:
        logger.error("翻訳データの読み込みに失敗しました: %s", load_result.error)

    # URLLanguageServiceの初期化
    url_language_service = URLLanguageService(base_domain="localhost")

    return locale_detection_service, i18n_service, url_language_service


def create_app():
    """Tornadoアプリケーションを作成"""
    config = get_app_config()

    # 静的ファイルディレクトリを作成（存在しない場合）
    static_path = config["static_path"]
    os.makedirs(static_path, exist_ok=True)
    os.makedirs(os.path.join(static_path, "css"), exist_ok=True)
    os.makedirs(os.path.join(static_path, "js"), exist_ok=True)

    # i18nディレクトリを作成（存在しない場合）
    i18n_path = os.path.join(static_path, "i18n")
    os.makedirs(i18n_path, exist_ok=True)

    # geoディレクトリを作成（存在しない場合）
    geo_path = os.path.join(static_path, "geo")
    os.makedirs(geo_path, exist_ok=True)

    # サービスのインスタンス作成
    db_service = get_db_service()
    anonymization_service = ReviewAnonymizationService(salt=os.getenv("ANONYMIZATION_SALT", ""))

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
        # レビュー詳細ページ (Task 5.1)
        (r"/companies/([^/]+)/reviews/by-category/([^/]+)", CategoryReviewListHandler, {
            "db_service": db_service,
            "anonymization_service": anonymization_service
        }),
        (r"/companies/([^/]+)/reviews/([^/]+)", ReviewDetailHandler, {
            "db_service": db_service,
            "anonymization_service": anonymization_service
        }),
        # メール認証関連ルート (Task 5.3, 5.4)
        (r"/auth/email/register", EmailRegistrationHandler),
        (r"/auth/email/verify", EmailVerificationHandler),
        (r"/auth/email/login", EmailLoginHandler),
        (r"/auth/email/verify-code", EmailCodeVerificationHandler),
        (r"/auth/email/resend-code", EmailCodeResendHandler),
        # User info API
        (r"/api/user/info", UserInfoHandler),
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


async def startup_tasks(app):
    """アプリケーション起動時のタスク"""
    # 多言語サービスの初期化
    locale_detection_service, i18n_service, url_language_service = (
        await initialize_i18n_services()
    )

    # アプリケーションにサービスを登録
    app.locale_detection_service = locale_detection_service
    app.i18n_service = i18n_service
    app.url_language_service = url_language_service

    logger.info("多言語サービスの初期化が完了しました")


async def shutdown_tasks(app):
    """アプリケーション終了時のタスク"""
    logger.info("アプリケーションのシャットダウン処理を開始します")

    # GeoIP2リーダーのクローズ
    if hasattr(app, "locale_detection_service"):
        await app.locale_detection_service.close()

    logger.info("アプリケーションのシャットダウン処理が完了しました")


async def shutdown_and_stop(app, io_loop):
    """シャットダウン処理を実行してイベントループを停止"""
    await shutdown_tasks(app)
    io_loop.stop()


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

    # イベントループ取得
    io_loop = tornado.ioloop.IOLoop.current()

    # 起動時タスクを実行
    io_loop.run_sync(lambda: startup_tasks(app))

    # シャットダウンハンドラーの登録
    def shutdown_handler(signum, frame):
        """シグナル受信時のシャットダウン処理"""
        logger.info("シャットダウンシグナルを受信しました")
        io_loop.add_callback_from_signal(lambda: shutdown_and_stop(app, io_loop))

    import signal

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # イベントループ開始
        io_loop.start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterruptを受信しました")
    finally:
        # 確実にクリーンアップを実行
        io_loop.run_sync(lambda: shutdown_tasks(app))


if __name__ == "__main__":
    main()
