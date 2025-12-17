"""
URL言語パラメータ管理サービス
"""
from typing import Literal, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# 型定義
LanguageCode = Literal["en", "ja", "zh"]


class URLLanguageService:
    """URL言語パラメータの追加・更新・抽出を管理"""

    def __init__(self, base_domain: str = "localhost") -> None:
        """
        Args:
            base_domain: 自サイトのドメイン（内部リンク判定用）
        """
        self.base_domain = base_domain

    def add_language_param(self, url: str, locale: LanguageCode) -> str:
        """
        URLに言語パラメータを追加

        Args:
            url: 対象URL (例: "/companies", "/reviews?page=2")
            locale: 言語コード ('en', 'ja', 'zh')

        Returns:
            str: 言語パラメータ付きURL

        Examples:
            >>> service.add_language_param("/companies", "ja")
            "/companies?lang=ja"

            >>> service.add_language_param("/reviews?page=2", "en")
            "/reviews?page=2&lang=en"
        """
        # URLパース
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)

        # lang パラメータ追加
        query_params["lang"] = [locale]

        # URL再構築
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )

        return new_url

    def update_language_param(self, url: str, new_locale: LanguageCode) -> str:
        """
        URLの言語パラメータを更新

        Args:
            url: 対象URL (例: "/companies?lang=ja")
            new_locale: 新しい言語コード

        Returns:
            str: 言語パラメータ更新済みURL

        Examples:
            >>> service.update_language_param("/companies?lang=ja", "en")
            "/companies?lang=en"

            >>> service.update_language_param("/reviews?page=2&lang=zh", "ja")
            "/reviews?page=2&lang=ja"
        """
        # 既存の言語パラメータを削除してから新しいパラメータを追加
        return self.add_language_param(url, new_locale)

    def extract_language_param(self, url: str) -> Optional[str]:
        """
        URLから言語パラメータを抽出

        Args:
            url: 対象URL

        Returns:
            Optional[str]: 言語コード、存在しない場合None
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        lang_list = query_params.get("lang")
        if lang_list and len(lang_list) > 0:
            return lang_list[0]

        return None

    def is_internal_link(self, url: str, base_domain: str) -> bool:
        """
        内部リンクかどうかを判定

        Args:
            url: 判定対象URL
            base_domain: 自サイトのドメイン

        Returns:
            bool: 内部リンクの場合True

        Internal Link Conditions:
            - 相対パス (/companies, ../about)
            - 自サイトドメイン (http://localhost:8202/companies)

        External Link Examples:
            - https://google.com
            - http://example.com
            - javascript:void(0)
            - #anchor
        """
        # アンカーリンクチェック
        if url.startswith("#"):
            return False

        # javascript:, mailto: などのプロトコルチェック
        if url.startswith("javascript:") or url.startswith("mailto:"):
            return False

        # 相対パスチェック
        if not url.startswith("http://") and not url.startswith("https://"):
            return True

        # 絶対URLの場合、ドメインチェック
        parsed = urlparse(url)

        # ドメインが空の場合は内部リンク
        if not parsed.netloc:
            return True

        # ドメインがbase_domainと一致するか確認（ポート番号を除外）
        url_domain = parsed.netloc.split(":")[0] if ":" in parsed.netloc else parsed.netloc

        return url_domain == base_domain

    def should_add_language_param(self, url: str) -> bool:
        """
        言語パラメータを付与すべきかを判定

        Args:
            url: 判定対象URL

        Returns:
            bool: 言語パラメータ付与すべき場合True

        Skip Conditions:
            - 外部リンク
            - アンカーリンク (#section)
            - javascript: プロトコル
        """
        return self.is_internal_link(url, self.base_domain)
