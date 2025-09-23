"""
レビュー投稿制限機能の専用テスト
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from src.services.review_submission_service import ReviewSubmissionService


class TestReviewRestrictions:
    """レビュー投稿制限機能の詳細テスト"""

    def setup_method(self):
        """各テスト前の準備"""
        self.mock_db = AsyncMock()
        self.mock_calc_service = AsyncMock()
        self.submission_service = ReviewSubmissionService(
            self.mock_db,
            self.mock_calc_service
        )

    @pytest.mark.asyncio
    async def test_one_year_restriction_enforcement(self):
        """1年以内の重複投稿制限の強制"""
        user_id = "user_123"
        company_id = "company_456"

        # 3ヶ月前のレビューが存在
        existing_review = {
            "_id": "review_existing",
            "created_at": datetime.utcnow() - timedelta(days=90)
        }
        self.mock_db.find_one.return_value = existing_review

        result = await self.submission_service.validate_review_permissions(
            user_id, company_id
        )

        assert result["can_create"] is False
        assert result["can_update"] is True
        assert result["existing_review_id"] == "review_existing"
        # 約275日後に投稿可能
        assert 270 <= result["days_until_next"] <= 280

    @pytest.mark.asyncio
    async def test_exact_one_year_boundary(self):
        """ちょうど1年経過の境界テスト"""
        user_id = "user_123"
        company_id = "company_456"

        # ちょうど365日前のレビュー
        existing_review = {
            "_id": "review_boundary",
            "created_at": datetime.utcnow() - timedelta(days=365)
        }
        self.mock_db.find_one.return_value = existing_review

        result = await self.submission_service.validate_review_permissions(
            user_id, company_id
        )

        assert result["can_create"] is True
        assert result["can_update"] is False
        assert result["existing_review_id"] is None
        assert result["days_until_next"] == 0

    @pytest.mark.asyncio
    async def test_multiple_companies_independent_restrictions(self):
        """複数企業への投稿制限の独立性"""
        user_id = "user_123"
        company_a = "company_aaa"
        company_b = "company_bbb"

        # 会社Aには6ヶ月前にレビュー済み
        review_company_a = {
            "_id": "review_a",
            "created_at": datetime.utcnow() - timedelta(days=180)
        }

        # 会社Aの権限チェック
        self.mock_db.find_one.return_value = review_company_a
        result_a = await self.submission_service.validate_review_permissions(
            user_id, company_a
        )

        # 会社Bの権限チェック（レビューなし）
        self.mock_db.find_one.return_value = None
        result_b = await self.submission_service.validate_review_permissions(
            user_id, company_b
        )

        # 会社Aは更新のみ可能
        assert result_a["can_create"] is False
        assert result_a["can_update"] is True

        # 会社Bは新規投稿可能
        assert result_b["can_create"] is True
        assert result_b["can_update"] is False

    @pytest.mark.asyncio
    async def test_inactive_review_handling(self):
        """非アクティブレビューの取り扱い"""
        user_id = "user_123"
        company_id = "company_456"

        # 既存レビューなしの場合
        self.mock_db.find_one.return_value = None

        # データベース検索条件の確認
        await self.submission_service.validate_review_permissions(
            user_id, company_id
        )

        # find_oneが正しい条件で呼ばれることを確認
        expected_filter = {
            "user_id": user_id,
            "company_id": company_id,
            "is_active": True  # アクティブなレビューのみ検索
        }

        self.mock_db.find_one.assert_called_with("reviews", expected_filter)

    @pytest.mark.asyncio
    async def test_create_review_with_existing_within_year(self):
        """1年以内既存レビューありでの投稿試行"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "良い"}
        }

        # 8ヶ月前のレビューが存在
        existing_review = {
            "_id": "existing_review",
            "created_at": datetime.utcnow() - timedelta(days=240)
        }
        self.mock_db.find_one.return_value = existing_review

        result = await self.submission_service.create_review(review_data)

        assert result["success"] is False
        assert result["error_code"] == "duplicate_review"
        assert result["existing_review_id"] == "existing_review"
        assert result["days_until_next"] > 120  # 残り約125日

        # レビュー作成は実行されない
        self.mock_db.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_different_users_same_company(self):
        """同じ企業への異なるユーザーからの投稿"""
        company_id = "company_123"
        user_a = "user_aaa"
        user_b = "user_bbb"

        # 両ユーザーとも投稿可能であることを確認
        self.mock_db.find_one.return_value = None

        result_a = await self.submission_service.validate_review_permissions(
            user_a, company_id
        )
        result_b = await self.submission_service.validate_review_permissions(
            user_b, company_id
        )

        assert result_a["can_create"] is True
        assert result_b["can_create"] is True

        # それぞれ独立した検索が行われる
        assert self.mock_db.find_one.call_count == 2

    @pytest.mark.asyncio
    async def test_update_permission_within_year(self):
        """1年以内での更新権限の詳細確認"""
        user_id = "user_123"
        company_id = "company_456"

        # 各期間での権限確認
        test_cases = [
            (30, True),   # 1ヶ月前 - 更新可能
            (180, True),  # 6ヶ月前 - 更新可能
            (350, True),  # 11.5ヶ月前 - 更新可能
            (370, False), # 13ヶ月前 - 更新不可（新規投稿可能）
        ]

        for days_ago, should_update in test_cases:
            existing_review = {
                "_id": f"review_{days_ago}",
                "created_at": datetime.utcnow() - timedelta(days=days_ago)
            }
            self.mock_db.find_one.return_value = existing_review

            result = await self.submission_service.validate_review_permissions(
                user_id, company_id
            )

            if should_update:
                assert result["can_update"] is True
                assert result["can_create"] is False
            else:
                assert result["can_update"] is False
                assert result["can_create"] is True