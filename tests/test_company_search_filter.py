"""
CompanySearchService の検索フィルタ構築機能のテスト
"""
import pytest
import pytest_asyncio
from src.services.company_search_service import CompanySearchService
from src.database import DatabaseService
from datetime import datetime, timezone
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


class TestCompanySearchFilter:
    """CompanySearchService の検索フィルタ機能のテスト"""

    @pytest.mark.asyncio
    async def test_filter_by_company_name(self, service_and_db):
        """企業名による部分一致検索フィルタ"""
        service, db = service_and_db

        # テスト用企業を作成
        await db.create("companies", {
            "name": "テスト株式会社",
            "location": "東京都",
            "review_summary": {
                "total_reviews": 5,
                "overall_average": 4.0
            }
        })
        await db.create("companies", {
            "name": "サンプル企業",
            "location": "大阪府",
            "review_summary": {
                "total_reviews": 3,
                "overall_average": 3.5
            }
        })

        # 検索フィルタを構築
        search_filter = await service.build_search_filter({"name": "テスト"})

        # フィルタ内容を検証
        assert "name" in search_filter
        assert search_filter["name"]["$regex"] == "テスト"
        assert search_filter["name"]["$options"] == "i"
        assert "review_summary" in search_filter
        assert search_filter["review_summary"] == {"$exists": True}

    @pytest.mark.asyncio
    async def test_filter_by_location(self, service_and_db):
        """所在地による部分一致検索フィルタ"""
        service, db = service_and_db

        # 検索フィルタを構築
        search_filter = await service.build_search_filter({"location": "東京"})

        # フィルタ内容を検証
        assert "location" in search_filter
        assert search_filter["location"]["$regex"] == "東京"
        assert search_filter["location"]["$options"] == "i"

    @pytest.mark.asyncio
    async def test_filter_by_min_rating(self, service_and_db):
        """最低評価による範囲フィルタ"""
        service, db = service_and_db

        # 検索フィルタを構築
        search_filter = await service.build_search_filter({"min_rating": 3.5})

        # フィルタ内容を検証
        assert "review_summary.overall_average" in search_filter
        assert search_filter["review_summary.overall_average"]["$gte"] == 3.5

    @pytest.mark.asyncio
    async def test_filter_by_max_rating(self, service_and_db):
        """最高評価による範囲フィルタ"""
        service, db = service_and_db

        # 検索フィルタを構築
        search_filter = await service.build_search_filter({"max_rating": 4.0})

        # フィルタ内容を検証
        assert "review_summary.overall_average" in search_filter
        assert search_filter["review_summary.overall_average"]["$lte"] == 4.0

    @pytest.mark.asyncio
    async def test_filter_by_rating_range(self, service_and_db):
        """最低評価と最高評価の範囲フィルタ"""
        service, db = service_and_db

        # 検索フィルタを構築
        search_filter = await service.build_search_filter({
            "min_rating": 2.5,
            "max_rating": 4.5
        })

        # フィルタ内容を検証
        assert "review_summary.overall_average" in search_filter
        assert search_filter["review_summary.overall_average"]["$gte"] == 2.5
        assert search_filter["review_summary.overall_average"]["$lte"] == 4.5

    @pytest.mark.asyncio
    async def test_filter_multiple_conditions(self, service_and_db):
        """複数フィルタ条件のAND結合"""
        service, db = service_and_db

        # 検索フィルタを構築
        search_filter = await service.build_search_filter({
            "name": "テスト",
            "location": "東京",
            "min_rating": 3.0,
            "max_rating": 5.0
        })

        # フィルタ内容を検証（すべての条件が含まれている）
        assert "name" in search_filter
        assert "location" in search_filter
        assert "review_summary.overall_average" in search_filter
        assert "review_summary" in search_filter

    @pytest.mark.asyncio
    async def test_filter_only_companies_with_review_summary(self, service_and_db):
        """review_summary が存在する企業のみを対象とするフィルタ"""
        service, db = service_and_db

        # 検索フィルタを構築（パラメータなし）
        search_filter = await service.build_search_filter({})

        # review_summary の存在チェックが含まれていることを確認
        assert "review_summary" in search_filter
        assert search_filter["review_summary"] == {"$exists": True}

    @pytest.mark.asyncio
    async def test_filter_regex_escape(self, service_and_db):
        """正規表現エスケープ処理を含む検索"""
        service, db = service_and_db

        # 特殊文字を含む検索文字列
        search_filter = await service.build_search_filter({"name": "Test.Inc (株)"})

        # エスケープされていることを確認（特殊文字がリテラルとして扱われる）
        assert "name" in search_filter
        # re.escape() の結果、特殊文字がエスケープされている
        assert "Test\\.Inc\\ \\(株\\)" in search_filter["name"]["$regex"]

    @pytest.mark.asyncio
    async def test_search_with_name_filter(self, service_and_db):
        """企業名フィルタを使った実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        await db.create("companies", {
            "name": "ABC株式会社",
            "location": "東京都",
            "review_summary": {
                "total_reviews": 5,
                "overall_average": 4.0,
                "last_updated": datetime.now(timezone.utc)
            }
        })
        await db.create("companies", {
            "name": "XYZ企業",
            "location": "大阪府",
            "review_summary": {
                "total_reviews": 3,
                "overall_average": 3.5,
                "last_updated": datetime.now(timezone.utc)
            }
        })
        # review_summaryなしの企業（検索対象外）
        await db.create("companies", {
            "name": "DEF会社",
            "location": "東京都"
        })

        # 検索実行
        result = await service.search_companies({"name": "ABC", "page": 1, "per_page": 20})

        assert result["success"] is True
        assert result["total_count"] == 1
        assert len(result["companies"]) == 1
        assert result["companies"][0]["name"] == "ABC株式会社"

    @pytest.mark.asyncio
    async def test_search_with_rating_filter(self, service_and_db):
        """評価範囲フィルタを使った実際の検索"""
        service, db = service_and_db

        # テスト用企業を作成
        await db.create("companies", {
            "name": "高評価会社",
            "location": "東京都",
            "review_summary": {
                "total_reviews": 10,
                "overall_average": 4.5,
                "last_updated": datetime.now(timezone.utc)
            }
        })
        await db.create("companies", {
            "name": "中評価会社",
            "location": "大阪府",
            "review_summary": {
                "total_reviews": 5,
                "overall_average": 3.0,
                "last_updated": datetime.now(timezone.utc)
            }
        })
        await db.create("companies", {
            "name": "低評価会社",
            "location": "名古屋市",
            "review_summary": {
                "total_reviews": 3,
                "overall_average": 2.0,
                "last_updated": datetime.now(timezone.utc)
            }
        })

        # 検索実行（3.5以上の評価）
        result = await service.search_companies({
            "min_rating": 3.5,
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert result["total_count"] == 1
        assert result["companies"][0]["name"] == "高評価会社"

    @pytest.mark.asyncio
    async def test_search_with_multiple_filters(self, service_and_db):
        """複数フィルタ条件での検索（AND条件）"""
        service, db = service_and_db

        # テスト用企業を作成
        await db.create("companies", {
            "name": "東京ハイテク株式会社",
            "location": "東京都渋谷区",
            "review_summary": {
                "total_reviews": 10,
                "overall_average": 4.2,
                "last_updated": datetime.now(timezone.utc)
            }
        })
        await db.create("companies", {
            "name": "大阪ハイテク企業",
            "location": "大阪府大阪市",
            "review_summary": {
                "total_reviews": 5,
                "overall_average": 4.0,
                "last_updated": datetime.now(timezone.utc)
            }
        })
        await db.create("companies", {
            "name": "東京ローテク会社",
            "location": "東京都新宿区",
            "review_summary": {
                "total_reviews": 3,
                "overall_average": 2.5,
                "last_updated": datetime.now(timezone.utc)
            }
        })

        # 検索実行（東京 AND ハイテク AND 評価3.5以上）
        result = await service.search_companies({
            "name": "ハイテク",
            "location": "東京",
            "min_rating": 3.5,
            "page": 1,
            "per_page": 20
        })

        assert result["success"] is True
        assert result["total_count"] == 1
        assert result["companies"][0]["name"] == "東京ハイテク株式会社"
