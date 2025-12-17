"""
ベースハンドラー
"""
import logging
from typing import Literal
import tornado.web
from ..services.oauth_session_service import OAuthSessionService

logger = logging.getLogger(__name__)

# 型定義
LanguageCode = Literal["en", "ja", "zh"]


class BaseHandler(tornado.web.RequestHandler):
    """ベースハンドラー - 共通機能を提供"""

    current_locale: LanguageCode
    locale_source: Literal["url", "session", "ip", "default"]

    async def prepare(self) -> None:
        """
        全リクエスト前に実行されるフック
        言語検出とセッション設定を行う
        """
        await self._detect_and_set_locale()

    async def _detect_and_set_locale(self) -> None:
        """
        言語検出ロジック

        Priority:
            1. URL ?lang= パラメータ
            2. セッションクッキー
            3. IP ロケーション検出
            4. デフォルト言語 (en)
        """
        # 1. URL ?lang= パラメータ確認
        lang_param = self.get_argument("lang", None)
        if lang_param and self.validate_language_code(lang_param):
            self.current_locale = lang_param  # type: ignore
            self.locale_source = "url"
            self.set_secure_cookie("locale", lang_param, expires_days=30)
            return

        # 2. セッションクッキー確認
        cookie_locale = self.get_secure_cookie("locale")
        if cookie_locale:
            locale_str = cookie_locale.decode("utf-8")
            if self.validate_language_code(locale_str):
                self.current_locale = locale_str  # type: ignore
                self.locale_source = "session"
                return

        # 3. IP ロケーション検出
        if hasattr(self.application, "locale_detection_service"):
            client_ip = self.get_client_ip()
            locale_result = self.application.locale_detection_service.detect_locale_from_ip(
                client_ip
            )

            if locale_result.is_success:
                self.current_locale = locale_result.data
                self.locale_source = "ip"
                self.set_secure_cookie("locale", self.current_locale, expires_days=30)
                return

        # 4. デフォルト言語
        self.current_locale = "en"
        self.locale_source = "default"

    def validate_language_code(self, lang_code: str) -> bool:
        """
        言語コードのホワイトリスト検証

        Args:
            lang_code: 検証対象の言語コード

        Returns:
            bool: 'en', 'zh', 'ja' のいずれかの場合 True
        """
        return lang_code in {"en", "ja", "zh"}

    def get_template_namespace(self) -> dict:  # type: ignore
        """
        Jinja2テンプレートに渡すコンテキスト変数

        Returns:
            dict: テンプレート変数
                - current_locale: 現在の言語コード
                - locale_source: 言語検出ソース
                - t: 翻訳関数
                - url_for_lang: URL言語パラメータ関数
                - format_date: 日付フォーマット関数
        """
        namespace = super().get_template_namespace()

        # 言語関連変数とヘルパー関数を追加
        current_locale = getattr(self, "current_locale", "en")
        locale_source = getattr(self, "locale_source", "default")

        namespace.update(
            {
                "current_locale": current_locale,
                "locale_source": locale_source,
            }
        )

        # サービスが利用可能な場合、ヘルパー関数を追加
        if hasattr(self.application, "i18n_service"):
            namespace["t"] = lambda key: self.application.i18n_service.get_translation(
                key, current_locale
            )
            namespace["format_date"] = lambda date: self.application.i18n_service.format_date(
                date, current_locale
            )

        if hasattr(self.application, "url_language_service"):
            namespace["url_for_lang"] = (
                lambda path: self.application.url_language_service.add_language_param(
                    path, current_locale
                )
            )

        return namespace

    def set_default_headers(self):
        """デフォルトヘッダーを設定"""
        self.set_header("Content-Type", "text/html; charset=UTF-8")

    def write_error(self, status_code, **kwargs):
        """エラーレスポンスをカスタマイズ"""
        self.write(f"<html><body><h1>Error {status_code}</h1></body></html>")

    async def get_current_user_id(self):
        """現在のユーザーIDを取得（OAuth セッションベース）"""
        session_id = self.get_secure_cookie("session_id")
        if not session_id:
            return None

        session_id = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
        oauth_session_service = OAuthSessionService()

        # OAuth セッション検証してユーザーID取得
        validation_result = await oauth_session_service.validate_oauth_session(
            session_id,
            self.request.remote_ip
        )

        if not validation_result.is_success:
            logger.warning("Session validation failed: %s", validation_result.error if hasattr(validation_result, 'error') else "Unknown")
            return None

        # identity_id を返す
        return validation_result.data.get('identity_id')

    async def require_authentication(self):
        """認証を要求し、ユーザーIDを返す"""
        user_id = await self.get_current_user_id()
        if not user_id:
            raise tornado.web.HTTPError(401, "Authentication required")
        return user_id

    async def require_authentication_with_redirect(self):
        """認証を要求し、未認証の場合は認証画面にリダイレクト (Task 4.1)"""
        user_id = await self.get_current_user_id()
        if not user_id:
            # 現在のURLを保存してリダイレクト
            return_url = self.request.uri
            import urllib.parse
            # Task 4.1: ログイン/登録選択画面にリダイレクト
            auth_url = f"/login?return_url={urllib.parse.quote(return_url)}"
            self.redirect(auth_url)
            return None
        return user_id

    def get_client_ip(self):
        """クライアントIPアドレスを取得"""
        return (self.request.headers.get('X-Forwarded-For') or
                self.request.headers.get('X-Real-IP') or
                self.request.remote_ip or
                '127.0.0.1')

    def _get_client_ip(self):
        """クライアントIPアドレスを取得（内部メソッド）"""
        return self.get_client_ip()

    def _send_error_response(self, status_code: int, message: str):
        """エラーレスポンスを送信"""
        import json
        self.set_status(status_code)
        if self.request.headers.get('Content-Type', '').startswith('application/json'):
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                'success': False,
                'error': message
            }))
        else:
            self.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>エラー</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }}
                    .error {{ padding: 20px; margin: 20px 0; border-radius: 8px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>エラー</h2>
                    <p>{message}</p>
                </div>
                <p><a href="javascript:history.back()">戻る</a></p>
            </body>
            </html>
            """)

    def _send_success_response(self, data: dict):
        """成功レスポンスを送信"""
        import json
        if self.request.headers.get('Content-Type', '').startswith('application/json'):
            self.set_header('Content-Type', 'application/json')
            response_data = {'success': True}
            response_data.update(data)
            self.write(json.dumps(response_data))
        else:
            message = data.get('message', '処理が完了しました')
            self.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>完了</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }}
                    .success {{ padding: 20px; margin: 20px 0; border-radius: 8px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h2>完了</h2>
                    <p>{message}</p>
                </div>
                <p><a href="/">ホームページに戻る</a></p>
            </body>
            </html>
            """)

    def set_flash_message(self, message: str, category: str = "success"):
        """
        Task 8.1: フラッシュメッセージを設定

        Args:
            message: 表示するメッセージ
            category: メッセージカテゴリー（success, error, warning, info）
        """
        import json
        # フラッシュメッセージをセキュアクッキーに保存（1回限りの表示）
        flash_data = {"message": message, "category": category}
        self.set_secure_cookie("flash_message", json.dumps(flash_data), expires_days=None)

    def get_flash_message(self):
        """
        Task 8.1: フラッシュメッセージを取得して削除

        Returns:
            dict or None: {"message": str, "category": str} または None
        """
        import json
        flash_cookie = self.get_secure_cookie("flash_message")
        if not flash_cookie:
            return None

        try:
            flash_data = json.loads(flash_cookie.decode('utf-8'))
            # クッキーをクリア（1回限りの表示）
            self.clear_cookie("flash_message")
            return flash_data
        except Exception:
            return None