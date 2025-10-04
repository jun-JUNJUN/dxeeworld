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