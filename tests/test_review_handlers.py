"""
レビューハンドラーのテスト
"""
import pytest
import tornado.testing
import tornado.web
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime

from src.handlers.review_handler import (
    ReviewListHandler,
    ReviewCreateHandler,
    ReviewEditHandler
)
from src.services.review_submission_service import ReviewSubmissionService


class TestReviewHandlers(tornado.testing.AsyncHTTPTestCase):
    """レビューハンドラーのテストクラス"""

    def get_app(self):
        """テスト用アプリケーションを作成"""
        return tornado.web.Application([
            (r"/review", ReviewListHandler),
            (r"/companies/([^/]+)/reviews/new", ReviewCreateHandler),
            (r"/reviews/([^/]+)/edit", ReviewEditHandler),
        ], template_path="templates")

    def test_review_list_page_accessible(self):
        """レビュー一覧ページがアクセス可能"""
        response = self.fetch("/review")
        self.assertEqual(response.code, 200)
        self.assertIn(b"review", response.body.lower())

    def test_review_create_form_accessible(self):
        """レビュー投稿フォームがアクセス可能"""
        company_id = "64a1b2c3d4e5f6789abc123"
        response = self.fetch(f"/companies/{company_id}/reviews/new")
        self.assertEqual(response.code, 200)
        self.assertIn(b"form", response.body.lower())

    def test_review_edit_form_accessible(self):
        """レビュー編集フォームがアクセス可能"""
        review_id = "64a1b2c3d4e5f6789abc456"
        response = self.fetch(f"/reviews/{review_id}/edit")
        self.assertEqual(response.code, 200)
        self.assertIn(b"edit", response.body.lower())

    @patch('src.services.review_submission_service.ReviewSubmissionService')
    def test_review_submission_form_fields(self, mock_service):
        """レビュー投稿フォームに必要なフィールドが含まれる"""
        company_id = "64a1b2c3d4e5f6789abc123"
        response = self.fetch(f"/companies/{company_id}/reviews/new")

        # 6つの評価カテゴリーが含まれる
        self.assertIn(b"recommendation", response.body)
        self.assertIn(b"foreign_support", response.body)
        self.assertIn(b"company_culture", response.body)
        self.assertIn(b"employee_relations", response.body)
        self.assertIn(b"evaluation_system", response.body)
        self.assertIn(b"promotion_treatment", response.body)

        # 評価選択肢（1-5点、回答しない）
        self.assertIn(b'value="1"', response.body)
        self.assertIn(b'value="5"', response.body)
        self.assertIn("回答しない".encode('utf-8'), response.body)

    @patch('src.services.review_submission_service.ReviewSubmissionService')
    def test_review_list_displays_companies(self, mock_service):
        """レビュー一覧に企業情報が表示される"""
        # モックデータを設定
        mock_service_instance = mock_service.return_value
        mock_service_instance.search_companies_with_reviews = AsyncMock(return_value={
            "companies": [
                {
                    "id": "company1",
                    "name": "テスト会社A",
                    "location": "東京都",
                    "overall_average": 3.2,
                    "total_reviews": 15
                }
            ],
            "pagination": {"page": 1, "total": 1, "pages": 1}
        })

        response = self.fetch("/review")
        self.assertIn("テスト会社A".encode('utf-8'), response.body)
        self.assertIn(b"3.2", response.body)
        self.assertIn(b"15", response.body)


class TestReviewListHandler(tornado.testing.AsyncHTTPTestCase):
    """レビュー一覧ハンドラーの詳細テスト"""

    def get_app(self):
        return tornado.web.Application([
            (r"/review", ReviewListHandler),
        ], template_path="templates")

    def test_search_functionality(self):
        """検索機能のテスト"""
        # 企業名での検索
        response = self.fetch("/review?name=テスト会社")
        self.assertEqual(response.code, 200)

        # 所在地での検索
        response = self.fetch("/review?location=東京都")
        self.assertEqual(response.code, 200)

        # 評価範囲での検索
        response = self.fetch("/review?min_rating=3.0&max_rating=5.0")
        self.assertEqual(response.code, 200)

    def test_pagination(self):
        """ページネーション機能のテスト"""
        response = self.fetch("/review?page=2&limit=10")
        self.assertEqual(response.code, 200)

    def test_sorting(self):
        """ソート機能のテスト"""
        response = self.fetch("/review?sort=rating_high")
        self.assertEqual(response.code, 200)

        response = self.fetch("/review?sort=review_count")
        self.assertEqual(response.code, 200)


class TestReviewCreateHandler(tornado.testing.AsyncHTTPTestCase):
    """レビュー投稿ハンドラーの詳細テスト"""

    def get_app(self):
        return tornado.web.Application([
            (r"/companies/([^/]+)/reviews/new", ReviewCreateHandler),
        ], template_path="templates")

    @patch('src.services.review_submission_service.ReviewSubmissionService')
    def test_form_validation(self, mock_service):
        """フォームバリデーションのテスト"""
        company_id = "64a1b2c3d4e5f6789abc123"

        # 不正な評価値
        form_data = {
            "employment_status": "current",
            "ratings[recommendation]": "6",  # 1-5の範囲外
            "comments[recommendation]": "test comment"
        }

        response = self.fetch(
            f"/companies/{company_id}/reviews/new",
            method="POST",
            body=tornado.httputil.urlencode(form_data)
        )

        # バリデーションエラーが返される
        self.assertEqual(response.code, 400)

    @patch('src.services.review_submission_service.ReviewSubmissionService')
    def test_successful_submission(self, mock_service):
        """正常な投稿のテスト"""
        company_id = "64a1b2c3d4e5f6789abc123"
        mock_service_instance = mock_service.return_value
        mock_service_instance.submit_review = AsyncMock(return_value={
            "status": "success",
            "review_id": "new_review_id"
        })

        form_data = {
            "employment_status": "former",
            "ratings[recommendation]": "4",
            "ratings[foreign_support]": "3",
            "comments[recommendation]": "good company",
            "comments[foreign_support]": ""
        }

        response = self.fetch(
            f"/companies/{company_id}/reviews/new",
            method="POST",
            body=tornado.httputil.urlencode(form_data)
        )

        # 成功時はリダイレクト
        self.assertEqual(response.code, 302)


class TestReviewEditHandler(tornado.testing.AsyncHTTPTestCase):
    """レビュー編集ハンドラーの詳細テスト"""

    def get_app(self):
        return tornado.web.Application([
            (r"/reviews/([^/]+)/edit", ReviewEditHandler),
        ], template_path="templates")

    @patch('src.services.review_submission_service.ReviewSubmissionService')
    def test_edit_permission_check(self, mock_service):
        """編集権限チェックのテスト"""
        review_id = "64a1b2c3d4e5f6789abc456"
        mock_service_instance = mock_service.return_value
        mock_service_instance.check_edit_permission = AsyncMock(return_value=False)

        response = self.fetch(f"/reviews/{review_id}/edit")

        # 権限がない場合は403
        self.assertEqual(response.code, 403)

    @patch('src.services.review_submission_service.ReviewSubmissionService')
    def test_existing_data_display(self, mock_service):
        """既存データの表示テスト"""
        review_id = "64a1b2c3d4e5f6789abc456"
        mock_service_instance = mock_service.return_value
        mock_service_instance.check_edit_permission = AsyncMock(return_value=True)
        mock_service_instance.get_review = AsyncMock(return_value={
            "id": review_id,
            "ratings": {"recommendation": 4, "foreign_support": 3},
            "comments": {"recommendation": "existing comment", "foreign_support": ""}
        })

        response = self.fetch(f"/reviews/{review_id}/edit")
        self.assertEqual(response.code, 200)
        self.assertIn("existing comment".encode('utf-8'), response.body)