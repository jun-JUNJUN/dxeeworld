"""
レビュー編集機能のテスト
TDD Red Phase: 失敗するテストを最初に作成
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
import tornado.testing
import tornado.web
from src.handlers.review_handler import ReviewEditHandler
from src.services.review_submission_service import ReviewSubmissionService


class TestReviewEditFunctionality(tornado.testing.AsyncHTTPTestCase):
    """レビュー編集機能のテストクラス"""

    def get_app(self):
        """テスト用アプリケーションを設定"""
        # モックサービスを設定
        self.mock_review_service = AsyncMock(spec=ReviewSubmissionService)

        # カスタムハンドラークラスを作成してモックを注入
        class MockReviewEditHandler(ReviewEditHandler):
            def initialize(self):
                self.review_service = self.application.mock_review_service

            def get_current_user_id(self):
                return "user123"

        app = tornado.web.Application([
            (r"/reviews/([^/]+)/edit", MockReviewEditHandler),
        ])
        app.mock_review_service = self.mock_review_service
        return app

    @tornado.testing.gen_test
    async def test_edit_form_display_for_own_review_within_one_year(self):
        """1年以内の自己投稿レビューの編集フォーム表示テスト"""
        # Given: ユーザーが1年以内に投稿したレビューが存在
        review_id = "review123"
        user_id = "user123"
        review_data = {
            "_id": review_id,
            "company_id": "company123",
            "user_id": user_id,
            "employment_status": "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": None,
                "employee_relations": 5,
                "evaluation_system": 2,
                "promotion_treatment": 4
            },
            "comments": {
                "recommendation": "良い会社です",
                "foreign_support": "",
                "company_culture": None,
                "employee_relations": "同僚との関係良好",
                "evaluation_system": None,
                "promotion_treatment": "昇進は普通"
            },
            "individual_average": 3.6,
            "answered_count": 5,
            "created_at": datetime.utcnow() - timedelta(days=180),  # 6ヶ月前
            "updated_at": datetime.utcnow() - timedelta(days=180),
            "is_active": True
        }

        company_data = {
            "_id": "company123",
            "name": "テスト会社",
            "location": "東京都"
        }

        # モックサービスの設定
        self.mock_review_service.check_edit_permission.return_value = True
        self.mock_review_service.get_review.return_value = review_data
        self.mock_review_service.get_company_info.return_value = company_data

        # When: 編集フォームにアクセス
        response = await self.fetch(f"/reviews/{review_id}/edit")

        # Then: フォームが正常に表示される
        self.assertEqual(response.code, 200)
        self.assertIn("テスト会社", response.body.decode())
        self.assertIn("良い会社です", response.body.decode())

        # 権限チェックが呼ばれたことを確認
        self.mock_review_service.check_edit_permission.assert_called_once_with(user_id, review_id)

    @tornado.testing.gen_test
    async def test_edit_permission_denied_for_other_users_review(self):
        """他のユーザーのレビュー編集権限拒否テスト"""
        # Given: 他のユーザーが投稿したレビュー
        review_id = "review123"
        current_user_id = "user456"  # 異なるユーザー

        # モックサービスの設定
        self.mock_review_service.check_edit_permission.return_value = False

        # When: 編集フォームにアクセス
        response = await self.fetch(f"/reviews/{review_id}/edit")

        # Then: 403エラーが返される
        self.assertEqual(response.code, 403)

    @tornado.testing.gen_test
    async def test_edit_permission_denied_for_review_older_than_one_year(self):
        """1年以上経過したレビューの編集権限拒否テスト"""
        # Given: 1年以上前に投稿されたレビュー
        review_id = "review123"
        user_id = "user123"

        # モックサービスの設定（1年以上経過で編集不可）
        self.mock_review_service.check_edit_permission.return_value = False

        # When: 編集フォームにアクセス
        response = await self.fetch(f"/reviews/{review_id}/edit")

        # Then: 403エラーが返される
        self.assertEqual(response.code, 403)

    @tornado.testing.gen_test
    async def test_review_update_success(self):
        """レビュー更新成功テスト"""
        # Given: 編集可能なレビューと更新データ
        review_id = "review123"
        user_id = "user123"

        update_data = {
            "employment_status": "current",
            "ratings": {
                "recommendation": 5,
                "foreign_support": 4,
                "company_culture": 3,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 3
            },
            "comments": {
                "recommendation": "更新されたコメント",
                "foreign_support": "改善されました",
                "company_culture": None,
                "employee_relations": "良好な関係",
                "evaluation_system": "",
                "promotion_treatment": "昇進機会あり"
            }
        }

        # モックサービスの設定
        self.mock_review_service.check_edit_permission.return_value = True
        self.mock_review_service.update_review.return_value = {
            "status": "success",
            "individual_average": 3.7
        }

        # When: レビューを更新
        body = self._create_form_body(update_data)
        response = await self.fetch(f"/reviews/{review_id}/edit",
                                  method="PUT",
                                  body=body)

        # Then: 更新が成功し、適切にリダイレクトされる
        self.assertEqual(response.code, 302)  # リダイレクト

        # 更新サービスが呼ばれたことを確認
        self.mock_review_service.update_review.assert_called_once()

    @tornado.testing.gen_test
    async def test_review_update_validation_failure(self):
        """レビュー更新バリデーション失敗テスト"""
        # Given: 無効なデータでの更新試行
        review_id = "review123"
        user_id = "user123"

        invalid_data = {
            "employment_status": "invalid_status",  # 無効な値
            "ratings": {
                "recommendation": 6,  # 範囲外の値
                "foreign_support": "invalid",  # 無効な型
            },
            "comments": {
                "recommendation": "a" * 1001,  # 長すぎるコメント
            }
        }

        # モックサービスの設定
        self.mock_review_service.check_edit_permission.return_value = True

        # When: 無効なデータで更新試行
        body = self._create_form_body(invalid_data)
        response = await self.fetch(f"/reviews/{review_id}/edit",
                                  method="PUT",
                                  body=body)

        # Then: バリデーションエラーが返される
        self.assertEqual(response.code, 400)

    @tornado.testing.gen_test
    async def test_review_update_triggers_company_average_recalculation(self):
        """レビュー更新が企業平均点の再計算をトリガーするテスト"""
        # Given: 更新可能なレビュー
        review_id = "review123"
        company_id = "company123"
        user_id = "user123"

        update_data = {
            "employment_status": "current",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 4,
                "company_culture": 4,
                "employee_relations": 4,
                "evaluation_system": 4,
                "promotion_treatment": 4
            },
            "comments": {}
        }

        # モックサービスの設定
        self.mock_review_service.check_edit_permission.return_value = True
        self.mock_review_service.update_review.return_value = {
            "status": "success",
            "company_id": company_id
        }

        # When: レビューを更新
        body = self._create_form_body(update_data)
        response = await self.fetch(f"/reviews/{review_id}/edit",
                                  method="PUT",
                                  body=body)

        # Then: 更新が成功し、企業平均点の再計算がトリガーされる
        self.assertEqual(response.code, 302)

        # update_reviewが呼ばれて内部で企業平均点が再計算されることを確認
        self.mock_review_service.update_review.assert_called_once()

    def _create_form_body(self, data):
        """フォームデータのボディを作成"""
        form_data = [f"employment_status={data['employment_status']}"]

        # 評価データ
        for category, rating in data.get('ratings', {}).items():
            if rating is not None:
                form_data.append(f"ratings[{category}]={rating}")
            else:
                form_data.append(f"ratings[{category}]=no_answer")

        # コメントデータ
        for category, comment in data.get('comments', {}).items():
            if comment:
                form_data.append(f"comments[{category}]={comment}")
            else:
                form_data.append(f"comments[{category}]=")

        return "&".join(form_data)


class TestReviewEditPermissionLogic:
    """レビュー編集権限ロジックの単体テスト"""

    @pytest.fixture
    def review_service(self):
        """レビューサービスのモック"""
        return AsyncMock(spec=ReviewSubmissionService)

    @pytest.mark.asyncio
    async def test_check_edit_permission_within_one_year(self, review_service):
        """1年以内の編集権限チェックテスト"""
        # Given: 6ヶ月前に投稿されたレビュー
        user_id = "user123"
        review_id = "review123"
        review_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow() - timedelta(days=180),
            "is_active": True
        }

        review_service.find_one.return_value = review_data

        # When: 編集権限をチェック
        from src.services.review_submission_service import ReviewSubmissionService
        service = ReviewSubmissionService()
        service.db = review_service  # モックDB注入

        result = await service.check_edit_permission(user_id, review_id)

        # Then: 編集権限が認められる
        assert result is True

    @pytest.mark.asyncio
    async def test_check_edit_permission_over_one_year(self, review_service):
        """1年超過の編集権限拒否テスト"""
        # Given: 13ヶ月前に投稿されたレビュー
        user_id = "user123"
        review_id = "review123"
        review_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow() - timedelta(days=400),
            "is_active": True
        }

        review_service.find_one.return_value = review_data

        # When: 編集権限をチェック
        from src.services.review_submission_service import ReviewSubmissionService
        service = ReviewSubmissionService()
        service.db = review_service

        result = await service.check_edit_permission(user_id, review_id)

        # Then: 編集権限が拒否される
        assert result is False

    @pytest.mark.asyncio
    async def test_check_edit_permission_different_user(self, review_service):
        """異なるユーザーの編集権限拒否テスト"""
        # Given: 他のユーザーが投稿したレビュー
        owner_user_id = "user123"
        requesting_user_id = "user456"
        review_id = "review123"
        review_data = {
            "user_id": owner_user_id,
            "created_at": datetime.utcnow() - timedelta(days=30),
            "is_active": True
        }

        review_service.find_one.return_value = review_data

        # When: 異なるユーザーが編集権限をチェック
        from src.services.review_submission_service import ReviewSubmissionService
        service = ReviewSubmissionService()
        service.db = review_service

        result = await service.check_edit_permission(requesting_user_id, review_id)

        # Then: 編集権限が拒否される
        assert result is False