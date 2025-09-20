"""
ヘルスチェックハンドラー
"""
from .base_handler import BaseHandler


class HealthCheckHandler(BaseHandler):
    """ヘルスチェックエンドポイント"""
    
    async def get(self):
        """サーバーの健全性をチェック"""
        try:
            # データベース接続チェック（後で実装）
            self.set_header("Content-Type", "application/json")
            self.write({"status": "ok", "service": "dxeeworld"})
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": str(e)})