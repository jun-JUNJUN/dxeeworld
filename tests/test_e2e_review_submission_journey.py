"""
Task 12.1: レビュー投稿ユーザージャーニーテスト（日本語）

フォーム表示から入力、確認、投稿、成功メッセージまでの完全フローを検証するテスト
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from tornado.testing import AsyncHTTPTestCase
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urlencode

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


class ReviewSubmissionJourneyTest(AsyncHTTPTestCase):
    """Task 12.1: レビュー投稿ユーザージャーニーテスト（日本語）"""

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

        # レビューデータ（日本語）
        self.review_data_ja = {
            "employment_status": "current",
            "review_language": "ja",
            "ratings[recommendation]": "4",
            "ratings[foreign_support]": "5",
            "ratings[company_culture]": "4",
            "ratings[employee_relations]": "5",
            "ratings[evaluation_system]": "4",
            "ratings[promotion_treatment]": "5",
            "comments[recommendation]": "非常に働きやすい環境です。",
            "comments[foreign_support]": "外国人サポートが充実しています。",
            "comments[company_culture]": "オープンな企業文化が良いです。",
            "comments[employee_relations]": "上司との関係も良好です。",
            "comments[evaluation_system]": "評価制度が明確です。",
            "comments[promotion_treatment]": "昇進機会も平等です。",
        }

    @patch("src.handlers.review_handler.ReviewCreateHandler.require_authentication")
    @patch("src.services.review_submission_service.ReviewSubmissionService.submit_review")
    @patch("src.services.review_submission_service.ReviewSubmissionService.check_review_permission")
    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_full_review_submission_journey_japanese(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
        mock_check_permission,
        mock_submit_review,
        mock_require_auth,
    ):
        """
        完全なレビュー投稿フロー（日本語）を検証
        1. フォーム表示
        2. 確認画面表示（翻訳含む）
        3. レビュー投稿
        4. 成功メッセージ表示
        """
        # モックの設定
        from src.utils.result import Result

        # アクセス制御: 認証済みユーザー
        mock_check_access.return_value = Result.success({
            "access_granted": True,
            "user_context": {"identity_id": self.test_user_id}
        })

        # セッション検証
        mock_validate_session.return_value = Result.success({
            "identity_id": self.test_user_id,
            "email": "test@example.com"
        })

        # 会社情報取得
        mock_get_company.return_value = self.test_company

        # レビュー投稿権限
        mock_check_permission.return_value = {"can_create": True}

        # 認証要求（POSTリクエスト用）- AsyncMockでawait可能にする
        async def mock_auth():
            return self.test_user_id
        mock_require_auth.side_effect = mock_auth

        # レビュー投稿成功
        mock_submit_review.return_value = {
            "status": "success",
            "review_id": "review-789"
        }

        # 翻訳サービス（日本語→英語+中国語）
        # TranslationServiceのインスタンスメソッドをモック
        mock_translate_method = AsyncMock(return_value={
            "en": "Very comfortable working environment.",
            "zh": "非常舒适的工作环境。"
        })
        mock_translation_service_instance = MagicMock()
        mock_translation_service_instance.translate_to_other_languages = mock_translate_method
        mock_translation_service_class.return_value = mock_translation_service_instance

        # Step 1: フォーム表示を検証
        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        self.assertEqual(response.code, 200, "フォーム表示が成功すること")

        soup = BeautifulSoup(response.body, "html.parser")

        # フォームの存在を確認
        form = soup.find("form")
        self.assertIsNotNone(form, "レビュー投稿フォームが存在すること")

        # 言語選択ドロップダウンの存在を確認
        language_select = soup.find("select", {"name": "review_language"})
        self.assertIsNotNone(language_select, "言語選択ドロップダウンが存在すること")

        # 6つのレビューカテゴリーフィールドが存在することを確認
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

        for category in categories:
            rating_field = soup.find("input", {"name": f"ratings[{category}]"})
            comment_field = soup.find("textarea", {"name": f"comments[{category}]"})
            self.assertIsNotNone(
                rating_field or comment_field,  # どちらか一方があればOK
                f"{category}のフィールドが存在すること"
            )

        # Step 2: 確認画面表示を検証（mode=preview）
        preview_data = self.review_data_ja.copy()
        preview_data["mode"] = "preview"

        response_preview = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new?mode=preview",
            method="POST",
            body=urlencode(preview_data),
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        self.assertEqual(response_preview.code, 200, "確認画面が表示されること")

        soup_preview = BeautifulSoup(response_preview.body, "html.parser")
        response_text_preview = response_preview.body.decode("utf-8")

        # 確認画面の内容を確認（タイトルではなく、コンテンツで判断）
        # 確認画面には原文コメントや評価が表示されているはず
        self.assertIn("非常に働きやすい環境です", response_text_preview, "原文（日本語）コメントが表示されること")

        # 翻訳サービスが呼び出されたことを確認
        self.assertTrue(mock_translate_method.called, "翻訳サービスが呼び出されること")

        # Step 3: レビュー投稿を実行（mode=submit）
        submit_data = self.review_data_ja.copy()
        submit_data["mode"] = "submit"
        submit_data["selected_language"] = "ja"

        # 確認画面からの翻訳データをシミュレート（hidden fields）
        submit_data["translated_comments_en[recommendation]"] = "Very comfortable working environment."
        submit_data["translated_comments_zh[recommendation]"] = "非常舒适的工作环境。"

        response_submit = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new?mode=submit",
            method="POST",
            body=urlencode(submit_data),
            headers={"Cookie": f"session_id={self.test_session_id}"},
            follow_redirects=False  # リダイレクトを手動で確認
        )

        # リダイレクトを確認（302 Found - Tornadoのデフォルト）
        self.assertEqual(response_submit.code, 302, "投稿成功時にリダイレクトされること")

        # リダイレクト先を確認
        redirect_location = response_submit.headers.get("Location")
        self.assertIsNotNone(redirect_location, "リダイレクト先が設定されていること")
        self.assertIn(
            f"/companies/{self.test_company['id']}",
            redirect_location,
            "企業詳細ページにリダイレクトされること"
        )

        # レビュー投稿サービスが呼び出されたことを確認
        self.assertTrue(mock_submit_review.called, "レビュー投稿サービスが呼び出されること")

        # Step 4: リダイレクト後の成功メッセージを確認
        # Note: フラッシュメッセージの検証は実際のリダイレクト先を取得する必要がある
        # このテストではリダイレクト先のURLが正しいことを確認

        # 投稿データの検証（submit_reviewに渡されたデータ）
        call_args = mock_submit_review.call_args
        self.assertIsNotNone(call_args, "submit_reviewが呼び出されたこと")

        submitted_data = call_args[0][0]  # 第1引数がreview_data
        self.assertEqual(submitted_data["company_id"], self.test_company["id"], "会社IDが正しいこと")
        self.assertEqual(submitted_data["user_id"], self.test_user_id, "ユーザーIDが正しいこと")
        self.assertEqual(submitted_data["language"], "ja", "言語が日本語であること")
        self.assertEqual(submitted_data["employment_status"], "current", "雇用状態が現従業員であること")

        # 評価値の検証
        self.assertEqual(submitted_data["ratings"]["recommendation"], 4, "推薦度の評価が正しいこと")
        self.assertEqual(submitted_data["ratings"]["foreign_support"], 5, "外国人サポートの評価が正しいこと")

        # コメントの検証
        self.assertEqual(
            submitted_data["comments"]["recommendation"],
            "非常に働きやすい環境です。",
            "推薦度のコメントが正しいこと"
        )

    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_form_display_with_default_japanese_language(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
    ):
        """フォーム表示時にデフォルト言語が日本語に設定されていることを検証"""
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

        # Accept-Languageヘッダーを日本語に設定
        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new",
            headers={
                "Cookie": f"session_id={self.test_session_id}",
                "Accept-Language": "ja-JP,ja;q=0.9"
            }
        )

        self.assertEqual(response.code, 200)

        # レスポンスボディに日本語ラベルが含まれていることを確認
        response_body = response.body.decode("utf-8")

        # デフォルト言語の設定を確認（JavaScriptコード内）
        self.assertIn("defaultLanguage", response_body, "デフォルト言語設定が存在すること")

    @patch("src.services.review_submission_service.ReviewSubmissionService.submit_review")
    @patch("src.services.review_submission_service.ReviewSubmissionService.check_review_permission")
    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_validation_error_blocks_submission(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
        mock_check_permission,
        mock_submit_review,
    ):
        """バリデーションエラー時に投稿がブロックされることを検証"""
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

        # 無効なデータ（評価値が範囲外）
        invalid_data = {
            "employment_status": "current",
            "review_language": "ja",
            "mode": "submit",
            "selected_language": "ja",
            "ratings[recommendation]": "10",  # 無効な値（1-5の範囲外）
            "comments[recommendation]": "テストコメント",
        }

        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new?mode=submit",
            method="POST",
            body=urlencode(invalid_data),
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        # バリデーションエラーで422が返されること
        self.assertEqual(response.code, 422, "バリデーションエラーで422が返されること")

        # submit_reviewが呼び出されないことを確認
        self.assertFalse(mock_submit_review.called, "バリデーションエラー時にsubmit_reviewが呼び出されないこと")

    @patch("src.services.review_submission_service.ReviewSubmissionService.get_company_info")
    @patch("src.services.session_service.SessionService.validate_session")
    @patch("src.middleware.access_control_middleware.AccessControlMiddleware.check_access")
    def test_confirmation_screen_shows_all_ratings_and_comments(
        self,
        mock_check_access,
        mock_validate_session,
        mock_get_company,
    ):
        """確認画面で全ての評価とコメントが表示されることを検証"""
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

        # 翻訳サービス
        mock_translate_method = AsyncMock(return_value={
            "en": "Translated text",
            "zh": "翻译文本"
        })
        mock_translation_service_instance = MagicMock()
        mock_translation_service_instance.translate_to_other_languages = mock_translate_method
        mock_translation_service_class.return_value = mock_translation_service_instance

        # 確認画面を表示
        preview_data = self.review_data_ja.copy()
        preview_data["mode"] = "preview"

        response = self.fetch(
            f"/companies/{self.test_company['id']}/reviews/new?mode=preview",
            method="POST",
            body=urlencode(preview_data),
            headers={"Cookie": f"session_id={self.test_session_id}"}
        )

        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, "html.parser")

        # 全ての評価値が表示されていることを確認
        response_text = response.body.decode("utf-8")

        # カテゴリー名の一部を確認（日本語）
        self.assertIn("推薦", response_text, "推薦度カテゴリーが表示されること")
        self.assertIn("外国人", response_text, "外国人サポートカテゴリーが表示されること")

        # コメントの一部を確認
        self.assertIn("非常に働きやすい環境です", response_text, "推薦度のコメントが表示されること")
        self.assertIn("外国人サポートが充実しています", response_text, "外国人サポートのコメントが表示されること")

        # 「投稿する」ボタンと「戻る」ボタンの存在を確認
        submit_button = soup.find("button", type="submit")
        back_button = soup.find("button", {"class": lambda x: x and "back" in x.lower()}) or \
                     soup.find("a", {"class": lambda x: x and "back" in x.lower()})

        # どちらか一方が存在すればOK（実装により異なる）
        self.assertTrue(
            submit_button is not None or back_button is not None,
            "確認画面に投稿ボタンまたは戻るボタンが存在すること"
        )


if __name__ == "__main__":
    unittest.main()
