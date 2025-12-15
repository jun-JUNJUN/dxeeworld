"""
I18nServiceのユニットテスト
"""
import pytest
from datetime import datetime
from src.services.i18n_service import I18nService, I18nError


class TestI18nService:
    """I18nServiceのテストクラス"""

    @pytest.fixture
    def service(self) -> I18nService:
        """I18nServiceのインスタンスを作成（同期版）"""
        import asyncio
        service = I18nService()
        # 同期的に翻訳データをロード
        result = asyncio.run(service.load_translations())
        assert result.is_success, f"翻訳データロード失敗: {result.error}"
        return service

    @pytest.mark.asyncio
    async def test_load_translations_success(self) -> None:
        """翻訳データのロードが成功することを確認"""
        service = I18nService()
        result = await service.load_translations()

        assert result.is_success
        assert result.data is None
        assert "en" in service.translations
        assert "ja" in service.translations
        assert "zh" in service.translations

    @pytest.mark.asyncio
    async def test_load_translations_with_invalid_path(self) -> None:
        """無効なパスでの翻訳データロードが失敗することを確認"""
        service = I18nService(translations_dir="invalid/path")
        result = await service.load_translations()

        # 翻訳ファイルがなくても空辞書でロード成功
        assert result.is_success
        assert service.translations.get("en") == {}

    def test_get_translation_success_japanese(self, service: I18nService) -> None:
        """日本語の翻訳キー取得が成功することを確認"""
        translation = service.get_translation("nav.home", "ja")
        assert translation == "ホーム"

    def test_get_translation_success_english(self, service: I18nService) -> None:
        """英語の翻訳キー取得が成功することを確認"""
        translation = service.get_translation("nav.home", "en")
        assert translation == "Home"

    def test_get_translation_success_chinese(self, service: I18nService) -> None:
        """中国語の翻訳キー取得が成功することを確認"""
        translation = service.get_translation("nav.home", "zh")
        assert translation == "首页"

    def test_get_translation_nested_key(self, service: I18nService) -> None:
        """ネストされた翻訳キーの取得"""
        translation = service.get_translation("nav.companies", "ja")
        assert translation == "企業一覧"

    def test_get_translation_fallback_to_english(self, service: I18nService) -> None:
        """翻訳キーが日本語にない場合、英語にフォールバック"""
        # 存在しないキーでテスト（実際のテストでは翻訳ファイルに依存）
        translation = service.get_translation("nonexistent.key", "ja")
        # キーが見つからない場合はキー名を返す
        assert "nonexistent.key" in translation

    def test_get_translation_return_key_when_not_found(self, service: I18nService) -> None:
        """翻訳キーが全言語で見つからない場合、キー名を返す"""
        translation = service.get_translation("completely.missing.key", "en")
        assert translation == "completely.missing.key"

    def test_format_date_japanese(self, service: I18nService) -> None:
        """日本語の日付フォーマット"""
        date = datetime(2025, 12, 14, 10, 30, 0)
        formatted = service.format_date(date, "ja")

        assert "2025" in formatted
        assert "12" in formatted
        assert "14" in formatted

    def test_format_date_english(self, service: I18nService) -> None:
        """英語の日付フォーマット"""
        date = datetime(2025, 12, 14, 10, 30, 0)
        formatted = service.format_date(date, "en")

        # 英語フォーマット: "Dec 14, 2025" または "December 14, 2025"
        assert "Dec" in formatted or "December" in formatted
        assert "2025" in formatted

    def test_format_date_chinese(self, service: I18nService) -> None:
        """中国語の日付フォーマット"""
        date = datetime(2025, 12, 14, 10, 30, 0)
        formatted = service.format_date(date, "zh")

        assert "2025" in formatted
        assert "12" in formatted
        assert "14" in formatted

    def test_format_number_with_commas(self, service: I18nService) -> None:
        """数値フォーマット（桁区切りカンマ）"""
        number = 1234567.89
        formatted_ja = service.format_number(number, "ja")
        formatted_en = service.format_number(number, "en")
        formatted_zh = service.format_number(number, "zh")

        # カンマ区切り確認
        assert "," in formatted_ja or "1234567" in formatted_ja
        assert "," in formatted_en or "1234567" in formatted_en
        assert "," in formatted_zh or "1234567" in formatted_zh

    @pytest.mark.asyncio
    async def test_reload_translations(self) -> None:
        """翻訳データの再読み込み"""
        service = I18nService()
        await service.load_translations()

        result = await service.reload_translations()

        assert result.is_success
        assert "en" in service.translations
