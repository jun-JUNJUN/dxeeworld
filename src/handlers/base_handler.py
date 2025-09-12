"""
ベースハンドラー
"""
import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    """ベースハンドラー - 共通機能を提供"""
    
    def set_default_headers(self):
        """デフォルトヘッダーを設定"""
        self.set_header("Content-Type", "text/html; charset=UTF-8")
    
    def write_error(self, status_code, **kwargs):
        """エラーレスポンスをカスタマイズ"""
        self.write(f"<html><body><h1>Error {status_code}</h1></body></html>")