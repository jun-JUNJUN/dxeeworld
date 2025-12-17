"""
URLLanguageServiceのユニットテスト
"""
import pytest
from src.services.url_language_service import URLLanguageService


class TestURLLanguageService:
    """URLLanguageServiceのテストクラス"""

    @pytest.fixture
    def service(self) -> URLLanguageService:
        """URLLanguageServiceのインスタンスを作成"""
        return URLLanguageService(base_domain="localhost")

    def test_add_language_param_simple(self, service: URLLanguageService) -> None:
        """シンプルなURLに言語パラメータを追加"""
        result = service.add_language_param("/companies", "ja")
        assert result == "/companies?lang=ja"

    def test_add_language_param_with_existing_query(self, service: URLLanguageService) -> None:
        """既存のクエリパラメータがあるURLに言語パラメータを追加"""
        result = service.add_language_param("/reviews?page=2", "en")
        assert "lang=en" in result
        assert "page=2" in result

    def test_add_language_param_multiple_existing_queries(
        self, service: URLLanguageService
    ) -> None:
        """複数の既存クエリパラメータがあるURLに言語パラメータを追加"""
        result = service.add_language_param("/companies?industry=tech&location=tokyo", "zh")
        assert "lang=zh" in result
        assert "industry=tech" in result
        assert "location=tokyo" in result

    def test_update_language_param_simple(self, service: URLLanguageService) -> None:
        """URLの言語パラメータを更新"""
        result = service.update_language_param("/companies?lang=ja", "en")
        assert "lang=en" in result
        assert "lang=ja" not in result

    def test_update_language_param_with_other_queries(
        self, service: URLLanguageService
    ) -> None:
        """他のクエリパラメータがある場合の言語パラメータ更新"""
        result = service.update_language_param("/reviews?page=2&lang=zh", "ja")
        assert "lang=ja" in result
        assert "lang=zh" not in result
        assert "page=2" in result

    def test_extract_language_param_exists(self, service: URLLanguageService) -> None:
        """URLから言語パラメータを抽出（存在する場合）"""
        result = service.extract_language_param("/companies?lang=ja")
        assert result == "ja"

    def test_extract_language_param_not_exists(self, service: URLLanguageService) -> None:
        """URLから言語パラメータを抽出（存在しない場合）"""
        result = service.extract_language_param("/companies")
        assert result is None

    def test_extract_language_param_with_other_queries(
        self, service: URLLanguageService
    ) -> None:
        """他のクエリパラメータがある場合の言語パラメータ抽出"""
        result = service.extract_language_param("/reviews?page=2&lang=en&sort=date")
        assert result == "en"

    def test_is_internal_link_relative_path(self, service: URLLanguageService) -> None:
        """相対パスは内部リンクと判定"""
        assert service.is_internal_link("/companies", "localhost") is True
        assert service.is_internal_link("../about", "localhost") is True
        assert service.is_internal_link("./contact", "localhost") is True

    def test_is_internal_link_absolute_same_domain(self, service: URLLanguageService) -> None:
        """同じドメインの絶対URLは内部リンクと判定"""
        assert service.is_internal_link("http://localhost:8202/companies", "localhost") is True
        assert service.is_internal_link("https://localhost/reviews", "localhost") is True

    def test_is_internal_link_external_domain(self, service: URLLanguageService) -> None:
        """外部ドメインのURLは外部リンクと判定"""
        assert service.is_internal_link("https://google.com", "localhost") is False
        assert service.is_internal_link("http://example.com/page", "localhost") is False

    def test_is_internal_link_javascript_protocol(self, service: URLLanguageService) -> None:
        """javascript:プロトコルは外部リンクと判定"""
        assert service.is_internal_link("javascript:void(0)", "localhost") is False
        assert service.is_internal_link("javascript:alert('test')", "localhost") is False

    def test_is_internal_link_anchor(self, service: URLLanguageService) -> None:
        """アンカーリンクは外部リンクと判定（言語パラメータ不要）"""
        assert service.is_internal_link("#section", "localhost") is False
        assert service.is_internal_link("#top", "localhost") is False

    def test_is_internal_link_mailto(self, service: URLLanguageService) -> None:
        """mailto:プロトコルは外部リンクと判定"""
        assert service.is_internal_link("mailto:test@example.com", "localhost") is False

    def test_should_add_language_param_internal_link(self, service: URLLanguageService) -> None:
        """内部リンクには言語パラメータを付与すべき"""
        assert service.should_add_language_param("/companies") is True
        assert service.should_add_language_param("/reviews?page=2") is True

    def test_should_add_language_param_external_link(self, service: URLLanguageService) -> None:
        """外部リンクには言語パラメータを付与すべきでない"""
        assert service.should_add_language_param("https://google.com") is False
        assert service.should_add_language_param("http://example.com") is False

    def test_should_add_language_param_anchor(self, service: URLLanguageService) -> None:
        """アンカーリンクには言語パラメータを付与すべきでない"""
        assert service.should_add_language_param("#section") is False

    def test_should_add_language_param_javascript(self, service: URLLanguageService) -> None:
        """javascript:プロトコルには言語パラメータを付与すべきでない"""
        assert service.should_add_language_param("javascript:void(0)") is False

    def test_add_language_param_preserves_fragment(self, service: URLLanguageService) -> None:
        """フラグメント（#anchor）を保持したまま言語パラメータを追加"""
        result = service.add_language_param("/companies#top", "ja")
        assert "lang=ja" in result
        assert "#top" in result
