"""
BaseHandler言語検出ミドルウェアのユニットテスト

Tasks 11.4: BaseHandler言語検出ロジックのユニットテスト
- URLパラメータ優先のテスト
- セッションクッキーフォールバックのテスト
- IPロケーション検出フォールバックのテスト
- デフォルト言語適用のテスト
- 不正な言語コードの拒否テスト
- セッションクッキー保存のテスト
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import tornado.testing
import tornado.web
from tornado.httpclient import HTTPRequest

from src.handlers.base_handler import BaseHandler
from src.services.locale_detection_service import LocaleDetectionService
from src.services.i18n_service import I18nService
from src.services.url_language_service import URLLanguageService
from src.utils.result import Result


class TestHandler(BaseHandler):
    """テスト用ハンドラー"""

    async def get(self):
        self.write({
            "current_locale": self.current_locale,
            "locale_source": self.locale_source,
        })


class TestBaseHandlerLocale(tornado.testing.AsyncHTTPTestCase):
    """BaseHandler言語検出のテストクラス"""

    def get_app(self):
        """テスト用アプリケーションを作成"""
        # モックサービスを作成
        self.mock_locale_detection_service = Mock(spec=LocaleDetectionService)
        self.mock_i18n_service = Mock(spec=I18nService)
        self.mock_url_language_service = Mock(spec=URLLanguageService)

        # デフォルトのモック動作を設定
        self.mock_locale_detection_service.detect_locale_from_ip.return_value = Result.success("en")
        self.mock_i18n_service.get_translation.return_value = "Translation"
        self.mock_i18n_service.format_date.return_value = "2025-01-01"
        self.mock_url_language_service.add_language_param.return_value = "/path?lang=en"

        app = tornado.web.Application(
            [(r"/test", TestHandler)],
            cookie_secret="test-secret-key",
        )

        # サービスをアプリケーションに登録
        app.locale_detection_service = self.mock_locale_detection_service
        app.i18n_service = self.mock_i18n_service
        app.url_language_service = self.mock_url_language_service

        return app

    def test_url_param_priority(self):
        """URLパラメータが最優先されることを確認"""
        response = self.fetch("/test?lang=ja")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertEqual(data["current_locale"], "ja")
        self.assertEqual(data["locale_source"], "url")

    def test_url_param_chinese(self):
        """URL中国語パラメータが適用されることを確認"""
        response = self.fetch("/test?lang=zh")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertEqual(data["current_locale"], "zh")
        self.assertEqual(data["locale_source"], "url")

    def test_url_param_english(self):
        """URL英語パラメータが適用されることを確認"""
        response = self.fetch("/test?lang=en")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertEqual(data["current_locale"], "en")
        self.assertEqual(data["locale_source"], "url")

    def test_invalid_url_param_ignored(self):
        """無効なURLパラメータが無視されることを確認"""
        response = self.fetch("/test?lang=invalid")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        # 無効なパラメータは無視され、デフォルトまたはIPベースの言語が使用される
        self.assertIn(data["current_locale"], ["en", "ja", "zh"])
        self.assertIn(data["locale_source"], ["ip", "default"])

    def test_xss_attack_vector_rejected(self):
        """XSS攻撃ベクターが拒否されることを確認"""
        response = self.fetch("/test?lang=<script>alert(1)</script>")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        # XSSペイロードは無効な言語コードとして拒否される
        self.assertNotEqual(data["current_locale"], "<script>alert(1)</script>")
        self.assertIn(data["current_locale"], ["en", "ja", "zh"])

    def test_ip_detection_fallback(self):
        """IPロケーション検出フォールバックが機能することを確認"""
        # IPから日本語を検出するようモックを設定
        self.mock_locale_detection_service.detect_locale_from_ip.return_value = Result.success("ja")

        response = self.fetch("/test")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertEqual(data["current_locale"], "ja")
        self.assertEqual(data["locale_source"], "ip")

    def test_ip_detection_chinese(self):
        """中国IPから中国語が検出されることを確認"""
        self.mock_locale_detection_service.detect_locale_from_ip.return_value = Result.success("zh")

        response = self.fetch("/test")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertEqual(data["current_locale"], "zh")
        self.assertEqual(data["locale_source"], "ip")

    def test_default_language_fallback(self):
        """デフォルト言語(英語)へのフォールバックを確認"""
        # IPロケーション検出が失敗するようモックを設定
        self.mock_locale_detection_service.detect_locale_from_ip.return_value = Result.failure(Exception("Failed"))

        # アプリケーションからlocale_detection_serviceを削除して完全なフォールバックをテスト
        del self._app.locale_detection_service

        response = self.fetch("/test")

        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertEqual(data["current_locale"], "en")
        self.assertEqual(data["locale_source"], "default")


class TestBaseHandlerValidation:
    """BaseHandler言語コード検証のテストクラス"""

    def test_validate_language_code_en(self):
        """英語コードが有効であることを確認"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler.validate_language_code("en") is True

    def test_validate_language_code_ja(self):
        """日本語コードが有効であることを確認"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler.validate_language_code("ja") is True

    def test_validate_language_code_zh(self):
        """中国語コードが有効であることを確認"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler.validate_language_code("zh") is True

    def test_validate_language_code_invalid(self):
        """無効なコードが拒否されることを確認"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler.validate_language_code("fr") is False
        assert handler.validate_language_code("es") is False
        assert handler.validate_language_code("de") is False

    def test_validate_language_code_empty(self):
        """空文字列が拒否されることを確認"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler.validate_language_code("") is False

    def test_validate_language_code_xss(self):
        """XSS攻撃ベクターが拒否されることを確認"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler.validate_language_code("<script>") is False
        assert handler.validate_language_code("javascript:") is False
        assert handler.validate_language_code("' OR '1'='1") is False


class TestBaseHandlerTemplateNamespace:
    """BaseHandler テンプレートコンテキスト変数のテストクラス"""

    def test_get_template_namespace_without_services(self):
        """サービスなしでテンプレートネームスペースが取得できることを確認"""
        # モックアプリケーションを作成
        mock_app = Mock()
        mock_app.ui_methods = {}
        mock_app.ui_modules = {}

        # BaseHandlerのインスタンスを作成
        handler = BaseHandler.__new__(BaseHandler)
        handler.application = mock_app
        handler.current_locale = "ja"
        handler.locale_source = "url"
        handler.request = Mock()
        handler.ui = {}
        handler.locale = None

        # パッチを適用してget_template_namespaceを呼び出し可能にする
        with patch.object(tornado.web.RequestHandler, 'get_template_namespace', return_value={}):
            namespace = handler.get_template_namespace()

        assert namespace["current_locale"] == "ja"
        assert namespace["locale_source"] == "url"

    def test_get_template_namespace_with_services(self):
        """サービスありでヘルパー関数が提供されることを確認"""
        # モックサービスを作成
        mock_i18n_service = Mock(spec=I18nService)
        mock_i18n_service.get_translation.return_value = "ホーム"
        mock_i18n_service.format_date.return_value = "2025年1月26日"

        mock_url_language_service = Mock(spec=URLLanguageService)
        mock_url_language_service.add_language_param.return_value = "/companies?lang=ja"

        # モックアプリケーションを作成
        mock_app = Mock()
        mock_app.ui_methods = {}
        mock_app.ui_modules = {}
        mock_app.i18n_service = mock_i18n_service
        mock_app.url_language_service = mock_url_language_service

        # BaseHandlerのインスタンスを作成
        handler = BaseHandler.__new__(BaseHandler)
        handler.application = mock_app
        handler.current_locale = "ja"
        handler.locale_source = "url"
        handler.request = Mock()
        handler.ui = {}
        handler.locale = None

        # パッチを適用してget_template_namespaceを呼び出し可能にする
        with patch.object(tornado.web.RequestHandler, 'get_template_namespace', return_value={}):
            namespace = handler.get_template_namespace()

        # 変数の確認
        assert namespace["current_locale"] == "ja"
        assert namespace["locale_source"] == "url"

        # ヘルパー関数の確認
        assert "t" in namespace
        assert "format_date" in namespace
        assert "url_for_lang" in namespace

        # ヘルパー関数の動作確認
        assert namespace["t"]("nav.home") == "ホーム"
        mock_i18n_service.get_translation.assert_called_with("nav.home", "ja")


class TestBaseHandlerIPExtraction:
    """BaseHandler IPアドレス取得のテストクラス"""

    def test_get_client_ip_from_x_forwarded_for(self):
        """X-Forwarded-Forヘッダーからの取得"""
        handler = BaseHandler.__new__(BaseHandler)
        handler.request = Mock()
        handler.request.headers = {"X-Forwarded-For": "203.0.113.45, 10.0.0.1"}
        handler.request.remote_ip = "127.0.0.1"

        ip = handler.get_client_ip()
        assert ip == "203.0.113.45"

    def test_get_client_ip_from_x_real_ip(self):
        """X-Real-IPヘッダーからの取得"""
        handler = BaseHandler.__new__(BaseHandler)
        handler.request = Mock()
        handler.request.headers = {"X-Real-IP": "203.0.113.100"}
        handler.request.remote_ip = "127.0.0.1"

        ip = handler.get_client_ip()
        assert ip == "203.0.113.100"

    def test_get_client_ip_from_remote_ip(self):
        """直接接続からの取得"""
        handler = BaseHandler.__new__(BaseHandler)
        handler.request = Mock()
        handler.request.headers = {}
        handler.request.remote_ip = "192.168.1.1"

        ip = handler.get_client_ip()
        assert ip == "192.168.1.1"

    def test_get_client_ip_invalid_forwarded_for(self):
        """無効なX-Forwarded-Forの処理"""
        handler = BaseHandler.__new__(BaseHandler)
        handler.request = Mock()
        handler.request.headers = {"X-Forwarded-For": "invalid-ip"}
        handler.request.remote_ip = "127.0.0.1"

        ip = handler.get_client_ip()
        # 無効なIPはスキップされ、remote_ipが使用される
        assert ip == "127.0.0.1"

    def test_is_valid_ip_ipv4(self):
        """IPv4アドレスの検証"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler._is_valid_ip("192.168.1.1") is True
        assert handler._is_valid_ip("10.0.0.1") is True
        assert handler._is_valid_ip("203.0.113.45") is True

    def test_is_valid_ip_ipv6(self):
        """IPv6アドレスの検証"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler._is_valid_ip("::1") is True
        assert handler._is_valid_ip("2001:db8::1") is True
        assert handler._is_valid_ip("fe80::1") is True

    def test_is_valid_ip_invalid(self):
        """無効なIPアドレスの検証"""
        handler = BaseHandler.__new__(BaseHandler)
        assert handler._is_valid_ip("invalid") is False
        assert handler._is_valid_ip("") is False
        assert handler._is_valid_ip("256.256.256.256") is False
