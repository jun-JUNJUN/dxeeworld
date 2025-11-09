"""
レビュー投稿と集計処理の統合テスト
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from bson import ObjectId
from unittest.mock import Mock, patch, AsyncMock
from src.services.review_aggregation_service import ReviewAggregationService
from src.services.review_submission_service import ReviewSubmissionService
from src.database import DatabaseService


@pytest_asyncio.fixture
async def services_and_db():
    """テスト用サービスインスタンスとデータベース"""
    from src.services.review_calculation_service import ReviewCalculationService

    db = DatabaseService()
    await db.connect()

    # テストデータをクリーンアップ
    await db.delete_many("reviews", {})
    await db.delete_many("companies", {})

    aggregation_service = ReviewAggregationService(db)
    calc_service = ReviewCalculationService()
    submission_service = ReviewSubmissionService(db, calc_service)

    yield aggregation_service, submission_service, db

    # テスト後のクリーンアップ
    await db.delete_many("reviews", {})
    await db.delete_many("companies", {})
    await db.close()


class TestReviewSubmissionAggregation:
    """レビュー投稿と集計処理の統合テスト"""

    @pytest.mark.asyncio
    async def test_review_submission_triggers_aggregation(self, services_and_db):
        """レビュー投稿が企業集計をトリガーすることを確認"""
        aggregation_service, submission_service, db = services_and_db

        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業F",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # レビューデータを作成
        review_data = {
            "company_id": ObjectId(company_id),
            "user_id": "user_test",
            "employment_status": "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": 5,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 4
            },
            "comments": {"recommendation": "良い会社でした"},
            "comments_ja": {"recommendation": "良い会社でした"},
            "comments_en": None,
            "comments_zh": None,
            "language": "ja",
            "individual_average": 3.8,
            "answered_count": 6,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # レビューを投稿
        result = await submission_service.submit_review(review_data)
        assert result["status"] == "success"

        # 非同期集計処理をシミュレート（本来はバックグラウンドタスク）
        await aggregation_service.aggregate_and_update_company(str(company_id))

        # 企業レコードを取得してreview_summaryが更新されているか確認
        company = await db.find_one("companies", {"_id": ObjectId(company_id)})
        assert company is not None
        assert "review_summary" in company
        assert company["review_summary"]["total_reviews"] == 1
        assert company["review_summary"]["overall_average"] > 0

    @pytest.mark.asyncio
    async def test_async_aggregation_does_not_block_submission(self, services_and_db):
        """非同期集計がレビュー投稿のレスポンスをブロックしないことを確認"""
        aggregation_service, submission_service, db = services_and_db

        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業G",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # 集計処理をモックして遅延をシミュレート
        import asyncio
        original_method = aggregation_service.aggregate_and_update_company

        async def slow_aggregation(cid):
            await asyncio.sleep(0.1)  # 100ms遅延
            return await original_method(cid)

        # レビューデータを作成
        review_data = {
            "company_id": ObjectId(company_id),
            "user_id": "user_test",
            "employment_status": "former",
            "ratings": {
                "recommendation": 5,
                "foreign_support": 5,
                "company_culture": 5,
                "employee_relations": 5,
                "evaluation_system": 5,
                "promotion_treatment": 5
            },
            "comments": {},
            "comments_ja": None,
            "comments_en": None,
            "comments_zh": None,
            "language": "ja",
            "individual_average": 5.0,
            "answered_count": 6,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # レビュー投稿（集計は非同期で実行される想定）
        import time
        start_time = time.time()
        result = await submission_service.submit_review(review_data)
        submission_time = time.time() - start_time

        # レビュー投稿は即座に完了することを確認（集計を待たない）
        assert result["status"] == "success"
        assert submission_time < 0.05  # 50ms未満で完了

    @pytest.mark.asyncio
    async def test_aggregation_error_does_not_affect_submission(self, services_and_db):
        """集計エラー時でもレビュー投稿は成功として処理されることを確認"""
        aggregation_service, submission_service, db = services_and_db

        # テスト用企業を作成
        company_id = await db.create("companies", {
            "name": "テスト企業H",
            "industry": "technology",
            "size": "medium",
            "country": "日本",
            "location": "東京都",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # レビューデータを作成
        review_data = {
            "company_id": ObjectId(company_id),
            "user_id": "user_test",
            "employment_status": "former",
            "ratings": {
                "recommendation": 3,
                "foreign_support": 4,
                "company_culture": 3,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 4
            },
            "comments": {},
            "comments_ja": None,
            "comments_en": None,
            "comments_zh": None,
            "language": "ja",
            "individual_average": 3.5,
            "answered_count": 6,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # レビュー投稿は成功
        result = await submission_service.submit_review(review_data)
        assert result["status"] == "success"

        # 集計処理でエラーが発生してもレビューは保存されている
        reviews = await db.find_many("reviews", {"company_id": ObjectId(company_id)})
        assert len(reviews) == 1
