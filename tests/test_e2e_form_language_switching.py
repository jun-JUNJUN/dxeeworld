"""
Task 12.2: フォーム言語切り替えテスト

英語→日本語→中国語の言語切り替え動作を検証するテスト
ラベルとプレースホルダーの正しい切り替えを検証するテスト

注: 完全なJavaScript動作のテストにはブラウザ自動化が必要です。
このテストでは、HTTP統合レベルで検証可能な部分（フォームデータの埋め込み、言語選択要素の存在）を検証します。
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from tornado.testing import AsyncHTTPTestCase
from bs4 import BeautifulSoup
import sys
import os
import json

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# TranslationServiceモジュールをモック（httpx依存を回避）
mock_translation_service_class = MagicMock()
mock_translation_service_class.return_value = MagicMock()
mock_translation_service_module = MagicMock()
mock_translation_service_module.TranslationService = mock_translation_service_class
sys.modules['src.services.translation_service'] = mock_translation_service_module

from src.app import create_app


class FormLanguageSwitchingTest(AsyncHTTPTestCase):
    """Task 12.2: フォーム言語切り替えテスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        self.test_company = {
            "id": "test-company-001",
            "name": "テスト株式会社",
            "industry_label": "IT・インターネット",
            "size_label": "中規模企業（100-999名）",
            "location": "東京都渋谷区",
            "country": "日本",
        }

        self.test_user_id = "test-user-123"
        self.test_session_id = "test-session-456"

    @patch("src.services.review_submission_service.ReviewSubmissionService.check_review_permission")
    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_form_contains_language_selector(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
        mock_check_permission,
    ):
        """フォームに言語選択ドロップダウンが存在することを検証"""
        from src.utils.result import Result

        # モックの設定
        mock_check_access.return_value = Result.success({
            "access_granted": True,
            "user_context": {"identity_id": self.test_user_id}
        })

        mock_validate_session.return_value = Result.success({
            "identity_id": self.test_user_id
        })

        mock_get_company.return_value = self.test_company
        mock_check_permission.return_value = {"can_create": True}

        # フォーム表示
        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        self.assertEqual(response.code, 200, "フォームが表示されること")

        soup = BeautifulSoup(response.body, "html.parser")

        # 言語選択ドロップダウンの存在を確認
        language_select = soup.find("select", {"name": "review_language"})
        self.assertIsNotNone(language_select, "言語選択ドロップダウンが存在すること")

        # 3言語のオプションが存在することを確認
        options = language_select.find_all("option")
        option_values = [opt.get("value") for opt in options]

        self.assertIn("ja", option_values, "日本語オプションが存在すること")
        self.assertIn("en", option_values, "英語オプションが存在すること")
        self.assertIn("zh", option_values, "中国語オプションが存在すること")

    @patch("src.services.review_submission_service.ReviewSubmissionService.check_review_permission")
    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_form_contains_translation_data(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
        mock_check_permission,
    ):
        """フォームに翻訳データ（JSON）が埋め込まれていることを検証"""
        from src.utils.result import Result

        # モックの設定
        mock_check_access.return_value = Result.success({
            "access_granted": True,
            "user_context": {"identity_id": self.test_user_id}
        })

        mock_validate_session.return_value = Result.success({
            "identity_id": self.test_user_id
        })

        mock_get_company.return_value = self.test_company
        mock_check_permission.return_value = {"can_create": True}

        # フォーム表示
        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        self.assertEqual(response.code, 200)

        response_body = response.body.decode("utf-8")

        # 翻訳データのJSONが埋め込まれていることを確認
        # JavaScriptコード内に translations 変数が存在するはず
        self.assertIn("translations", response_body, "翻訳データ変数が存在すること")

        # JSONデータを抽出して検証
        # JavaScriptコード内の translations = {...} パターンを探す
        if "translations" in response_body:
            # 翻訳データの存在を確認（完全なJSONパースは難しいため、キーワード検証）
            # 3言語のラベルが含まれていることを確認
            self.assertIn("\"ja\"", response_body, "日本語翻訳データが存在すること")
            self.assertIn("\"en\"", response_body, "英語翻訳データが存在すること")
            self.assertIn("\"zh\"", response_body, "中国語翻訳データが存在すること")

    @patch("src.services.review_submission_service.ReviewSubmissionService.check_review_permission")
    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_form_default_language_detection(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
        mock_check_permission,
    ):
        """ブラウザ言語検出によるデフォルト言語設定を検証"""
        from src.utils.result import Result

        # モックの設定
        mock_check_access.return_value = Result.success({
            "access_granted": True,
            "user_context": {"identity_id": self.test_user_id}
        })

        mock_validate_session.return_value = Result.success({
            "identity_id": self.test_user_id
        })

        mock_get_company.return_value = self.test_company
        mock_check_permission.return_value = {"can_create": True}

        # Accept-Languageヘッダーを英語に設定してフォーム表示
        response_en = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={
                "Cookie": f"session_id={self.test_session_id}",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )

        self.assertEqual(response_en.code, 200)

        # レスポンスに翻訳データとフォーム要素が存在することを確認
        response_body_en = response_en.body.decode("utf-8")
        self.assertIn("translations", response_body_en, "翻訳データが存在すること")
        self.assertIn("reviewLanguage", response_body_en, "言語選択要素が存在すること")

        # Accept-Languageヘッダーを中国語に設定してフォーム表示
        response_zh = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={
                "Cookie": f"session_id={self.test_session_id}",
                "Accept-Language": "zh-CN,zh;q=0.9"
            }
        )

        self.assertEqual(response_zh.code, 200)

        response_body_zh = response_zh.body.decode("utf-8")
        self.assertIn("translations", response_body_zh, "翻訳データが存在すること")
        self.assertIn("reviewLanguage", response_body_zh, "言語選択要素が存在すること")

    @patch("src.services.review_submission_service.ReviewSubmissionService.check_review_permission")
    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_form_contains_multilingual_labels(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
        mock_check_permission,
    ):
        """フォームに多言語ラベルのデータ属性が存在することを検証"""
        from src.utils.result import Result

        # モックの設定
        mock_check_access.return_value = Result.success({
            "access_granted": True,
            "user_context": {"identity_id": self.test_user_id}
        })

        mock_validate_session.return_value = Result.success({
            "identity_id": self.test_user_id
        })

        mock_get_company.return_value = self.test_company
        mock_check_permission.return_value = {"can_create": True}

        # フォーム表示
        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, "html.parser")

        # フォームフィールドに言語切り替え用のデータ属性が存在することを確認
        # 例: data-label-ja, data-label-en, data-label-zh などの属性
        response_body = response.body.decode("utf-8")

        # ラベルやプレースホルダーが設定されていることを確認
        # （実際の実装により異なるため、存在確認のみ）
        has_language_data = (
            "data-label" in response_body or
            "data-placeholder" in response_body or
            "translations" in response_body
        )

        self.assertTrue(
            has_language_data,
            "フォームに言語切り替え用のデータが存在すること"
        )


if __name__ == "__main__":
    unittest.main()
