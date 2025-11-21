"""
ReviewAggregationService のユニットテスト
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from bson import ObjectId
from src.services.review_aggregation_service import ReviewAggregationService
from src.database import DatabaseService


@pytest_asyncio.fixture
async def service_and_db():
    """テスト用サービスインスタンスとデータベース"""
    db = DatabaseService()
    await db.connect()

    # テストデータをクリーンアップ
    await db.delete_many("reviews", {})
    await db.delete_many("companies", {})

    service = ReviewAggregationService(db)

    yield service, db

    # テスト後のクリーンアップ
    await db.delete_many("reviews", {})
    await db.delete_many("companies", {})
    await db.close()


class TestReviewAggregationService:
    """ReviewAggregationService のテストクラス"""

    @pytest.mark.asyncio
    async def test_calculate_category_averages_with_none_values(self, service_and_db):
        """None値を含むレビューの集計が正しく計算される"""
        service, _ = service_and_db
        reviews = [
            {
                "ratings": {
                    "recommendation": 4,
                    "foreign_support": None,
                    "company_culture": 3,
                    "employee_relations": 5,
                    "evaluation_system": None,
                    "promotion_treatment": 4
                }
            },
            {
                "ratings": {
                    "recommendation": 5,
                    "foreign_support": 2,
                    "company_culture": None,
                    "employee_relations": 4,
                    "evaluation_system": 3,
                    "promotion_treatment": None
                }
            }
        ]

        averages = service.calculate_category_averages(reviews)

        # recommendation: (4 + 5) / 2 = 4.5
        assert averages["recommendation"] == 4.5
        # foreign_support: 2 / 1 = 2.0（None除外）
        assert averages["foreign_support"] == 2.0
        # company_culture: 3 / 1 = 3.0（None除外）
        assert averages["company_culture"] == 3.0
        # employee_relations: (5 + 4) / 2 = 4.5
        assert averages["employee_relations"] == 4.5
        # evaluation_system: 3 / 1 = 3.0（None除外）
        assert averages["evaluation_system"] == 3.0
        # promotion_treatment: 4 / 1 = 4.0（None除外）
        assert averages["promotion_treatment"] == 4.0

    @pytest.mark.asyncio
    async def test_calculate_category_averages_all_none(self, service_and_db):
        """すべてNoneの場合は0.0を返す"""
        service, _ = service_and_db
        reviews = [
            {
                "ratings": {
                    "recommendation": None,
                    "foreign_support": None,
                    "company_culture": None,
                    "employee_relations": None,
                    "evaluation_system": None,
                    "promotion_treatment": None
                }
            }
        ]

        averages = service.calculate_category_averages(reviews)

        for category, value in averages.items():
            assert value == 0.0, f"Category {category} should be 0.0 when all values are None"

    @pytest.mark.asyncio
    async def test_calculate_overall_average(self, service_and_db):
        """総合評価平均が全カテゴリの平均値の平均として計算される"""
        service, _ = service_and_db
        category_averages = {
            "recommendation": 4.0,
            "foreign_support": 3.0,
            "company_culture": 5.0,
            "employee_relations": 4.0,
            "evaluation_system": 3.5,
            "promotion_treatment": 4.5
        }

        overall = service.calculate_overall_average(category_averages)

        # (4.0 + 3.0 + 5.0 + 4.0 + 3.5 + 4.5) / 6 = 4.0
        assert overall == 4.0

    @pytest.mark.asyncio
    async def test_calculate_overall_average_with_zeros(self, service_and_db):
        """0.0を含むカテゴリ平均でも正しく計算される"""
        service, _ = service_and_db
        category_averages = {
            "recommendation": 4.0,
            "foreign_support": 0.0,  # None値のみのカテゴリ
            "company_culture": 3.0,
            "employee_relations": 0.0,
            "evaluation_system": 5.0,
            "promotion_treatment": 4.0
        }

        overall = service.calculate_overall_average(category_averages)

        # (4.0 + 0.0 + 3.0 + 0.0 + 5.0 + 4.0) / 6 = 2.666... ≈ 2.67
        assert round(overall, 2) == 2.67

    @pytest.mark.asyncio
    async def test_aggregate_company_reviews_with_no_reviews(self, service_and_db):
        """レビューが0件の企業の集計が正しく処理される"""
        service, db = service_and_db
        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業A",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # レビューが0件の企業を集計
        result = await service.aggregate_company_reviews(str(company_id))

        assert result["success"] is True
        assert result["total_reviews"] == 0
        assert result["overall_average"] == 0.0
        assert result["category_averages"]["recommendation"] == 0.0
        assert result["last_review_date"] is None

    @pytest.mark.asyncio
    async def test_aggregate_company_reviews_with_multiple_reviews(self, service_and_db):
        """複数レビューの集計が正しく計算される"""
        service, db = service_and_db
        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業B",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # レビューを3件作成
        review_dates = [
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 2, 1, tzinfo=timezone.utc),
            datetime(2024, 3, 1, tzinfo=timezone.utc)  # 最新
        ]

        for i, review_date in enumerate(review_dates):
            await db.create("reviews", {
                "company_id": ObjectId(company_id),
                "user_id": f"user_{i}",
                "employment_status": "former",
                "ratings": {
                    "recommendation": 3 + i,  # 3, 4, 5
                    "foreign_support": 4,
                    "company_culture": 3,
                    "employee_relations": 5,
                    "evaluation_system": 4,
                    "promotion_treatment": 3
                },
                "comments": {},
                "individual_average": 3.5,
                "answered_count": 6,
                "is_active": True,
                "created_at": review_date,
                "updated_at": review_date,
                "language": "ja"
            })

        # 集計実行
        result = await service.aggregate_company_reviews(str(company_id))

        assert result["success"] is True
        assert result["total_reviews"] == 3
        # recommendation の平均: (3 + 4 + 5) / 3 = 4.0
        assert result["category_averages"]["recommendation"] == 4.0
        # foreign_support の平均: (4 + 4 + 4) / 3 = 4.0
        assert result["category_averages"]["foreign_support"] == 4.0
        # 総合平均: (4.0 + 4.0 + 3.0 + 5.0 + 4.0 + 3.0) / 6 = 3.833... ≈ 3.83
        assert round(result["overall_average"], 2) == 3.83
        # 最終レビュー日時（MongoDBからはタイムゾーンなしで返ってくるため、日時のみで比較）
        assert result["last_review_date"].replace(tzinfo=None) == review_dates[2].replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_aggregate_excludes_inactive_reviews(self, service_and_db):
        """is_active=False のレビューは集計から除外される"""
        service, db = service_and_db
        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業C",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # アクティブなレビューを1件作成
        await db.create("reviews", {
            "company_id": ObjectId(company_id),
            "user_id": "user_1",
            "employment_status": "former",
            "ratings": {"recommendation": 5, "foreign_support": 5, "company_culture": 5,
                       "employee_relations": 5, "evaluation_system": 5, "promotion_treatment": 5},
            "comments": {},
            "individual_average": 5.0,
            "answered_count": 6,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "language": "ja"
        })

        # 非アクティブなレビューを1件作成（集計対象外）
        await db.create("reviews", {
            "company_id": ObjectId(company_id),
            "user_id": "user_2",
            "employment_status": "former",
            "ratings": {"recommendation": 1, "foreign_support": 1, "company_culture": 1,
                       "employee_relations": 1, "evaluation_system": 1, "promotion_treatment": 1},
            "comments": {},
            "individual_average": 1.0,
            "answered_count": 6,
            "is_active": False,  # 非アクティブ
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "language": "ja"
        })

        # 集計実行
        result = await service.aggregate_company_reviews(str(company_id))

        assert result["success"] is True
        assert result["total_reviews"] == 1  # アクティブなレビューのみカウント
        assert result["overall_average"] == 5.0  # 非アクティブなレビューは除外

    @pytest.mark.asyncio
    async def test_update_company_review_summary(self, service_and_db):
        """企業の review_summary を更新する"""
        service, db = service_and_db
        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業D",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # レビューを作成
        await db.create("reviews", {
            "company_id": ObjectId(company_id),
            "user_id": "user_1",
            "employment_status": "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": 5,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 4
            },
            "comments": {},
            "individual_average": 3.8,
            "answered_count": 6,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "language": "ja"
        })

        # 集計を実行し、企業レコードを更新
        result = await service.aggregate_and_update_company(str(company_id))

        assert result["success"] is True
        assert result["updated"] is True

        # 企業レコードを取得して review_summary が更新されているか確認
        company = await db.find_one("companies", {"_id": ObjectId(company_id)})
        assert company is not None
        assert "review_summary" in company
        assert company["review_summary"]["total_reviews"] == 1
        assert company["review_summary"]["overall_average"] == 3.8333333333333335  # (4+3+5+4+3+4)/6
        assert company["review_summary"]["category_averages"]["recommendation"] == 4.0
        assert company["review_summary"]["last_review_date"] is not None

    @pytest.mark.asyncio
    async def test_update_company_review_summary_idempotent(self, service_and_db):
        """集計処理の冪等性を確認（複数回実行しても結果は同じ）"""
        service, db = service_and_db
        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業E",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # レビューを作成
        await db.create("reviews", {
            "company_id": ObjectId(company_id),
            "user_id": "user_1",
            "employment_status": "former",
            "ratings": {
                "recommendation": 3,
                "foreign_support": 4,
                "company_culture": 3,
                "employee_relations": 5,
                "evaluation_system": 4,
                "promotion_treatment": 3
            },
            "comments": {},
            "individual_average": 3.7,
            "answered_count": 6,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "language": "ja"
        })

        # 1回目の集計
        result1 = await service.aggregate_and_update_company(str(company_id))
        company1 = await db.find_one("companies", {"_id": ObjectId(company_id)})

        # 2回目の集計（冪等性の確認）
        result2 = await service.aggregate_and_update_company(str(company_id))
        company2 = await db.find_one("companies", {"_id": ObjectId(company_id)})

        assert result1["success"] is True
        assert result2["success"] is True

        # 集計結果は同じであることを確認
        assert company1["review_summary"]["total_reviews"] == company2["review_summary"]["total_reviews"]
        assert company1["review_summary"]["overall_average"] == company2["review_summary"]["overall_average"]
        assert company1["review_summary"]["category_averages"] == company2["review_summary"]["category_averages"]

    @pytest.mark.asyncio
    async def test_update_company_review_summary_error_handling(self, service_and_db):
        """集計エラー時のエラーハンドリング"""
        service, db = service_and_db

        # 存在しない企業IDで集計を試行
        result = await service.aggregate_and_update_company("000000000000000000000000")

        # エラーが適切に処理されることを確認
        assert result["success"] is True  # 集計自体は成功（レビューが0件）
        assert result["total_reviews"] == 0
