"""
Test: Review Aggregation Service Extended (Task 8.1)

8カテゴリー集計サービスのテスト:
- 新8カテゴリーの平均計算
- NPS計算（Promoters/Passives/Detractors）
- 業界ベンチマーク計算
- キャッシュ無効化
- 旧6カテゴリーとの後方互換性

Requirements: 12.1～12.5
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.services.review_aggregation_service import ReviewAggregationService


def make_new_schema_review(**overrides):
    """新スキーマのレビューデータを作成するヘルパー"""
    base = {
        "_id": "review-id-1",
        "company_id": "company-123",
        "user_id": "user-1",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        # 新8カテゴリーフィールド
        "comp_salary": 4,
        "comp_bonus": 3,
        "comp_benefits": 4,
        "comp_equity": 3,
        "wlb_hours": 4,
        "wlb_vacation": 5,
        "wlb_flexibility": 4,
        "wlb_overall": 4,
        "culture_atmosphere": 4,
        "culture_diversity": 3,
        "culture_ethics": 4,
        "culture_communication": 4,
        "career_growth": 4,
        "career_training": 3,
        "career_path": 4,
        "career_mentorship": 4,
        "mgmt_vision": 3,
        "mgmt_decision": 4,
        "mgmt_structure": 3,
        "mgmt_manager": 4,
        "perf_fairness": 3,
        "perf_feedback": 4,
        "perf_promotion": 3,
        "perf_linkage": 4,
        "env_office": 4,
        "env_relationships": 5,
        "env_stress": 3,
        "env_health": 4,
        "biz_future": 4,
        "biz_pride": 5,
        "biz_social_impact": 4,
        "biz_financial": 3,
        # 総合評価
        "overall_satisfaction": 4,
        "overall_nps": 8,
        # 旧スキーマ
        "ratings": {},
        "individual_average": 0.0,
    }
    base.update(overrides)
    return base


class TestCalculateNewCategoryAverages:
    """新8カテゴリーの平均計算テスト"""

    def test_calculate_compensation_average(self):
        """待遇・報酬カテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(comp_salary=4, comp_bonus=3, comp_benefits=4, comp_equity=3),
            make_new_schema_review(comp_salary=5, comp_bonus=4, comp_benefits=5, comp_equity=4),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "compensation" in result
        # (4+3+4+3)/4 = 3.5, (5+4+5+4)/4 = 4.5 → 平均 4.0
        assert abs(result["compensation"] - 4.0) < 0.01

    def test_calculate_wlb_average(self):
        """ワークライフバランスカテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(wlb_hours=4, wlb_vacation=5, wlb_flexibility=4, wlb_overall=4),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "work_life_balance" in result
        # (4+5+4+4)/4 = 4.25
        assert abs(result["work_life_balance"] - 4.25) < 0.01

    def test_calculate_culture_average(self):
        """企業文化カテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(
                culture_atmosphere=4, culture_diversity=3,
                culture_ethics=4, culture_communication=4
            ),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "culture" in result
        # (4+3+4+4)/4 = 3.75
        assert abs(result["culture"] - 3.75) < 0.01

    def test_calculate_career_average(self):
        """キャリア・成長カテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(
                career_growth=4, career_training=3,
                career_path=4, career_mentorship=4
            ),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "career_development" in result
        # (4+3+4+4)/4 = 3.75
        assert abs(result["career_development"] - 3.75) < 0.01

    def test_calculate_management_average(self):
        """マネジメントカテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(
                mgmt_vision=3, mgmt_decision=4,
                mgmt_structure=3, mgmt_manager=4
            ),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "management" in result
        # (3+4+3+4)/4 = 3.5
        assert abs(result["management"] - 3.5) < 0.01

    def test_calculate_performance_average(self):
        """評価制度カテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(
                perf_fairness=3, perf_feedback=4,
                perf_promotion=3, perf_linkage=4
            ),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "performance_system" in result
        # (3+4+3+4)/4 = 3.5
        assert abs(result["performance_system"] - 3.5) < 0.01

    def test_calculate_environment_average(self):
        """職場環境カテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(
                env_office=4, env_relationships=5,
                env_stress=3, env_health=4
            ),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "work_environment" in result
        # (4+5+3+4)/4 = 4.0
        assert abs(result["work_environment"] - 4.0) < 0.01

    def test_calculate_business_average(self):
        """事業・製品カテゴリーの平均計算"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(
                biz_future=4, biz_pride=5,
                biz_social_impact=4, biz_financial=3
            ),
        ]
        result = service.calculate_new_category_averages(reviews)
        assert "business_product" in result
        # (4+5+4+3)/4 = 4.0
        assert abs(result["business_product"] - 4.0) < 0.01

    def test_all_8_categories_returned(self):
        """全8カテゴリーが返されること"""
        service = ReviewAggregationService()
        reviews = [make_new_schema_review()]
        result = service.calculate_new_category_averages(reviews)
        expected_keys = [
            "compensation",
            "work_life_balance",
            "culture",
            "career_development",
            "management",
            "performance_system",
            "work_environment",
            "business_product",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_null_ratings_excluded_from_average(self):
        """Noneのレーティングは平均計算から除外される"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(comp_salary=4, comp_bonus=None, comp_benefits=4, comp_equity=None),
        ]
        result = service.calculate_new_category_averages(reviews)
        # Noneを除外: (4+4)/2 = 4.0
        assert abs(result["compensation"] - 4.0) < 0.01

    def test_empty_reviews_returns_zero_averages(self):
        """レビューが0件の場合は全カテゴリー0.0を返す"""
        service = ReviewAggregationService()
        result = service.calculate_new_category_averages([])
        expected_keys = [
            "compensation", "work_life_balance", "culture", "career_development",
            "management", "performance_system", "work_environment", "business_product",
        ]
        for key in expected_keys:
            assert key in result
            assert result[key] == 0.0

    def test_multiple_reviews_averaged_correctly(self):
        """複数レビューの平均が正しく計算される"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(comp_salary=2, comp_bonus=2, comp_benefits=2, comp_equity=2),
            make_new_schema_review(comp_salary=4, comp_bonus=4, comp_benefits=4, comp_equity=4),
        ]
        result = service.calculate_new_category_averages(reviews)
        # 全評価 = 2, 2, 2, 2, 4, 4, 4, 4 → カテゴリ1の平均 = 2.0, カテゴリ2の平均 = 4.0 → 総計平均 = 3.0
        assert abs(result["compensation"] - 3.0) < 0.01


class TestCalculateNPS:
    """NPS計算テスト"""

    def test_nps_promoters_only(self):
        """全員がPromoters(9-10)の場合、NPS = 100"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(overall_nps=9),
            make_new_schema_review(overall_nps=10),
            make_new_schema_review(overall_nps=10),
        ]
        result = service.calculate_nps(reviews)
        assert result["nps_score"] == 100
        assert result["promoters_count"] == 3
        assert result["passives_count"] == 0
        assert result["detractors_count"] == 0

    def test_nps_detractors_only(self):
        """全員がDetractors(0-6)の場合、NPS = -100"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(overall_nps=0),
            make_new_schema_review(overall_nps=3),
            make_new_schema_review(overall_nps=6),
        ]
        result = service.calculate_nps(reviews)
        assert result["nps_score"] == -100
        assert result["promoters_count"] == 0
        assert result["detractors_count"] == 3

    def test_nps_passives_only(self):
        """全員がPassives(7-8)の場合、NPS = 0"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(overall_nps=7),
            make_new_schema_review(overall_nps=8),
        ]
        result = service.calculate_nps(reviews)
        assert result["nps_score"] == 0
        assert result["passives_count"] == 2

    def test_nps_mixed_calculation(self):
        """混在ケース: NPS = (promoters - detractors) / total * 100"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(overall_nps=9),   # Promoter
            make_new_schema_review(overall_nps=10),  # Promoter
            make_new_schema_review(overall_nps=7),   # Passive
            make_new_schema_review(overall_nps=4),   # Detractor
        ]
        result = service.calculate_nps(reviews)
        # NPS = (2 - 1) / 4 * 100 = 25
        assert result["nps_score"] == 25
        assert result["promoters_count"] == 2
        assert result["passives_count"] == 1
        assert result["detractors_count"] == 1
        assert result["total_count"] == 4

    def test_nps_empty_reviews(self):
        """レビューが0件の場合"""
        service = ReviewAggregationService()
        result = service.calculate_nps([])
        assert result["nps_score"] == 0
        assert result["total_count"] == 0

    def test_nps_excludes_null_values(self):
        """overall_nps がNullのレビューは除外"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(overall_nps=10),  # Promoter
            make_new_schema_review(overall_nps=None),  # Null (旧スキーマ)
        ]
        result = service.calculate_nps(reviews)
        # Nullを除外: 1件のみ → NPS = 100
        assert result["nps_score"] == 100
        assert result["total_count"] == 1

    def test_nps_result_has_required_fields(self):
        """NPSの結果に必須フィールドが含まれる"""
        service = ReviewAggregationService()
        reviews = [make_new_schema_review(overall_nps=8)]
        result = service.calculate_nps(reviews)
        required_fields = ["nps_score", "promoters_count", "passives_count",
                           "detractors_count", "total_count"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_nps_boundary_values(self):
        """NPS境界値テスト: 6はDetractor, 7はPassive, 8はPassive, 9はPromoter"""
        service = ReviewAggregationService()
        reviews = [
            make_new_schema_review(overall_nps=6),  # Detractor (max)
            make_new_schema_review(overall_nps=7),  # Passive (min)
            make_new_schema_review(overall_nps=8),  # Passive (max)
            make_new_schema_review(overall_nps=9),  # Promoter (min)
        ]
        result = service.calculate_nps(reviews)
        assert result["detractors_count"] == 1
        assert result["passives_count"] == 2
        assert result["promoters_count"] == 1


class TestGetCompanyAggregations:
    """企業集計（新スキーマ対応版）テスト"""

    def test_get_company_aggregations_method_exists(self):
        """get_company_aggregations メソッドが存在すること"""
        service = ReviewAggregationService()
        assert hasattr(service, "get_company_aggregations")

    @pytest.mark.asyncio
    async def test_get_company_aggregations_returns_correct_structure(self):
        """集計結果が正しい構造を返す"""
        mock_db = AsyncMock()
        mock_db.find_many = AsyncMock(return_value=[
            make_new_schema_review(overall_nps=9),
            make_new_schema_review(overall_nps=7),
        ])

        service = ReviewAggregationService(mock_db)
        result = await service.get_company_aggregations("company-123")

        assert result["success"] is True
        assert "overall_rating" in result
        assert "nps_score" in result
        assert "review_count" in result
        assert "category_scores" in result
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_get_company_aggregations_category_scores_has_8_categories(self):
        """category_scores に8カテゴリーが含まれること"""
        mock_db = AsyncMock()
        mock_db.find_many = AsyncMock(return_value=[make_new_schema_review()])

        service = ReviewAggregationService(mock_db)
        result = await service.get_company_aggregations("company-123")

        category_scores = result.get("category_scores", {})
        expected_categories = [
            "compensation",
            "work_life_balance",
            "culture",
            "career_development",
            "management",
            "performance_system",
            "work_environment",
            "business_product",
        ]
        for cat in expected_categories:
            assert cat in category_scores, f"Missing category: {cat}"

    @pytest.mark.asyncio
    async def test_get_company_aggregations_empty_company(self):
        """レビューが0件の場合の集計"""
        mock_db = AsyncMock()
        mock_db.find_many = AsyncMock(return_value=[])

        service = ReviewAggregationService(mock_db)
        result = await service.get_company_aggregations("company-123")

        assert result["success"] is True
        assert result["review_count"] == 0
        assert result["overall_rating"] == 0.0
        assert result["nps_score"] == 0


class TestGetIndustryBenchmarks:
    """業界ベンチマーク計算テスト"""

    def test_get_industry_benchmarks_method_exists(self):
        """get_industry_benchmarks メソッドが存在すること"""
        service = ReviewAggregationService()
        assert hasattr(service, "get_industry_benchmarks")

    @pytest.mark.asyncio
    async def test_get_industry_benchmarks_returns_category_averages(self):
        """業界平均が全8カテゴリーを返す"""
        mock_db = AsyncMock()
        mock_db.find_many = AsyncMock(return_value=[
            make_new_schema_review(company_id="company-A"),
            make_new_schema_review(company_id="company-B"),
        ])

        service = ReviewAggregationService(mock_db)
        result = await service.get_industry_benchmarks()

        assert result["success"] is True
        assert "benchmarks" in result
        expected_categories = [
            "compensation", "work_life_balance", "culture", "career_development",
            "management", "performance_system", "work_environment", "business_product",
        ]
        for cat in expected_categories:
            assert cat in result["benchmarks"], f"Missing benchmark: {cat}"

    @pytest.mark.asyncio
    async def test_get_industry_benchmarks_no_reviews(self):
        """レビューが0件の場合の業界ベンチマーク"""
        mock_db = AsyncMock()
        mock_db.find_many = AsyncMock(return_value=[])

        service = ReviewAggregationService(mock_db)
        result = await service.get_industry_benchmarks()

        assert result["success"] is True
        # 全カテゴリーが0.0を返す
        for val in result["benchmarks"].values():
            assert val == 0.0


class TestInvalidateCache:
    """キャッシュ無効化テスト"""

    def test_invalidate_cache_method_exists(self):
        """invalidate_cache メソッドが存在すること"""
        service = ReviewAggregationService()
        assert hasattr(service, "invalidate_cache")

    @pytest.mark.asyncio
    async def test_invalidate_cache_clears_company_data(self):
        """キャッシュ無効化が特定企業のデータを削除する"""
        service = ReviewAggregationService()
        # キャッシュに何か入れる
        service._cache = {"company-123": {"data": "some_data"}}
        await service.invalidate_cache("company-123")
        assert "company-123" not in service._cache

    @pytest.mark.asyncio
    async def test_invalidate_cache_does_not_affect_other_companies(self):
        """キャッシュ無効化が他の企業データに影響しない"""
        service = ReviewAggregationService()
        service._cache = {
            "company-123": {"data": "some_data"},
            "company-456": {"data": "other_data"},
        }
        await service.invalidate_cache("company-123")
        assert "company-456" in service._cache


class TestCalculateOverallRating:
    """総合評価計算テスト（新スキーマ対応）"""

    def test_calculate_overall_from_new_schema(self):
        """新スキーマの8カテゴリーから総合評価を計算"""
        service = ReviewAggregationService()
        # 全カテゴリー4.0の場合、総合評価も4.0
        reviews = [
            make_new_schema_review(
                comp_salary=4, comp_bonus=4, comp_benefits=4, comp_equity=4,
                wlb_hours=4, wlb_vacation=4, wlb_flexibility=4, wlb_overall=4,
                culture_atmosphere=4, culture_diversity=4, culture_ethics=4, culture_communication=4,
                career_growth=4, career_training=4, career_path=4, career_mentorship=4,
                mgmt_vision=4, mgmt_decision=4, mgmt_structure=4, mgmt_manager=4,
                perf_fairness=4, perf_feedback=4, perf_promotion=4, perf_linkage=4,
                env_office=4, env_relationships=4, env_stress=4, env_health=4,
                biz_future=4, biz_pride=4, biz_social_impact=4, biz_financial=4,
            )
        ]
        category_avgs = service.calculate_new_category_averages(reviews)
        overall = service.calculate_new_overall_average(category_avgs)
        assert abs(overall - 4.0) < 0.01

    def test_calculate_new_overall_average_method_exists(self):
        """calculate_new_overall_average メソッドが存在すること"""
        service = ReviewAggregationService()
        assert hasattr(service, "calculate_new_overall_average")


class TestBackwardCompatibility:
    """旧6カテゴリースキーマとの後方互換性テスト"""

    def test_old_schema_reviews_still_aggregate(self):
        """旧スキーマのレビューも集計できること"""
        service = ReviewAggregationService()
        old_reviews = [
            {
                "_id": "old-1",
                "company_id": "company-123",
                "is_active": True,
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": 3,
                    "company_culture": 4,
                    "employee_relations": 4,
                    "evaluation_system": 3,
                    "promotion_treatment": 4,
                },
                "individual_average": 3.67,
                "created_at": datetime.now(timezone.utc),
            }
        ]
        # 旧スキーマは新カテゴリーを持たないので0.0を返す
        result = service.calculate_new_category_averages(old_reviews)
        assert isinstance(result, dict)
        # 旧スキーマのレビューには新フィールドがないので全カテゴリー 0.0
        for val in result.values():
            assert val == 0.0

    def test_calculate_category_averages_still_works(self):
        """既存のcalculate_category_averagesメソッドが引き続き動作する"""
        service = ReviewAggregationService()
        reviews = [
            {
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": 3,
                    "company_culture": 4,
                    "employee_relations": 4,
                    "evaluation_system": 3,
                    "promotion_treatment": 4,
                }
            }
        ]
        result = service.calculate_category_averages(reviews)
        assert "recommendation" in result
        assert abs(result["recommendation"] - 4.0) < 0.01
