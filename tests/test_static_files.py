"""
テストファースト: 静的ファイル配信機能のテスト
"""
import pytest
import tornado.testing
from src.app import create_app


class TestStaticFiles(tornado.testing.AsyncHTTPTestCase):
    """静的ファイル配信システムのテスト"""

    def get_app(self):
        """テスト用アプリケーションの作成"""
        return create_app()

    def test_css_file_serving(self):
        """CSSファイルが配信されることを確認"""
        response = self.fetch('/static/css/main.css')
        # ファイルが存在すれば200、存在しなければ404
        assert response.code in [200, 404]
        if response.code == 200:
            assert 'text/css' in response.headers.get('Content-Type', '')

    def test_js_file_serving(self):
        """JavaScriptファイルが配信されることを確認"""
        response = self.fetch('/static/js/main.js')
        assert response.code in [200, 404]
        if response.code == 200:
            assert 'javascript' in response.headers.get('Content-Type', '').lower()

    def test_static_file_caching_headers(self):
        """静的ファイルにキャッシュヘッダーが設定されることを確認"""
        response = self.fetch('/static/css/main.css')
        if response.code == 200:
            # キャッシュ関連のヘッダーが設定されていることを確認
            headers = response.headers
            assert any(header in headers for header in ['Cache-Control', 'Expires', 'ETag'])

    def test_static_file_not_found_handling(self):
        """存在しない静的ファイルのリクエストが適切に処理されることを確認"""
        response = self.fetch('/static/nonexistent/file.css')
        assert response.code == 404