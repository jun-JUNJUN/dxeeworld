"""
LocaleDetectionServiceのユニットテスト
"""
import pytest
from unittest.mock import Mock
from src.services.locale_detection_service import (
    LocaleDetectionService,
    LocaleDetectionError,
)


class TestLocaleDetectionService:
    """LocaleDetectionServiceのテストクラス"""

    @pytest.fixture
    def service(self) -> LocaleDetectionService:
        """LocaleDetectionServiceのインスタンスを作成（モック使用）"""
        service = LocaleDetectionService()
        # モックリーダーを設定（GeoIP2データベース不要）
        service.reader = Mock()
        return service

    @pytest.mark.asyncio
    async def test_initialize_with_invalid_path(self) -> None:
        """無効なパスでの初期化が失敗することを確認"""
        service = LocaleDetectionService(geoip_db_path="invalid/path.mmdb")
        result = await service.initialize()

        assert not result.is_success
        assert isinstance(result.error, LocaleDetectionError)

    def test_map_country_to_language_japanese(self, service: LocaleDetectionService) -> None:
        """日本の国コードから日本語を検出"""
        language = service.map_country_to_language("JP")
        assert language == "ja"

    def test_map_country_to_language_chinese(self, service: LocaleDetectionService) -> None:
        """中国語圏の国コードから中国語を検出"""
        assert service.map_country_to_language("CN") == "zh"
        assert service.map_country_to_language("HK") == "zh"
        assert service.map_country_to_language("TW") == "zh"
        assert service.map_country_to_language("SG") == "zh"

    def test_map_country_to_language_english(self, service: LocaleDetectionService) -> None:
        """その他地域の国コードから英語を検出"""
        assert service.map_country_to_language("US") == "en"
        assert service.map_country_to_language("GB") == "en"
        assert service.map_country_to_language("FR") == "en"
        assert service.map_country_to_language("DE") == "en"
        assert service.map_country_to_language("BR") == "en"

    def test_validate_language_code_valid(self, service: LocaleDetectionService) -> None:
        """有効な言語コードの検証"""
        assert service.validate_language_code("en") is True
        assert service.validate_language_code("ja") is True
        assert service.validate_language_code("zh") is True

    def test_validate_language_code_invalid(self, service: LocaleDetectionService) -> None:
        """無効な言語コードの検証"""
        assert service.validate_language_code("fr") is False
        assert service.validate_language_code("es") is False
        assert service.validate_language_code("<script>") is False
        assert service.validate_language_code("") is False
        assert service.validate_language_code("invalid") is False

    def test_detect_locale_from_private_ip(self, service: LocaleDetectionService) -> None:
        """プライベートIPアドレスでのロケール検出（デフォルト英語を返す）"""
        result = service.detect_locale_from_ip("127.0.0.1")

        assert result.is_success
        assert result.data == "en"  # ローカルIPはデフォルト英語

    def test_detect_locale_from_invalid_ip(self, service: LocaleDetectionService) -> None:
        """無効なIPアドレスでのロケール検出（デフォルト英語を返す）"""
        result = service.detect_locale_from_ip("invalid-ip")

        assert result.is_success
        assert result.data == "en"  # エラー時もデフォルト英語で継続

    @pytest.mark.asyncio
    async def test_close_service(self) -> None:
        """サービスのクローズ処理が正常に動作することを確認"""
        service = LocaleDetectionService()
        service.reader = Mock()
        service.reader.close = Mock()

        await service.close()

        # closeメソッドが呼ばれたことを確認
        service.reader.close.assert_called_once()
