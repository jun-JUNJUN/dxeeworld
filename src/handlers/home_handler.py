"""
ホームページハンドラー
"""
from .base_handler import BaseHandler


class HomeHandler(BaseHandler):
    """ホームページハンドラー"""
    
    def get(self):
        """ホームページを表示"""
        self.render("home.html")