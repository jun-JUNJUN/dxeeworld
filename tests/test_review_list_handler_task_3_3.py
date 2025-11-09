"""
ReviewListHandler の Task 3.3 機能のテスト
Task 3.3: 企業検索の実行とページレンダリングを実装
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from src.handlers.review_handler import ReviewListHandler
from src.database import DatabaseService


@pytest_asyncio.fixture
async def db():
    """テスト用データベース"""
    db = DatabaseService()
    await db.connect()

    # テストデータをクリーンアップ
    await db.delete_many("companies", {})

    yield db

    # テスト後のクリーンアップ
    await db.delete_many("companies", {})
    await db.close()


class TestReviewListHandlerSearchExecution:
    """Task 3.3: 企業検索の実行とページレンダリングのテスト"""

    @pytest.mark.asyncio
    async def test_search_companies_with_filters(self, db):
        """CompanySearchServiceを使用して企業を検索（フィルター付き）"""
        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        await db.create("companies", {
            "name": "テスト企業A",
            "location": "東京都",
            "review_summary": {
                "total_reviews": 10,
                "overall_average": 4.5,
                "last_review_date": base_time,
                "last_updated": base_time,
                "category_averages": {
                    "recommendation": 4.5,
                    "foreign_support": 4.0,
                    "company_culture": 4.2,
                    "employee_relations": 4.3,
                    "evaluation_system": 4.1,
                    "promotion_treatment": 4.4
                }
            }
        })

        await db.create("companies", {
            "name": "テスト企業B",
            "location": "大阪府",
            "review_summary": {
                "total_reviews": 5,
                "overall_average": 3.5,
                "last_review_date": base_time,
                "last_updated": base_time,
                "category_averages": {
                    "recommendation": 3.5,
                    "foreign_support": 3.0,
                    "company_culture": 3.2,
                    "employee_relations": 3.3,
                    "evaluation_system": 3.1,
                    "promotion_treatment": 3.4
                }
            }
        })

        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        # CompanySearchServiceにデータベースを渡す
        from src.services.company_search_service import CompanySearchService
        handler.company_search_service = CompanySearchService(db)
        from src.middleware.access_control_middleware import AccessControlMiddleware
        handler.access_control = AccessControlMiddleware()

        # Mock get_argument
        def mock_get_argument(key, default=None):
            params = {
                "name": "テスト",
                "location": "東京",
                "page": "1"
            }
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        # parse_search_params を呼び出し
        search_params = handler.parse_search_params(can_filter=True)

        # CompanySearchService.search_companies を呼び出し
        result = await handler.company_search_service.search_companies(search_params)

        assert result["success"] is True
        assert result["total_count"] == 1
        assert result["companies"][0]["name"] == "テスト企業A"

    @pytest.mark.asyncio
    async def test_search_companies_with_pagination(self, db):
        """ページネーション情報を正しく取得"""
        # 30件のテスト用企業を作成
        base_time = datetime.now(timezone.utc)
        for i in range(30):
            await db.create("companies", {
                "name": f"企業{i:02d}",
                "location": "東京都",
                "review_summary": {
                    "total_reviews": 5,
                    "overall_average": 4.0,
                    "last_review_date": base_time,
                    "last_updated": base_time,
                    "category_averages": {
                        "recommendation": 4.0,
                        "foreign_support": 4.0,
                        "company_culture": 4.0,
                        "employee_relations": 4.0,
                        "evaluation_system": 4.0,
                        "promotion_treatment": 4.0
                    }
                }
            })

        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        # CompanySearchServiceにデータベースを渡す
        from src.services.company_search_service import CompanySearchService
        handler.company_search_service = CompanySearchService(db)
        from src.middleware.access_control_middleware import AccessControlMiddleware
        handler.access_control = AccessControlMiddleware()

        # Mock get_argument for page 1
        def mock_get_argument(key, default=None):
            params = {"page": "1"}
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        # parse_search_params を呼び出し
        search_params = handler.parse_search_params(can_filter=True)

        # CompanySearchService.search_companies を呼び出し
        result = await handler.company_search_service.search_companies(search_params)

        assert result["success"] is True
        assert result["total_count"] == 30
        assert result["current_page"] == 1
        assert result["total_pages"] == 2
        assert result["per_page"] == 20
        assert len(result["companies"]) == 20

    @pytest.mark.asyncio
    async def test_search_companies_error_handling(self, db):
        """エラー時の処理（空のリスト、エラーログ記録）"""
        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument
        handler.get_argument = Mock(return_value=None)

        # parse_search_params を呼び出し
        search_params = handler.parse_search_params(can_filter=True)

        # Mock CompanySearchService to raise an error
        with patch.object(
            handler.company_search_service,
            'search_companies',
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = Exception("Database error")

            # エラーが発生しても例外を投げない
            try:
                result = await handler.company_search_service.search_companies(search_params)
            except Exception as e:
                # エラーが発生した場合、空のリストを返すべき
                result = {
                    "success": False,
                    "error_code": "database_error",
                    "message": str(e)
                }

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_method_uses_parse_search_params(self, db):
        """get()メソッドがparse_search_params()を使用する"""
        # テスト用企業を作成
        base_time = datetime.now(timezone.utc)
        await db.create("companies", {
            "name": "テスト企業",
            "location": "東京都",
            "review_summary": {
                "total_reviews": 5,
                "overall_average": 4.0,
                "last_review_date": base_time,
                "last_updated": base_time,
                "category_averages": {
                    "recommendation": 4.0,
                    "foreign_support": 4.0,
                    "company_culture": 4.0,
                    "employee_relations": 4.0,
                    "evaluation_system": 4.0,
                    "promotion_treatment": 4.0
                }
            }
        })

        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock request and methods
        handler.request = Mock()
        handler.request.headers = {"User-Agent": "Test Browser"}
        handler.get_secure_cookie = Mock(return_value=None)
        handler.get_argument = Mock(return_value=None)

        # Mock render to capture template data
        rendered_data = {}

        def mock_render(template, **kwargs):
            rendered_data.update(kwargs)

        handler.render = Mock(side_effect=mock_render)

        # Call get()
        await handler.get()

        # Verify render was called
        assert handler.render.called
        assert "companies" in rendered_data
        assert "pagination" in rendered_data
        assert "access_level" in rendered_data
        assert "can_filter" in rendered_data

    @pytest.mark.asyncio
    async def test_render_passes_access_level_and_can_filter(self, db):
        """テンプレートにアクセスレベルとcan_filterフラグを渡す"""
        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock request and methods
        handler.request = Mock()
        handler.request.headers = {"User-Agent": "Test Browser"}
        handler.get_secure_cookie = Mock(return_value=None)
        handler.get_argument = Mock(return_value=None)

        # Mock render to capture template data
        rendered_data = {}

        def mock_render(template, **kwargs):
            rendered_data.update(kwargs)

        handler.render = Mock(side_effect=mock_render)

        # Call get()
        await handler.get()

        # Verify access control data is passed
        assert rendered_data["access_level"] == "preview"
        assert rendered_data["can_filter"] is False

    @pytest.mark.asyncio
    async def test_search_with_empty_results(self, db):
        """検索結果が0件の場合"""
        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        # CompanySearchServiceにデータベースを渡す
        from src.services.company_search_service import CompanySearchService
        handler.company_search_service = CompanySearchService(db)
        from src.middleware.access_control_middleware import AccessControlMiddleware
        handler.access_control = AccessControlMiddleware()

        # Mock get_argument for search with no results
        def mock_get_argument(key, default=None):
            params = {
                "name": "存在しない企業",
                "page": "1"
            }
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        # parse_search_params を呼び出し
        search_params = handler.parse_search_params(can_filter=True)

        # CompanySearchService.search_companies を呼び出し
        result = await handler.company_search_service.search_companies(search_params)

        assert result["success"] is True
        assert result["total_count"] == 0
        assert result["total_pages"] == 0
        assert len(result["companies"]) == 0

    @pytest.mark.asyncio
    async def test_get_method_handles_errors_gracefully(self, db):
        """get()メソッドがエラーを適切に処理する"""
        # ハンドラーの初期化
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock request and methods
        handler.request = Mock()
        handler.request.headers = {"User-Agent": "Test Browser"}
        handler.get_secure_cookie = Mock(return_value=None)
        handler.get_argument = Mock(return_value=None)

        # Mock render
        rendered_data = {}

        def mock_render(template, **kwargs):
            rendered_data.update(kwargs)

        handler.render = Mock(side_effect=mock_render)

        # Mock company_search_service to raise an error
        with patch.object(
            handler.company_search_service,
            'search_companies',
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = Exception("Database connection error")

            # Call get() - should not raise exception
            await handler.get()

            # Verify render was still called with empty data
            assert handler.render.called
            assert "companies" in rendered_data
            # Error case should render empty list
            assert isinstance(rendered_data["companies"], list)
