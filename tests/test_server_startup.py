"""
テストファースト: サーバー起動機能のテスト
"""
import pytest
import tornado.testing
import tornado.web
from src.app import create_app
from src.config import get_app_config


class TestServerStartup(tornado.testing.AsyncHTTPTestCase):
    """サーバー起動とHTTPリクエスト処理のテスト"""

    def get_app(self):
        """テスト用アプリケーションの作成"""
        return create_app()

    def test_server_can_start(self):
        """サーバーが正常に起動できることを確認"""
        app = self.get_app()
        assert app is not None
        assert isinstance(app, tornado.web.Application)

    def test_basic_http_request_handling(self):
        """基本的なHTTPリクエストが処理されることを確認"""
        response = self.fetch('/')
        assert response.code in [200, 404]  # ルートが定義されていれば200、なければ404

    def test_app_configuration(self):
        """アプリケーション設定が正しく取得できることを確認"""
        config = get_app_config()
        assert config is not None
        assert 'debug' in config
        assert 'port' in config

    @tornado.testing.gen_test
    async def test_server_can_handle_async_requests(self):
        """非同期リクエストが処理できることを確認"""
        response = await self.fetch('/', method='GET', raise_error=False)
        assert response is not None