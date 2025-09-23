"""
企業別平均点計算サービスのテスト
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from src.services.company_calculation_service import CompanyCalculationService
from src.models.review import ReviewSummary, ReviewCategory


class TestCompanyCalculationService:
    """CompanyCalculationServiceのテスト"""

    def setup_method(self):
        """各テスト前の準備"""
        self.mock_db = AsyncMock()
        self.calc_service = CompanyCalculationService(self.mock_db)

    @pytest.mark.asyncio
    async def test_calculate_company_averages_with_reviews(self):
        """レビューがある企業の平均点計算"""
        company_id = "company_123"

        # モックデータ：3件のレビュー
        mock_reviews = [
            {
                "_id": "review_1",
                "individual_average": 3.5,
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": 3,
                    "company_culture": None,
                    "employee_relations": 4,
                    "evaluation_system": 3,
                    "promotion_treatment": 3
                }
            },
            {
                "_id": "review_2",
                "individual_average": 4.0,
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": 4,
                    "company_culture": 4,
                    "employee_relations": 4,
                    "evaluation_system": 4,
                    "promotion_treatment": 4
                }
            },
            {
                "_id": "review_3",
                "individual_average": 2.5,
                "ratings": {
                    "recommendation": 3,
                    "foreign_support": 2,
                    "company_culture": 2,
                    "employee_relations": None,
                    "evaluation_system": 3,
                    "promotion_treatment": 2
                }
            }
        ]

        self.mock_db.find_many.return_value = mock_reviews

        summary = await self.calc_service.calculate_company_averages(company_id)

        # 全項目平均: (3.5 + 4.0 + 2.5) / 3 = 3.3 (四捨五入)
        assert summary.total_reviews == 3
        assert summary.overall_average == 3.3

        # 項目別平均の確認
        # recommendation: (4+4+3)/3 = 3.7
        assert summary.category_averages["recommendation"] == 3.7
        # foreign_support: (3+4+2)/3 = 3.0
        assert summary.category_averages["foreign_support"] == 3.0
        # company_culture: (4+2)/2 = 3.0 (None除外)
        assert summary.category_averages["company_culture"] == 3.0

        # データベース呼び出しの確認
        self.mock_db.find_many.assert_called_once_with(
            "reviews",
            {"company_id": company_id, "is_active": True}
        )

    @pytest.mark.asyncio
    async def test_calculate_company_averages_no_reviews(self):
        """レビューがない企業の平均点計算"""
        company_id = "company_empty"
        self.mock_db.find_many.return_value = []

        summary = await self.calc_service.calculate_company_averages(company_id)

        assert summary.total_reviews == 0
        assert summary.overall_average == 0.0

        # 全カテゴリーが0.0になる
        for category in ReviewCategory:
            assert summary.category_averages[category.value] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_company_averages_single_review(self):
        """1件のレビューのみの企業の平均点計算"""
        company_id = "company_single"

        mock_reviews = [
            {
                "_id": "review_only",
                "individual_average": 4.2,
                "ratings": {
                    "recommendation": 5,
                    "foreign_support": 4,
                    "company_culture": 4,
                    "employee_relations": 4,
                    "evaluation_system": 4,
                    "promotion_treatment": None
                }
            }
        ]

        self.mock_db.find_many.return_value = mock_reviews

        summary = await self.calc_service.calculate_company_averages(company_id)

        assert summary.total_reviews == 1
        assert summary.overall_average == 4.2

        # 回答された項目のみ平均を計算
        assert summary.category_averages["recommendation"] == 5.0
        assert summary.category_averages["foreign_support"] == 4.0
        assert summary.category_averages["promotion_treatment"] == 0.0  # 未回答

    @pytest.mark.asyncio
    async def test_calculate_company_averages_all_none_category(self):
        """特定カテゴリーが全て未回答の場合"""
        company_id = "company_none_category"

        mock_reviews = [
            {
                "_id": "review_1",
                "individual_average": 3.0,
                "ratings": {
                    "recommendation": 3,
                    "foreign_support": 3,
                    "company_culture": None,  # 全レビューで未回答
                    "employee_relations": 3,
                    "evaluation_system": 3,
                    "promotion_treatment": 3
                }
            },
            {
                "_id": "review_2",
                "individual_average": 4.0,
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": 4,
                    "company_culture": None,  # 全レビューで未回答
                    "employee_relations": 4,
                    "evaluation_system": 4,
                    "promotion_treatment": 4
                }
            }
        ]

        self.mock_db.find_many.return_value = mock_reviews

        summary = await self.calc_service.calculate_company_averages(company_id)

        assert summary.total_reviews == 2
        assert summary.overall_average == 3.5  # (3.0 + 4.0) / 2

        # company_cultureは全て未回答なので0.0
        assert summary.category_averages["company_culture"] == 0.0
        # 他は正常に計算される
        assert summary.category_averages["recommendation"] == 3.5

    @pytest.mark.asyncio
    async def test_update_company_summary(self):
        """企業のレビューサマリー更新"""
        company_id = "company_update"

        summary = ReviewSummary(
            total_reviews=5,
            overall_average=3.8,
            category_averages={
                "recommendation": 4.0,
                "foreign_support": 3.6,
                "company_culture": 3.8,
                "employee_relations": 3.9,
                "evaluation_system": 3.7,
                "promotion_treatment": 3.5
            },
            last_updated=datetime.utcnow()
        )

        self.mock_db.update_one.return_value = True

        result = await self.calc_service.update_company_summary(company_id, summary)

        assert result is True

        # データベース更新の確認
        self.mock_db.update_one.assert_called_once()
        call_args = self.mock_db.update_one.call_args

        assert call_args[0][0] == "companies"  # collection
        assert call_args[0][1] == {"_id": company_id}  # filter
        assert "review_summary" in call_args[0][2]  # update data

    @pytest.mark.asyncio
    async def test_recalculate_company_averages_full_flow(self):
        """企業平均点の再計算（全フロー）"""
        company_id = "company_recalc"

        # レビューデータをモック
        mock_reviews = [
            {
                "_id": "review_1",
                "individual_average": 3.0,
                "ratings": {
                    "recommendation": 3,
                    "foreign_support": 3,
                    "company_culture": 3,
                    "employee_relations": 3,
                    "evaluation_system": 3,
                    "promotion_treatment": 3
                }
            }
        ]

        self.mock_db.find_many.return_value = mock_reviews
        self.mock_db.update_one.return_value = True

        result = await self.calc_service.recalculate_company_averages(company_id)

        assert result is True

        # find_many（レビュー取得）とupdate_one（サマリー更新）が呼ばれる
        self.mock_db.find_many.assert_called_once()
        self.mock_db.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_category_averages_rounding(self):
        """項目別平均の四捨五入テスト"""
        company_id = "company_rounding"

        mock_reviews = [
            {
                "_id": "review_1",
                "individual_average": 3.3,
                "ratings": {
                    "recommendation": 3,
                    "foreign_support": 3,
                    "company_culture": 4,
                    "employee_relations": 3,
                    "evaluation_system": 3,
                    "promotion_treatment": 3
                }
            },
            {
                "_id": "review_2",
                "individual_average": 3.7,
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": 4,
                    "company_culture": 3,
                    "employee_relations": 4,
                    "evaluation_system": 4,
                    "promotion_treatment": 3
                }
            }
        ]

        self.mock_db.find_many.return_value = mock_reviews

        summary = await self.calc_service.calculate_company_averages(company_id)

        # recommendation: (3+4)/2 = 3.5 (そのまま)
        assert summary.category_averages["recommendation"] == 3.5
        # company_culture: (4+3)/2 = 3.5 (そのまま)
        assert summary.category_averages["company_culture"] == 3.5