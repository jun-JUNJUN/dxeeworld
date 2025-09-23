"""
レビュー編集機能の簡潔なテスト
TDD Green Phase: テストを通すための実装確認
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from src.services.review_submission_service import ReviewSubmissionService


class TestReviewEditPermissionLogic:
    """レビュー編集権限ロジックの単体テスト"""

    @pytest.mark.asyncio
    async def test_check_edit_permission_within_one_year_same_user(self):
        """1年以内の同一ユーザーによる編集権限チェック"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        user_id = "user123"
        review_id = "review123"
        review_data = {
            "_id": review_id,
            "user_id": user_id,
            "created_at": datetime.utcnow() - timedelta(days=180),  # 6ヶ月前
            "is_active": True
        }

        mock_db.find_one.return_value = review_data

        # When
        result = await service.check_edit_permission(user_id, review_id)

        # Then
        assert result is True
        mock_db.find_one.assert_called_once_with(
            "reviews",
            {"_id": review_id, "is_active": True}
        )

    @pytest.mark.asyncio
    async def test_check_edit_permission_over_one_year(self):
        """1年超過のレビュー編集権限拒否"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        user_id = "user123"
        review_id = "review123"
        review_data = {
            "_id": review_id,
            "user_id": user_id,
            "created_at": datetime.utcnow() - timedelta(days=400),  # 400日前
            "is_active": True
        }

        mock_db.find_one.return_value = review_data

        # When
        result = await service.check_edit_permission(user_id, review_id)

        # Then
        assert result is False

    @pytest.mark.asyncio
    async def test_check_edit_permission_different_user(self):
        """異なるユーザーの編集権限拒否"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        requesting_user_id = "user456"
        review_id = "review123"
        review_data = {
            "_id": review_id,
            "user_id": "user123",  # 異なるユーザー
            "created_at": datetime.utcnow() - timedelta(days=30),
            "is_active": True
        }

        mock_db.find_one.return_value = review_data

        # When
        result = await service.check_edit_permission(requesting_user_id, review_id)

        # Then
        assert result is False

    @pytest.mark.asyncio
    async def test_check_edit_permission_review_not_found(self):
        """存在しないレビューの編集権限拒否"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        user_id = "user123"
        review_id = "nonexistent"

        mock_db.find_one.return_value = None

        # When
        result = await service.check_edit_permission(user_id, review_id)

        # Then
        assert result is False

    @pytest.mark.asyncio
    async def test_update_review_success(self):
        """レビュー更新成功テスト"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        review_id = "review123"
        user_id = "user123"
        company_id = "company123"

        existing_review = {
            "_id": review_id,
            "user_id": user_id,
            "company_id": company_id,
            "created_at": datetime.utcnow() - timedelta(days=30),
            "is_active": True
        }

        update_data = {
            "employment_status": "current",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": 5,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 4
            },
            "comments": {
                "recommendation": "Updated comment",
                "foreign_support": "",
                "company_culture": None,
                "employee_relations": "Good",
                "evaluation_system": None,
                "promotion_treatment": "Fair"
            }
        }

        mock_db.find_one.return_value = existing_review
        mock_db.create.return_value = "history123"
        mock_db.update.return_value = True

        # When
        result = await service.update_review(review_id, update_data)

        # Then
        assert result["status"] == "success"
        assert "individual_average" in result
        assert result["company_id"] == company_id

        # 更新が呼ばれたことを確認
        mock_db.update.assert_called_once()
        mock_db.create.assert_called_once()  # 履歴作成

    @pytest.mark.asyncio
    async def test_update_review_not_found(self):
        """存在しないレビューの更新エラー"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        review_id = "nonexistent"
        update_data = {"employment_status": "current", "ratings": {}, "comments": {}}

        mock_db.find_one.return_value = None

        # When
        result = await service.update_review(review_id, update_data)

        # Then
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_individual_average_calculation_in_update(self):
        """更新時の個別平均点計算テスト"""
        # Given
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        review_id = "review123"
        existing_review = {
            "_id": review_id,
            "user_id": "user123",
            "company_id": "company123",
            "created_at": datetime.utcnow() - timedelta(days=30),
            "is_active": True
        }

        # 4つの項目に回答: 5, 4, 3, 2 → 平均 3.5
        update_data = {
            "employment_status": "current",
            "ratings": {
                "recommendation": 5,
                "foreign_support": 4,
                "company_culture": 3,
                "employee_relations": 2,
                "evaluation_system": None,  # 未回答
                "promotion_treatment": None  # 未回答
            },
            "comments": {}
        }

        mock_db.find_one.return_value = existing_review
        mock_db.create.return_value = "history123"
        mock_db.update.return_value = True

        # When
        result = await service.update_review(review_id, update_data)

        # Then
        assert result["status"] == "success"
        assert result["individual_average"] == 3.5  # (5+4+3+2)/4 = 3.5