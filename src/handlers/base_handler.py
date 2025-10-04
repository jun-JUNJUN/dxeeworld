"""
ベースハンドラー
"""
import tornado.web
from ..services.session_service import SessionService


class BaseHandler(tornado.web.RequestHandler):
    """ベースハンドラー - 共通機能を提供"""

    def set_default_headers(self):
        """デフォルトヘッダーを設定"""
        self.set_header("Content-Type", "text/html; charset=UTF-8")

    def write_error(self, status_code, **kwargs):
        """エラーレスポンスをカスタマイズ"""
        self.write(f"<html><body><h1>Error {status_code}</h1></body></html>")

    async def get_current_user_id(self):
        """現在のユーザーIDを取得（セッションベース）"""
        session_id = self.get_secure_cookie("session_id")
        if not session_id:
            return None

        session_id = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
        session_service = SessionService()

        # セッション検証してユーザーID取得
        user_result = await session_service.get_current_user_from_session(session_id)
        if not user_result.is_success:
            return None

        return user_result.data

    async def require_authentication(self):
        """認証を要求し、ユーザーIDを返す"""
        user_id = await self.get_current_user_id()
        if not user_id:
            raise tornado.web.HTTPError(401, "Authentication required")
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