"""
CompanySearchService のページネーション機能のテスト
"""
import pytest
import pytest_asyncio
from src.services.company_search_service import CompanySearchService
from src.database import DatabaseService
from datetime import datetime, timezone


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


class TestCompanySearchPagination:
    """CompanySearchService のページネーション機能のテスト"""

    @pytest.mark.asyncio
    async def test_pagination_default_20_per_page(self, service_and_db):
        """1ページあたり20件の企業を取得（デフォルト）"""
        service, db = service_and_db

        # 30件のテスト用企業を作成
        base_time = datetime.now(timezone.utc)
        for i in range(30):
            await db.create("companies", {
                "name": f"会社{i:02d}",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            })

        # 検索実行（ページパラメータなし = デフォルト）
        result = await service.search_companies({"page": 1})

        assert result["success"] is True
        assert len(result["companies"]) == 20  # デフォルトで20件
        assert result["per_page"] == 20
        assert result["current_page"] == 1
        assert result["total_count"] == 30
        assert result["total_pages"] == 2

    @pytest.mark.asyncio
    async def test_pagination_page_offset_calculation(self, service_and_db):
        """ページ番号によるオフセット計算（skip/limit）"""
        service, db = service_and_db

        # 50件のテスト用企業を作成
        base_time = datetime.now(timezone.utc)
        for i in range(50):
            await db.create("companies", {
                "name": f"会社{i:03d}",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            })

        # 1ページ目
        result_page1 = await service.search_companies({"page": 1, "per_page": 10, "sort_by": "name"})
        # 2ページ目
        result_page2 = await service.search_companies({"page": 2, "per_page": 10, "sort_by": "name"})
        # 3ページ目
        result_page3 = await service.search_companies({"page": 3, "per_page": 10, "sort_by": "name"})

        # 各ページで異なる企業が返されることを確認
        assert len(result_page1["companies"]) == 10
        assert len(result_page2["companies"]) == 10
        assert len(result_page3["companies"]) == 10

        # ページごとに異なるデータが返されることを確認
        page1_names = [c["name"] for c in result_page1["companies"]]
        page2_names = [c["name"] for c in result_page2["companies"]]
        page3_names = [c["name"] for c in result_page3["companies"]]

        # 重複がないことを確認
        assert len(set(page1_names) & set(page2_names)) == 0
        assert len(set(page2_names) & set(page3_names)) == 0
        assert len(set(page1_names) & set(page3_names)) == 0

    @pytest.mark.asyncio
    async def test_pagination_total_count_and_pages(self, service_and_db):
        """総件数の取得とページ数計算"""
        service, db = service_and_db

        # 45件のテスト用企業を作成
        base_time = datetime.now(timezone.utc)
        for i in range(45):
            await db.create("companies", {
                "name": f"会社{i}",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            })

        # 検索実行（10件ずつ）
        result = await service.search_companies({"page": 1, "per_page": 10})

        assert result["success"] is True
        assert result["total_count"] == 45
        assert result["total_pages"] == 5  # ceil(45 / 10) = 5
        assert result["per_page"] == 10

    @pytest.mark.asyncio
    async def test_pagination_page_validation_positive(self, service_and_db):
        """ページ番号のバリデーション（1以上）"""
        service, db = service_and_db

        # ページ番号が0以下の場合
        errors = await service.validate_search_params({"page": 0})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # ページ番号が負の場合
        errors = await service.validate_search_params({"page": -1})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # ページ番号が正の整数の場合
        errors = await service.validate_search_params({"page": 1})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_pagination_last_page_partial(self, service_and_db):
        """最終ページが部分的に埋まる場合"""
        service, db = service_and_db

        # 25件のテスト用企業を作成
        base_time = datetime.now(timezone.utc)
        for i in range(25):
            await db.create("companies", {
                "name": f"会社{i}",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            })

        # 最終ページ（3ページ目）を取得
        result = await service.search_companies({"page": 3, "per_page": 10})

        assert result["success"] is True
        assert len(result["companies"]) == 5  # 25 - 20 = 5件
        assert result["total_count"] == 25
        assert result["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_pagination_empty_results(self, service_and_db):
        """検索結果が0件の場合のページネーション"""
        service, db = service_and_db

        # データなしで検索
        result = await service.search_companies({"page": 1, "per_page": 20})

        assert result["success"] is True
        assert len(result["companies"]) == 0
        assert result["total_count"] == 0
        assert result["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_pagination_per_page_limit_100(self, service_and_db):
        """1ページあたりの件数が100を超える場合、100に制限される"""
        service, db = service_and_db

        # 150件のテスト用企業を作成
        base_time = datetime.now(timezone.utc)
        for i in range(150):
            await db.create("companies", {
                "name": f"会社{i}",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            })

        # per_page=200を指定（上限を超える）
        result = await service.search_companies({"page": 1, "per_page": 200})

        assert result["success"] is True
        assert result["per_page"] == 100  # 100に制限される
        assert len(result["companies"]) == 100

    @pytest.mark.asyncio
    async def test_pagination_with_filters(self, service_and_db):
        """フィルタと組み合わせたページネーション"""
        service, db = service_and_db

        # テスト用企業を作成（一部だけフィルタに一致）
        base_time = datetime.now(timezone.utc)
        for i in range(30):
            await db.create("companies", {
                "name": f"東京会社{i}" if i < 15 else f"大阪会社{i}",
                "location": "東京都" if i < 15 else "大阪府",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time
                }
            })

        # フィルタ付き検索（"東京"で絞り込み）
        result = await service.search_companies({
            "location": "東京",
            "page": 1,
            "per_page": 10
        })

        assert result["success"] is True
        assert result["total_count"] == 15  # フィルタ後の件数
        assert result["total_pages"] == 2  # ceil(15 / 10) = 2
        assert len(result["companies"]) == 10
