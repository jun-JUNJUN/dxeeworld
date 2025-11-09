"""
CompanySearchService のソート順序構築機能のテスト
"""
import pytest
import pytest_asyncio
from src.services.company_search_service import CompanySearchService
from src.database import DatabaseService
from datetime import datetime, timezone, timedelta
from bson import ObjectId


@pytest_asyncio.fixture
async def service_and_db():
    """テスト用サービスインスタンスとデータベース"""
    db = DatabaseService()
    await db.connect()

    # テストデータをクリーンアップ
    await db.delete_many("companies", {})

    service = CompanySearchService(db)

    yield service, db

    # テスト後のクリーンアップ
    await db.delete_many("companies", {})
    await db.close()


class TestCompanySearchSort:
    """CompanySearchService のソート順序機能のテスト"""

    @pytest.mark.asyncio
    async def test_default_sort_by_last_review_date(self, service_and_db):
        """デフォルトソート：最新レビュー投稿順（last_review_date降順）"""
        service, db = service_and_db

        # ソート順序を構築（パラメータなし = デフォルト）
        sort_order = await service.build_sort_order({})

        # デフォルトは last_review_date 降順
        assert len(sort_order) == 1
        assert sort_order[0][0] == "review_summary.last_review_date"
        assert sort_order[0][1] == -1  # 降順

    @pytest.mark.asyncio
    async def test_sort_by_overall_average_desc(self, service_and_db):
        """評価順（高→低）：overall_average降順"""
        service, db = service_and_db

        # ソート順序を構築
        sort_order = await service.build_sort_order({"sort_by": "rating_high"})

        assert len(sort_order) == 1
        assert sort_order[0][0] == "review_summary.overall_average"
        assert sort_order[0][1] == -1  # 降順

    @pytest.mark.asyncio
    async def test_sort_by_overall_average_asc(self, service_and_db):
        """評価順（低→高）：overall_average昇順"""
        service, db = service_and_db

        # ソート順序を構築
        sort_order = await service.build_sort_order({"sort_by": "rating_low"})

        assert len(sort_order) == 1
        assert sort_order[0][0] == "review_summary.overall_average"
        assert sort_order[0][1] == 1  # 昇順

    @pytest.mark.asyncio
    async def test_sort_by_total_reviews_desc(self, service_and_db):
        """レビュー数順：total_reviews降順"""
        service, db = service_and_db

        # ソート順序を構築
        sort_order = await service.build_sort_order({"sort_by": "review_count"})

        assert len(sort_order) == 1
        assert sort_order[0][0] == "review_summary.total_reviews"
        assert sort_order[0][1] == -1  # 降順

    @pytest.mark.asyncio
    async def test_sort_by_name_asc(self, service_and_db):
        """企業名順：name昇順"""
        service, db = service_and_db

        # ソート順序を構築
        sort_order = await service.build_sort_order({"sort_by": "name"})

        assert len(sort_order) == 1
        assert sort_order[0][0] == "name"
        assert sort_order[0][1] == 1  # 昇順

    @pytest.mark.asyncio
    async def test_sort_by_last_review_date_desc(self, service_and_db):
        """最新レビュー順：last_review_date降順"""
        service, db = service_and_db

        # ソート順序を構築
        sort_order = await service.build_sort_order({"sort_by": "latest"})

        assert len(sort_order) == 1
        assert sort_order[0][0] == "review_summary.last_review_date"
        assert sort_order[0][1] == -1  # 降順

    @pytest.mark.asyncio
    async def test_sort_validation_invalid_sort_by(self, service_and_db):
        """無効なソートパラメータのバリデーション"""
        service, db = service_and_db

        # 無効なソートパラメータ
        sort_order = await service.build_sort_order({"sort_by": "invalid_field"})

        # デフォルトにフォールバック
        assert len(sort_order) == 1
        assert sort_order[0][0] == "review_summary.last_review_date"

    @pytest.mark.asyncio
    async def test_search_sorted_by_rating_high(self, service_and_db):
        """評価順（高→低）での実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        companies = [
            {
                "name": "低評価会社",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 2.5,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            },
            {
                "name": "高評価会社",
                "location": "大阪府",
                "review_summary": {
                    "total_reviews": 3,
                    "overall_average": 4.5,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            },
            {
                "name": "中評価会社",
                "location": "名古屋市",
                "review_summary": {
                    "total_reviews": 8,
                    "overall_average": 3.2,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            }
        ]

        for company in companies:
            await db.create("companies", company)

        # 検索実行（評価順：高→低）
        result = await service.search_companies({
            "sort_by": "rating_high",
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert len(result["companies"]) == 3
        # 評価の降順で並んでいることを確認
        assert result["companies"][0]["name"] == "高評価会社"
        assert result["companies"][1]["name"] == "中評価会社"
        assert result["companies"][2]["name"] == "低評価会社"

    @pytest.mark.asyncio
    async def test_search_sorted_by_review_count(self, service_and_db):
        """レビュー数順での実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        companies = [
            {
                "name": "少レビュー会社",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 2,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            },
            {
                "name": "多レビュー会社",
                "location": "大阪府",
                "review_summary": {
                    "total_reviews": 15,
                    "overall_average": 3.5,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            },
            {
                "name": "中レビュー会社",
                "location": "名古屋市",
                "review_summary": {
                    "total_reviews": 7,
                    "overall_average": 3.8,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            }
        ]

        for company in companies:
            await db.create("companies", company)

        # 検索実行（レビュー数順）
        result = await service.search_companies({
            "sort_by": "review_count",
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert len(result["companies"]) == 3
        # レビュー数の降順で並んでいることを確認
        assert result["companies"][0]["name"] == "多レビュー会社"
        assert result["companies"][1]["name"] == "中レビュー会社"
        assert result["companies"][2]["name"] == "少レビュー会社"

    @pytest.mark.asyncio
    async def test_search_sorted_by_name(self, service_and_db):
        """企業名順での実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        companies = [
            {
                "name": "Zebra株式会社",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            },
            {
                "name": "Apple企業",
                "location": "大阪府",
                "review_summary": {
                    "total_reviews": 3,
                    "overall_average": 3.5,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            },
            {
                "name": "Monkey会社",
                "location": "名古屋市",
                "review_summary": {
                    "total_reviews": 8,
                    "overall_average": 3.8,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            }
        ]

        for company in companies:
            await db.create("companies", company)

        # 検索実行（企業名順）
        result = await service.search_companies({
            "sort_by": "name",
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert len(result["companies"]) == 3
        # 企業名のアルファベット順で並んでいることを確認
        assert result["companies"][0]["name"] == "Apple企業"
        assert result["companies"][1]["name"] == "Monkey会社"
        assert result["companies"][2]["name"] == "Zebra株式会社"

    @pytest.mark.asyncio
    async def test_search_sorted_by_latest_review_date(self, service_and_db):
        """最新レビュー順での実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        companies = [
            {
                "name": "古い会社",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time - timedelta(days=10),
                    "last_updated": base_time
                }
            },
            {
                "name": "新しい会社",
                "location": "大阪府",
                "review_summary": {
                    "total_reviews": 3,
                    "overall_average": 3.5,
                    "last_review_date": base_time - timedelta(days=1),
                    "last_updated": base_time
                }
            },
            {
                "name": "中間会社",
                "location": "名古屋市",
                "review_summary": {
                    "total_reviews": 8,
                    "overall_average": 3.8,
                    "last_review_date": base_time - timedelta(days=5),
                    "last_updated": base_time
                }
            }
        ]

        for company in companies:
            await db.create("companies", company)

        # 検索実行（最新レビュー順）
        result = await service.search_companies({
            "sort_by": "latest",
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert len(result["companies"]) == 3
        # 最新レビュー日時の降順で並んでいることを確認
        assert result["companies"][0]["name"] == "新しい会社"
        assert result["companies"][1]["name"] == "中間会社"
        assert result["companies"][2]["name"] == "古い会社"

    @pytest.mark.asyncio
    async def test_search_default_sort(self, service_and_db):
        """デフォルトソート（最新レビュー順）での実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        companies = [
            {
                "name": "会社A",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time - timedelta(days=3),
                    "last_updated": base_time
                }
            },
            {
                "name": "会社B",
                "location": "大阪府",
                "review_summary": {
                    "total_reviews": 3,
                    "overall_average": 3.5,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            }
        ]

        for company in companies:
            await db.create("companies", company)

        # 検索実行（ソートパラメータなし = デフォルト）
        result = await service.search_companies({
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert len(result["companies"]) == 2
        # デフォルトで最新レビュー順になっていることを確認
        assert result["companies"][0]["name"] == "会社B"
        assert result["companies"][1]["name"] == "会社A"
