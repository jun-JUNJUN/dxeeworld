"""
基本的なHTTPリクエストハンドラー
"""
import tornado.web
import logging
from .handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class HomeHandler(BaseHandler):
    """ホームページハンドラー"""

    def get(self):
        """ホームページを表示"""
        self.write("<html><body><h1>Startup Platform: Dxee</h1><p>Coming Soon...</p></body></html>")


class HealthCheckHandler(BaseHandler):
    """ヘルスチェックエンドポイント"""

    async def get(self):
        """サーバーの健全性をチェック"""
        try:
            # データベース接続チェック（後で実装）
            self.set_header("Content-Type", "application/json")
            self.write({"status": "ok", "service": "startup-platform"})
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": str(e)})
