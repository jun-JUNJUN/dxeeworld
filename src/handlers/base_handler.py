"""
ベースハンドラー
"""
import logging
import tornado.web
from ..services.oauth_session_service import OAuthSessionService

logger = logging.getLogger(__name__)


class BaseHandler(tornado.web.RequestHandler):
    """ベースハンドラー - 共通機能を提供"""

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