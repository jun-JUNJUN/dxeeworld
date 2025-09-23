"""
企業検索システムのテスト
"""
import pytest
from unittest.mock import AsyncMock
from src.services.company_search_service import CompanySearchService


class TestCompanySearchService:
    """CompanySearchServiceのテスト"""

    def setup_method(self):
        """各テスト前の準備"""
        self.mock_db = AsyncMock()
        self.search_service = CompanySearchService(self.mock_db)

    @pytest.mark.asyncio
    async def test_search_by_name_partial_match(self):
        """企業名部分一致検索"""
        # モックデータ設定
        mock_companies = [
            {
                "_id": "company_1",
                "name": "株式会社ABC商事",
                "location": "東京都",
                "review_summary": {
                    "overall_average": 4.2,
                    "total_reviews": 15
                }
            },
            {
                "_id": "company_2",
                "name": "ABC技術開発",
                "location": "大阪府",
                "review_summary": {
                    "overall_average": 3.8,
                    "total_reviews": 8
                }
            }
        ]
        self.mock_db.find_many.return_value = mock_companies
        self.mock_db.count_documents.return_value = 2

        # 検索実行
        search_params = {"name": "ABC"}
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is True
        assert len(result["companies"]) == 2
        assert result["total_count"] == 2

        # データベース呼び出し確認
        call_args = self.mock_db.find_many.call_args[0]
        assert "$regex" in call_args[1]["name"]
        assert "ABC" in call_args[1]["name"]["$regex"]

    @pytest.mark.asyncio
    async def test_search_by_location(self):
        """所在地での検索"""
        mock_companies = [
            {
                "_id": "company_tokyo_1",
                "name": "東京企業A",
                "location": "東京都渋谷区",
                "review_summary": {"overall_average": 4.0, "total_reviews": 10}
            }
        ]
        self.mock_db.find_many.return_value = mock_companies
        self.mock_db.count_documents.return_value = 1

        search_params = {"location": "東京"}
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is True
        assert len(result["companies"]) == 1

        # データベース検索条件確認
        call_args = self.mock_db.find_many.call_args[0]
        assert "$regex" in call_args[1]["location"]

    @pytest.mark.asyncio
    async def test_search_by_rating_range(self):
        """評価点数範囲での絞り込み"""
        mock_companies = [
            {
                "_id": "high_rated",
                "name": "高評価企業",
                "location": "神奈川県",
                "review_summary": {"overall_average": 4.5, "total_reviews": 20}
            }
        ]
        self.mock_db.find_many.return_value = mock_companies
        self.mock_db.count_documents.return_value = 1

        search_params = {
            "min_rating": 4.0,
            "max_rating": 5.0
        }
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is True

        # 評価範囲での検索条件確認
        call_args = self.mock_db.find_many.call_args[0]
        rating_filter = call_args[1]["review_summary.overall_average"]
        assert "$gte" in rating_filter
        assert "$lte" in rating_filter
        assert rating_filter["$gte"] == 4.0
        assert rating_filter["$lte"] == 5.0

    @pytest.mark.asyncio
    async def test_search_combined_conditions(self):
        """複合検索条件のAND結合"""
        mock_companies = [
            {
                "_id": "matching_company",
                "name": "東京ABC株式会社",
                "location": "東京都新宿区",
                "review_summary": {"overall_average": 4.2, "total_reviews": 12}
            }
        ]
        self.mock_db.find_many.return_value = mock_companies
        self.mock_db.count_documents.return_value = 1

        search_params = {
            "name": "ABC",
            "location": "東京",
            "min_rating": 4.0
        }
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is True

        # 複合条件の確認
        call_args = self.mock_db.find_many.call_args[0]
        search_filter = call_args[1]

        assert "name" in search_filter
        assert "location" in search_filter
        assert "review_summary.overall_average" in search_filter

    @pytest.mark.asyncio
    async def test_search_with_pagination(self):
        """ページネーション機能"""
        # 3つの企業データ
        mock_companies = [
            {"_id": f"company_{i}", "name": f"企業{i}", "location": "東京都"}
            for i in range(1, 4)
        ]
        self.mock_db.find_many.return_value = mock_companies[:2]  # 2件取得
        self.mock_db.count_documents.return_value = 10  # 総件数

        search_params = {
            "page": 1,
            "per_page": 2
        }
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is True
        assert len(result["companies"]) == 2
        assert result["total_count"] == 10
        assert result["current_page"] == 1
        assert result["total_pages"] == 5

        # ページネーションのデータベース呼び出し確認
        call_args = self.mock_db.find_many.call_args
        assert "skip" in call_args[1]
        assert "limit" in call_args[1]
        assert call_args[1]["skip"] == 0  # (page-1) * per_page
        assert call_args[1]["limit"] == 2

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """検索結果なしの場合"""
        self.mock_db.find_many.return_value = []
        self.mock_db.count_documents.return_value = 0

        search_params = {"name": "存在しない企業"}
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is True
        assert len(result["companies"]) == 0
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_search_invalid_rating_range(self):
        """無効な評価範囲での検索"""
        search_params = {
            "min_rating": 5.0,
            "max_rating": 3.0  # min > max
        }

        result = await self.search_service.search_companies(search_params)

        assert result["success"] is False
        assert result["error_code"] == "validation_error"
        assert any("Min rating cannot be greater than max rating" in error
                  for error in result["errors"])

    @pytest.mark.asyncio
    async def test_build_search_filter_empty_params(self):
        """空の検索パラメータでのフィルタ構築"""
        search_filter = await self.search_service.build_search_filter({})

        # 基本フィルタのみ（レビューサマリー存在チェック）
        assert "review_summary" in search_filter
        assert search_filter["review_summary"]["$exists"] is True

    @pytest.mark.asyncio
    async def test_build_search_filter_name_escaping(self):
        """企業名検索での特殊文字エスケープ"""
        search_params = {"name": "ABC.+*?[]{}()^$|\\"}
        search_filter = await self.search_service.build_search_filter(search_params)

        # 正規表現特殊文字がエスケープされていることを確認
        regex_pattern = search_filter["name"]["$regex"]
        assert "\\." in regex_pattern
        assert "\\+" in regex_pattern

    @pytest.mark.asyncio
    async def test_validate_search_params_valid(self):
        """有効な検索パラメータのバリデーション"""
        valid_params = {
            "name": "テスト企業",
            "location": "東京都",
            "min_rating": 3.0,
            "max_rating": 5.0,
            "page": 1,
            "per_page": 20
        }

        errors = await self.search_service.validate_search_params(valid_params)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_search_params_invalid_pagination(self):
        """無効なページネーションパラメータ"""
        invalid_params = {
            "page": 0,      # 1以上である必要
            "per_page": 101 # 100以下である必要
        }

        errors = await self.search_service.validate_search_params(invalid_params)
        assert len(errors) >= 2
        assert any("page" in error for error in errors)
        assert any("per_page" in error for error in errors)

    @pytest.mark.asyncio
    async def test_search_database_error(self):
        """データベースエラー時の処理"""
        self.mock_db.find_many.side_effect = Exception("Database connection error")

        search_params = {"name": "テスト"}
        result = await self.search_service.search_companies(search_params)

        assert result["success"] is False
        assert "database_error" in result["error_code"]