"""
IPアドレスベースのロケール検出サービス
"""
import logging
from typing import Literal, Optional

import geoip2.database
import geoip2.errors

from src.utils.result import Result

# 型定義
LanguageCode = Literal["en", "ja", "zh"]
CountryCode = str  # ISO 3166-1 alpha-2

logger = logging.getLogger(__name__)


class LocaleDetectionError(Exception):
    """ロケール検出エラー"""
    pass


class LocaleDetectionService:
    """IPアドレスから地理的位置を検出し、言語を判定するサービス"""

    CHINESE_SPEAKING_COUNTRIES = {"CN", "HK", "TW", "SG"}
    JAPANESE_SPEAKING_COUNTRIES = {"JP"}
    SUPPORTED_LANGUAGES = {"en", "ja", "zh"}

    def __init__(self, geoip_db_path: str = "static/geo/GeoLite2-Country.mmdb") -> None:
        """
        Args:
            geoip_db_path: GeoIP2データベースファイルパス
        """
        self.geoip_db_path = geoip_db_path
        self.reader: Optional[geoip2.database.Reader] = None

    async def initialize(self) -> Result[None, LocaleDetectionError]:
        """
        GeoIP2データベースを初期化（アプリ起動時に1回）

        Returns:
            Result[None, LocaleDetectionError]:
                成功時: None
                失敗時: エラー詳細
        """
        try:
            self.reader = geoip2.database.Reader(self.geoip_db_path)
            logger.info("GeoIP2データベース初期化成功: %s", self.geoip_db_path)
            return Result.success(None)
        except FileNotFoundError as e:
            logger.warning("GeoIP2データベースファイルが見つかりません: %s", e)
            return Result.failure(
                LocaleDetectionError(f"GeoIP2 database file not found: {self.geoip_db_path}")
            )
        except (OSError, IOError) as e:
            logger.exception("GeoIP2データベースの読み込みエラー: %s", e)
            return Result.failure(LocaleDetectionError(f"Failed to load GeoIP2 database: {e}"))

    def detect_locale_from_ip(self, ip_address: str) -> Result[LanguageCode, LocaleDetectionError]:
        """
        IPアドレスから言語を検出

        Args:
            ip_address: クライアントIPアドレス (例: "203.0.113.45")

        Returns:
            Result[LanguageCode, LocaleDetectionError]:
                成功時: 'en', 'ja', 'zh' のいずれか
                失敗時: エラー詳細（ただしデフォルト言語 'en' で継続）

        Examples:
            >>> service.detect_locale_from_ip("203.0.113.45")  # 日本IP
            Result.success("ja")

            >>> service.detect_locale_from_ip("198.51.100.10")  # 米国IP
            Result.success("en")
        """
        if self.reader is None:
            logger.warning("GeoIP2リーダーが初期化されていません")
            return Result.success("en")

        try:
            response = self.reader.country(ip_address)
            country_code = response.country.iso_code

            if country_code is None:
                logger.warning("国コードがNone: %s", ip_address)
                return Result.success("en")

            language = self.map_country_to_language(country_code)
            logger.debug(
                "IPロケーション検出成功: ip=%s, country=%s, language=%s",
                ip_address,
                country_code,
                language,
            )
            return Result.success(language)

        except geoip2.errors.AddressNotFoundError:
            logger.warning("IPアドレス %s がGeoIP2データベースに見つかりません", ip_address)
            return Result.success("en")  # デフォルト言語
        except (ValueError, TypeError) as e:
            logger.warning("無効なIPアドレス形式: %s - %s", ip_address, e)
            return Result.success("en")  # デフォルト言語
        except geoip2.errors.GeoIP2Error as e:
            logger.exception("GeoIP2検出エラー: %s", e)
            return Result.success("en")  # エラー時もデフォルト言語で継続

    def map_country_to_language(self, country_code: CountryCode) -> LanguageCode:
        """
        国コードを言語コードにマッピング

        Args:
            country_code: ISO 3166-1 alpha-2国コード (例: "JP", "US", "CN")

        Returns:
            LanguageCode: 'en', 'ja', 'zh' のいずれか

        Mapping:
            - 'JP' → 'ja'
            - 'CN', 'HK', 'TW', 'SG' → 'zh'
            - その他 → 'en'
        """
        if country_code in self.JAPANESE_SPEAKING_COUNTRIES:
            return "ja"
        elif country_code in self.CHINESE_SPEAKING_COUNTRIES:
            return "zh"
        else:
            return "en"

    def validate_language_code(self, lang_code: str) -> bool:
        """
        言語コードがサポート対象かを検証

        Args:
            lang_code: 検証対象の言語コード

        Returns:
            bool: 'en', 'zh', 'ja' のいずれかの場合 True
        """
        return lang_code in self.SUPPORTED_LANGUAGES

    async def close(self) -> None:
        """GeoIP2リーダーをクローズ（アプリ終了時）"""
        if self.reader is not None:
            self.reader.close()
            logger.info("GeoIP2リーダーをクローズしました")
