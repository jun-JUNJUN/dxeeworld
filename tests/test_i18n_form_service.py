"""
I18nFormService のユニットテスト

TDD RED フェーズ: I18nFormService の期待される動作を定義
"""

import pytest
from src.services.i18n_form_service import I18nFormService


class TestI18nFormService:
    """I18nFormService のテストクラス"""

    @pytest.fixture
    def service(self):
        """テスト対象のサービスインスタンスを返す"""
        return I18nFormService()

    def test_get_form_translations_returns_all_languages(self, service):
        """
        test_get_form_translations(): 3言語すべての翻訳が返される
        Requirements: 2.1, 2.2, 2.5
        """
        translations = service.get_form_translations()

        # 翻訳辞書の構造を検証
        assert "labels" in translations
        assert "placeholders" in translations
        assert "buttons" in translations

        # 各セクションに3言語が含まれることを検証
        for key in translations["labels"]:
            assert "en" in translations["labels"][key]
            assert "ja" in translations["labels"][key]
            assert "zh" in translations["labels"][key]

        # 主要なフィールドが存在することを検証
        assert "employment_status" in translations["labels"]
        assert "review_language" in translations["labels"]
        assert "comment" in translations["placeholders"]

    def test_detect_browser_language_ja(self, service):
        """
        test_detect_browser_language_ja(): Accept-Languageヘッダーから日本語を検出
        Requirements: 2.5
        """
        # 日本語を優先する Accept-Language ヘッダー
        accept_language = "ja,en-US;q=0.9,en;q=0.8"
        language_code = service.detect_browser_language(accept_language)

        assert language_code == "ja"

    def test_detect_browser_language_en(self, service):
        """
        英語を優先する Accept-Language ヘッダーから英語を検出
        """
        accept_language = "en-US,en;q=0.9,ja;q=0.8"
        language_code = service.detect_browser_language(accept_language)

        assert language_code == "en"

    def test_detect_browser_language_zh(self, service):
        """
        中国語を優先する Accept-Language ヘッダーから中国語を検出
        """
        accept_language = "zh-CN,zh;q=0.9,en;q=0.8"
        language_code = service.detect_browser_language(accept_language)

        assert language_code == "zh"

    def test_detect_browser_language_fallback(self, service):
        """
        test_detect_browser_language_fallback(): 未対応言語は英語にフォールバック
        Requirements: 2.5
        """
        # サポートされていない言語（フランス語）
        accept_language = "fr-FR,fr;q=0.9"
        language_code = service.detect_browser_language(accept_language)

        # デフォルトで英語にフォールバック
        assert language_code == "en"

    def test_detect_browser_language_empty(self, service):
        """
        空の Accept-Language ヘッダーの場合、英語にフォールバック
        """
        accept_language = ""
        language_code = service.detect_browser_language(accept_language)

        assert language_code == "en"

    def test_get_supported_languages(self, service):
        """
        test_get_supported_languages(): 英語・日本語・中国語の3つのみ
        Requirements: 2.1, 2.2
        """
        languages = service.get_supported_languages()

        # 3言語のみサポート
        assert len(languages) == 3

        # 各言語のコードと名前を検証
        codes = [lang["code"] for lang in languages]
        assert "en" in codes
        assert "ja" in codes
        assert "zh" in codes

        # 言語オプションの構造を検証
        for lang in languages:
            assert "code" in lang
            assert "name" in lang
            assert "native_name" in lang

    def test_translation_completeness(self, service):
        """
        全ての翻訳キーが3言語で一致していることを検証
        Requirements: 2.6, 2.7, 2.8
        """
        translations = service.get_form_translations()

        # 空文字列が許容されるキー（例：英語の年サフィックスは不要）
        allowed_empty = {"year_suffix"}

        # labels の全キーで3言語が揃っているか検証
        for key, lang_dict in translations["labels"].items():
            assert set(lang_dict.keys()) == {"en", "ja", "zh"}, f"Label '{key}' missing languages"
            # 翻訳が空でないことを検証（特定のキーを除く）
            if key not in allowed_empty:
                assert lang_dict["en"], f"English translation for label '{key}' is empty"
                assert lang_dict["ja"], f"Japanese translation for label '{key}' is empty"
                assert lang_dict["zh"], f"Chinese translation for label '{key}' is empty"

        # placeholders の全キーで3言語が揃っているか検証
        for key, lang_dict in translations["placeholders"].items():
            assert set(lang_dict.keys()) == {"en", "ja", "zh"}, f"Placeholder '{key}' missing languages"

        # buttons の全キーで3言語が揃っているか検証
        for key, lang_dict in translations["buttons"].items():
            assert set(lang_dict.keys()) == {"en", "ja", "zh"}, f"Button '{key}' missing languages"

    def test_specific_translations_exist(self, service):
        """
        主要な翻訳キーが存在し、正しい翻訳があることを検証
        Requirements: 2.6, 2.7, 2.8
        """
        translations = service.get_form_translations()

        # 雇用状態ラベル
        assert "employment_status" in translations["labels"]
        assert translations["labels"]["employment_status"]["en"] == "Employment Status"
        assert translations["labels"]["employment_status"]["ja"] == "在職状況"
        assert translations["labels"]["employment_status"]["zh"] == "在职状态"

        # 現従業員
        assert "current_employee" in translations["labels"]
        assert translations["labels"]["current_employee"]["en"] == "Current Employee"
        assert translations["labels"]["current_employee"]["ja"] == "現従業員"
        assert translations["labels"]["current_employee"]["zh"] == "现员工"

        # 投稿ボタン
        assert "submit" in translations["buttons"]
        assert translations["buttons"]["submit"]["en"] == "Submit Review"
        assert translations["buttons"]["submit"]["ja"] == "レビューを投稿"
        assert translations["buttons"]["submit"]["zh"] == "提交评价"
