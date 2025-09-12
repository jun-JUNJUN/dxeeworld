"""
ホームページハンドラー
"""
from .base_handler import BaseHandler


class HomeHandler(BaseHandler):
    """ホームページハンドラー"""
    
    def get(self):
        """ホームページを表示"""
        self.write("<html><body><h1>Startup Platform</h1><p>Coming Soon...</p></body></html>")