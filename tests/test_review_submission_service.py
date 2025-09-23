"""
レビュー投稿システムのテスト
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from src.services.review_submission_service import ReviewSubmissionService
from src.models.review import Review, EmploymentStatus, ReviewCategory
from src.models.review_history import ReviewHistory, ReviewAction


class TestReviewSubmissionService:
    """ReviewSubmissionServiceのテスト"""

    def setup_method(self):
        """各テスト前の準備"""
        self.mock_db = AsyncMock()
        self.mock_calc_service = AsyncMock()
        self.submission_service = ReviewSubmissionService(
            self.mock_db,
            self.mock_calc_service
        )

    @pytest.mark.asyncio
    async def test_create_review_success(self):
        """レビュー投稿成功"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": None,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 2
            },
            "comments": {
                "recommendation": "良い会社です",
                "foreign_support": "",
                "company_culture": None,
                "employee_relations": "良好な関係",
                "evaluation_system": None,
                "promotion_treatment": "昇進は難しい"
            }
        }

        # 権限チェック: 投稿可能
        self.mock_db.find_one.return_value = None  # 既存レビューなし

        # 平均点計算
        self.mock_calc_service.calculate_individual_average.return_value = (3.2, 4)
        self.mock_calc_service.validate_rating_values.return_value = []
        self.mock_calc_service.validate_required_categories.return_value = []

        # レビュー作成成功
        self.mock_db.create.return_value = "review_789"

        # 企業平均点再計算
        self.mock_calc_service.recalculate_company_averages.return_value = True

        result = await self.submission_service.create_review(review_data)

        assert result["success"] is True
        assert result["review_id"] == "review_789"
        assert result["individual_average"] == 3.2

        # データベース操作の確認
        self.mock_db.find_one.assert_called_once()  # 重複チェック
        assert self.mock_db.create.call_count == 2  # レビュー作成 + 履歴作成
        self.mock_calc_service.recalculate_company_averages.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_validation_error(self):
        """レビュー投稿時のバリデーションエラー"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "former",
            "ratings": {
                "recommendation": 6,  # 無効な評価（1-5の範囲外）
                "foreign_support": "invalid",  # 無効な型
                # company_culture が欠如
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 2
            },
            "comments": {}
        }

        # バリデーションエラーを設定
        self.mock_calc_service.validate_rating_values.return_value = [
            "Invalid rating for recommendation: 6 (must be 1-5)",
            "Invalid type for foreign_support: expected int, got str"
        ]
        self.mock_calc_service.validate_required_categories.return_value = [
            "Missing required category: company_culture"
        ]

        result = await self.submission_service.create_review(review_data)

        assert result["success"] is False
        assert "errors" in result
        assert len(result["errors"]) == 3

        # データベース操作は行われない
        self.mock_db.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_duplicate_check(self):
        """重複レビュー投稿の防止"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "良い"}
        }

        # 1年以内の既存レビューが存在
        existing_review = {
            "_id": "existing_review",
            "created_at": datetime.utcnow() - timedelta(days=180)  # 6ヶ月前
        }
        self.mock_db.find_one.return_value = existing_review

        result = await self.submission_service.create_review(review_data)

        assert result["success"] is False
        assert "duplicate" in result["error_code"]
        assert "existing_review_id" in result

        # レビュー作成は行われない
        self.mock_db.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_with_history_logging(self):
        """レビュー投稿時の履歴ログ記録"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "former",
            "ratings": {"recommendation": 5},
            "comments": {"recommendation": "最高"}
        }

        # 設定
        self.mock_db.find_one.return_value = None
        self.mock_calc_service.calculate_individual_average.return_value = (5.0, 1)
        self.mock_calc_service.validate_rating_values.return_value = []
        self.mock_calc_service.validate_required_categories.return_value = []
        self.mock_db.create.side_effect = ["review_new", "history_new"]
        self.mock_calc_service.recalculate_company_averages.return_value = True

        result = await self.submission_service.create_review(review_data)

        assert result["success"] is True

        # create が2回呼ばれる（レビュー + 履歴）
        assert self.mock_db.create.call_count == 2

        # 2回目の呼び出しが履歴作成
        history_call = self.mock_db.create.call_args_list[1]
        assert history_call[0][0] == "review_history"
        assert history_call[0][1]["action"] == "create"

    @pytest.mark.asyncio
    async def test_validate_review_permissions_can_create(self):
        """レビュー投稿権限チェック - 投稿可能"""
        user_id = "user_123"
        company_id = "company_456"

        # 既存レビューなし
        self.mock_db.find_one.return_value = None

        result = await self.submission_service.validate_review_permissions(
            user_id, company_id
        )

        assert result["can_create"] is True
        assert result["can_update"] is False
        assert result["existing_review_id"] is None
        assert result["days_until_next"] == 0

    @pytest.mark.asyncio
    async def test_validate_review_permissions_can_update(self):
        """レビュー投稿権限チェック - 更新可能"""
        user_id = "user_123"
        company_id = "company_456"

        # 6ヶ月前のレビューが存在
        existing_review = {
            "_id": "review_existing",
            "created_at": datetime.utcnow() - timedelta(days=180)
        }
        self.mock_db.find_one.return_value = existing_review

        result = await self.submission_service.validate_review_permissions(
            user_id, company_id
        )

        assert result["can_create"] is False
        assert result["can_update"] is True
        assert result["existing_review_id"] == "review_existing"
        assert result["days_until_next"] > 180  # 1年まで残り日数

    @pytest.mark.asyncio
    async def test_validate_review_permissions_year_passed(self):
        """レビュー投稿権限チェック - 1年経過後投稿可能"""
        user_id = "user_123"
        company_id = "company_456"

        # 13ヶ月前のレビューが存在
        existing_review = {
            "_id": "review_old",
            "created_at": datetime.utcnow() - timedelta(days=400)
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
    async def test_sanitize_review_data(self):
        """レビューデータのサニタイズ処理"""
        raw_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": None,
                "company_culture": 3
            },
            "comments": {
                "recommendation": "<script>alert('xss')</script>良い会社",
                "foreign_support": "",
                "company_culture": "普通の会社 & 環境"
            }
        }

        sanitized = await self.submission_service.sanitize_review_data(raw_data)

        # HTMLエスケープの確認
        assert "&lt;script&gt;" in sanitized["comments"]["recommendation"]
        assert "&amp;" in sanitized["comments"]["company_culture"]

        # 他のデータは変更されない
        assert sanitized["ratings"]["recommendation"] == 4
        assert sanitized["employment_status"] == "former"

    @pytest.mark.asyncio
    async def test_build_review_object(self):
        """Reviewオブジェクトの構築"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "良い"}
        }

        individual_average = 4.0
        answered_count = 1

        review = await self.submission_service.build_review_object(
            review_data, individual_average, answered_count
        )

        assert isinstance(review, Review)
        assert review.company_id == "company_123"
        assert review.user_id == "user_456"
        assert review.employment_status == EmploymentStatus.CURRENT
        assert review.individual_average == 4.0
        assert review.answered_count == 1
        assert review.is_active is True

    @pytest.mark.asyncio
    async def test_create_review_database_error(self):
        """データベースエラー時の処理"""
        review_data = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "former",
            "ratings": {"recommendation": 3},
            "comments": {"recommendation": "普通"}
        }

        # 権限チェック成功
        self.mock_db.find_one.return_value = None

        # バリデーション成功
        self.mock_calc_service.validate_rating_values.return_value = []
        self.mock_calc_service.validate_required_categories.return_value = []
        self.mock_calc_service.calculate_individual_average.return_value = (3.0, 1)

        # データベースエラー
        self.mock_db.create.side_effect = Exception("Database error")

        result = await self.submission_service.create_review(review_data)

        assert result["success"] is False
        assert "database_error" in result["error_code"]