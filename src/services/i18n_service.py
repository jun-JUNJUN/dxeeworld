"""
翻訳データ管理と言語別フォーマット提供サービス
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from babel.dates import format_date as babel_format_date
from babel.numbers import format_decimal

from src.utils.result import Result

# 型定義
LanguageCode = Literal["en", "ja", "zh"]

logger = logging.getLogger(__name__)


class I18nError(Exception):
    """国際化サービスエラー"""
    pass


class I18nService:
    """翻訳データ管理と言語別フォーマット提供"""

    def __init__(self, translations_dir: str = "static/i18n") -> None:
        """
        Args:
            translations_dir: 翻訳JSONファイルのディレクトリパス
        """
        self.translations_dir = translations_dir
        self.translations: Dict[LanguageCode, Dict[str, Any]] = {}

    async def load_translations(self) -> Result[None, I18nError]:
        """
        全言語の翻訳データをメモリにロード（アプリ起動時に1回）

        Returns:
            Result[None, I18nError]:
                成功時: None
                失敗時: エラー詳細
        """
        try:
            for lang in ["en", "ja", "zh"]:
                file_path = Path(self.translations_dir) / f"{lang}.json"
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)  # type: ignore
                    logger.info("翻訳データロード成功: %s (%d keys)", lang, len(self.translations[lang]))  # type: ignore
                else:
                    logger.warning("翻訳ファイルが見つかりません: %s", file_path)
                    self.translations[lang] = {}  # type: ignore

            return Result.success(None)
        except Exception as e:
            logger.exception("翻訳データロードエラー: %s", e)
            return Result.failure(I18nError(f"Failed to load translations: {e}"))

    def get_translation(self, key: str, locale: LanguageCode) -> str:
        """
        翻訳キーから翻訳文字列を取得

        Args:
            key: 翻訳キー (例: "nav.home", "errors.not_found")
            locale: 言語コード ('en', 'ja', 'zh')

        Returns:
            str: 翻訳文字列、見つからない場合はフォールバック

        Fallback Order:
            1. 指定言語の翻訳
            2. 英語の翻訳
            3. 翻訳キー自体

        Examples:
            >>> service.get_translation("nav.home", "ja")
            "ホーム"

            >>> service.get_translation("nav.home", "en")
            "Home"

            >>> service.get_translation("unknown.key", "ja")
            "unknown.key"  # キーが見つからない場合
        """
        # ネストされたキー対応 (例: "nav.home" → translations["nav"]["home"])
        keys = key.split(".")

        # 指定言語で検索
        value = self._get_nested_value(self.translations.get(locale, {}), keys)
        if value:
            return value

        # 英語フォールバック
        if locale != "en":
            value = self._get_nested_value(self.translations.get("en", {}), keys)
            if value:
                logger.debug("翻訳キー %s が %s にないため英語にフォールバック", key, locale)
                return value

        # キー自体を返す（デバッグ用）
        logger.warning("翻訳キー %s が見つかりません (locale=%s)", key, locale)
        return key

    def _get_nested_value(self, data: Dict[str, Any], keys: list[str]) -> Optional[str]:
        """
        ネストされた辞書から値を取得

        Args:
            data: 辞書データ
            keys: キーのリスト

        Returns:
            str | None: 見つかった値、または None
        """
        current: Any = data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        return current if isinstance(current, str) else None

    def format_date(self, date: datetime, locale: LanguageCode) -> str:
        """
        日付を言語別フォーマットで表示

        Args:
            date: フォーマット対象の日時
            locale: 言語コード

        Returns:
            str: 言語別フォーマット文字列

        Format:
            - ja: "2025年12月14日"
            - zh: "2025年12月14日"
            - en: "Dec 14, 2025"
        """
        locale_map = {"ja": "ja_JP", "zh": "zh_CN", "en": "en_US"}
        babel_locale = locale_map.get(locale, "en_US")

        try:
            if locale == "en":
                # 英語: "Dec 14, 2025"
                return babel_format_date(date, format="medium", locale=babel_locale)
            else:
                # 日本語・中国語: "2025年12月14日"
                return babel_format_date(date, format="long", locale=babel_locale)
        except Exception as e:
            logger.exception("日付フォーマットエラー: %s", e)
            # フォールバック: ISO形式
            return date.strftime("%Y-%m-%d")

    def format_number(self, number: float, locale: LanguageCode) -> str:
        """
        数値を言語別フォーマットで表示

        Args:
            number: フォーマット対象の数値
            locale: 言語コード

        Returns:
            str: 言語別フォーマット文字列（桁区切り適用）

        Examples:
            >>> service.format_number(1234567.89, "ja")
            "1,234,567.89"
        """
        locale_map = {"ja": "ja_JP", "zh": "zh_CN", "en": "en_US"}
        babel_locale = locale_map.get(locale, "en_US")

        try:
            return format_decimal(number, locale=babel_locale)
        except Exception as e:
            logger.exception("数値フォーマットエラー: %s", e)
            # フォールバック: 基本フォーマット
            return f"{number:,.2f}"

    async def reload_translations(self) -> Result[None, I18nError]:
        """翻訳データを再読み込み（開発環境でのホットリロード用）"""
        logger.info("翻訳データを再読み込みします")
        return await self.load_translations()
