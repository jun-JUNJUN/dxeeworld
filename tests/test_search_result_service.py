"""
検索結果表示・ソート機能のテスト
"""
import pytest
from unittest.mock import AsyncMock
from src.services.search_result_service import SearchResultService


class TestSearchResultService:
    """SearchResultServiceのテスト"""

    def setup_method(self):
        """各テスト前の準備"""
        self.mock_search_service = AsyncMock()
        self.result_service = SearchResultService(self.mock_search_service)

    @pytest.mark.asyncio
    async def test_format_search_results_basic(self):
        """基本的な検索結果フォーマット"""
        raw_companies = [
            {
                "_id": "company_1",
                "name": "テスト企業A",
                "location": "東京都",
                "review_summary": {
                    "overall_average": 4.2,
                    "total_reviews": 15,
                    "category_averages": {
                        "recommendation": 4.3,
                        "foreign_support": 4.1
                    },
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            }
        ]

        formatted = await self.result_service.format_search_results(raw_companies)

        assert len(formatted) == 1
        company = formatted[0]
        assert company["id"] == "company_1"
        assert company["name"] == "テスト企業A"
        assert company["location"] == "東京都"
        assert company["overall_average"] == 4.2
        assert company["total_reviews"] == 15
        assert "display_summary" in company

    @pytest.mark.asyncio
    async def test_format_search_results_no_reviews(self):
        """レビューサマリーなしの企業"""
        raw_companies = [
            {
                "_id": "company_no_reviews",
                "name": "新規企業",
                "location": "大阪府",
                "review_summary": None
            }
        ]

        formatted = await self.result_service.format_search_results(raw_companies)

        assert len(formatted) == 1
        company = formatted[0]
        assert company["overall_average"] == 0.0
        assert company["total_reviews"] == 0
        assert "レビューなし" in company["display_summary"]

    @pytest.mark.asyncio
    async def test_sort_results_by_overall_average_desc(self):
        """全項目平均点降順ソート"""
        search_params = {
            "sort_by": "overall_average",
            "sort_direction": "desc",
            "name": "テスト"
        }

        # モックの検索結果
        mock_result = {
            "success": True,
            "companies": [
                {"_id": "comp_a", "name": "企業A", "review_summary": {"overall_average": 3.5}},
                {"_id": "comp_b", "name": "企業B", "review_summary": {"overall_average": 4.2}},
                {"_id": "comp_c", "name": "企業C", "review_summary": {"overall_average": 3.8}}
            ],
            "total_count": 3
        }
        self.mock_search_service.search_companies.return_value = mock_result

        result = await self.result_service.get_sorted_search_results(search_params)

        assert result["success"] is True
        assert len(result["companies"]) == 3

        # ソート確認
        search_call_args = self.mock_search_service.search_companies.call_args[0][0]
        assert search_call_args["sort_by"] == "overall_average"
        assert search_call_args["sort_direction"] == "desc"

    @pytest.mark.asyncio
    async def test_sort_results_by_total_reviews_asc(self):
        """レビュー数昇順ソート"""
        search_params = {
            "sort_by": "total_reviews",
            "sort_direction": "asc"
        }

        mock_result = {
            "success": True,
            "companies": [],
            "total_count": 0
        }
        self.mock_search_service.search_companies.return_value = mock_result

        result = await self.result_service.get_sorted_search_results(search_params)

        search_call_args = self.mock_search_service.search_companies.call_args[0][0]
        assert search_call_args["sort_by"] == "total_reviews"
        assert search_call_args["sort_direction"] == "asc"

    @pytest.mark.asyncio
    async def test_sort_results_by_last_updated(self):
        """最終更新日ソート"""
        search_params = {
            "sort_by": "last_updated",
            "sort_direction": "desc"
        }

        mock_result = {
            "success": True,
            "companies": [],
            "total_count": 0
        }
        self.mock_search_service.search_companies.return_value = mock_result

        await self.result_service.get_sorted_search_results(search_params)

        search_call_args = self.mock_search_service.search_companies.call_args[0][0]
        assert search_call_args["sort_by"] == "last_updated"

    @pytest.mark.asyncio
    async def test_sort_results_default_sorting(self):
        """デフォルトソート（全項目平均点降順）"""
        search_params = {"name": "テスト"}  # ソート指定なし

        mock_result = {
            "success": True,
            "companies": [],
            "total_count": 0
        }
        self.mock_search_service.search_companies.return_value = mock_result

        await self.result_service.get_sorted_search_results(search_params)

        search_call_args = self.mock_search_service.search_companies.call_args[0][0]
        assert search_call_args["sort_by"] == "overall_average"
        assert search_call_args["sort_direction"] == "desc"

    @pytest.mark.asyncio
    async def test_paginate_results_first_page(self):
        """ページネーション - 1ページ目"""
        search_params = {
            "page": 1,
            "per_page": 5
        }

        mock_result = {
            "success": True,
            "companies": [{"_id": f"comp_{i}", "name": f"企業{i}"} for i in range(1, 6)],
            "total_count": 23,
            "current_page": 1,
            "total_pages": 5,
            "per_page": 5
        }
        self.mock_search_service.search_companies.return_value = mock_result

        result = await self.result_service.get_paginated_results(search_params)

        assert result["success"] is True
        assert result["current_page"] == 1
        assert result["total_pages"] == 5
        assert result["per_page"] == 5
        assert result["has_next"] is True
        assert result["has_previous"] is False

    @pytest.mark.asyncio
    async def test_paginate_results_middle_page(self):
        """ページネーション - 中間ページ"""
        search_params = {
            "page": 3,
            "per_page": 10
        }

        mock_result = {
            "success": True,
            "companies": [],
            "total_count": 50,
            "current_page": 3,
            "total_pages": 5,
            "per_page": 10
        }
        self.mock_search_service.search_companies.return_value = mock_result

        result = await self.result_service.get_paginated_results(search_params)

        assert result["has_next"] is True
        assert result["has_previous"] is True

    @pytest.mark.asyncio
    async def test_paginate_results_last_page(self):
        """ページネーション - 最終ページ"""
        search_params = {
            "page": 5,
            "per_page": 10
        }

        mock_result = {
            "success": True,
            "companies": [],
            "total_count": 45,
            "current_page": 5,
            "total_pages": 5,
            "per_page": 10
        }
        self.mock_search_service.search_companies.return_value = mock_result

        result = await self.result_service.get_paginated_results(search_params)

        assert result["has_next"] is False
        assert result["has_previous"] is True

    @pytest.mark.asyncio
    async def test_build_display_summary_with_reviews(self):
        """レビューありの企業サマリー表示"""
        company_data = {
            "review_summary": {
                "overall_average": 4.2,
                "total_reviews": 15,
                "category_averages": {
                    "recommendation": 4.3,
                    "foreign_support": 4.1,
                    "company_culture": 4.0
                }
            }
        }

        summary = await self.result_service.build_display_summary(company_data)

        assert "4.2" in summary
        assert "15件" in summary
        assert "総合推薦度" in summary or "recommendation" in summary

    @pytest.mark.asyncio
    async def test_build_display_summary_no_reviews(self):
        """レビューなしの企業サマリー表示"""
        company_data = {
            "review_summary": None
        }

        summary = await self.result_service.build_display_summary(company_data)

        assert "レビューなし" in summary

    @pytest.mark.asyncio
    async def test_validate_sort_params_valid(self):
        """有効なソートパラメータの検証"""
        valid_params = {
            "sort_by": "overall_average",
            "sort_direction": "desc"
        }

        normalized = await self.result_service.validate_and_normalize_sort_params(valid_params)

        assert normalized["sort_by"] == "overall_average"
        assert normalized["sort_direction"] == "desc"

    @pytest.mark.asyncio
    async def test_validate_sort_params_invalid_field(self):
        """無効なソートフィールドの正規化"""
        invalid_params = {
            "sort_by": "invalid_field",
            "sort_direction": "asc"
        }

        normalized = await self.result_service.validate_and_normalize_sort_params(invalid_params)

        # デフォルトにフォールバック
        assert normalized["sort_by"] == "overall_average"
        assert normalized["sort_direction"] == "asc"

    @pytest.mark.asyncio
    async def test_validate_sort_params_invalid_direction(self):
        """無効なソート方向の正規化"""
        invalid_params = {
            "sort_by": "total_reviews",
            "sort_direction": "invalid"
        }

        normalized = await self.result_service.validate_and_normalize_sort_params(invalid_params)

        assert normalized["sort_by"] == "total_reviews"
        assert normalized["sort_direction"] == "desc"  # デフォルト

    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """検索サービスエラー時の処理"""
        search_params = {"name": "テスト"}

        # 検索サービスでエラー
        self.mock_search_service.search_companies.return_value = {
            "success": False,
            "error_code": "database_error"
        }

        result = await self.result_service.get_sorted_search_results(search_params)

        assert result["success"] is False
        assert result["error_code"] == "database_error"