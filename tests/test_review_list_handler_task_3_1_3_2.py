"""
ReviewListHandler の Task 3.1-3.2 機能のテスト
Task 3.1: アクセス制御チェック
Task 3.2: 検索パラメータの解析と処理
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
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


class TestReviewListHandlerParseSearchParams:
    """Task 3.2: parse_search_params() メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_parse_search_params_method_exists(self, db):
        """parse_search_params() メソッドが存在する"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        assert hasattr(handler, 'parse_search_params')
        assert callable(getattr(handler, 'parse_search_params'))

    @pytest.mark.asyncio
    async def test_parse_search_params_default_values(self, db):
        """デフォルト値の設定（page=1, per_page=20, sort_by=rating_high）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument to return None/default
        handler.get_argument = Mock(return_value=None)

        params = handler.parse_search_params(can_filter=True)

        assert params["page"] == 1
        assert params["per_page"] == 20
        assert params["sort_by"] == "rating_high"

    @pytest.mark.asyncio
    async def test_parse_search_params_with_all_filters(self, db):
        """すべてのフィルターパラメータを解析"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument
        def mock_get_argument(key, default=None):
            params = {
                "name": "テスト企業",
                "location": "東京都",
                "min_rating": "3.5",
                "max_rating": "4.5",
                "page": "2",
                "per_page": "10",
                "sort": "review_count"
            }
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=True)

        assert params["name"] == "テスト企業"
        assert params["location"] == "東京都"
        assert params["min_rating"] == 3.5
        assert params["max_rating"] == 4.5
        assert params["page"] == 2
        assert params["per_page"] == 10
        assert params["sort_by"] == "review_count"

    @pytest.mark.asyncio
    async def test_parse_search_params_filter_disabled(self, db):
        """can_filter=false の場合、フィルターパラメータを無効化"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument with filter params
        def mock_get_argument(key, default=None):
            params = {
                "name": "テスト",
                "location": "東京",
                "min_rating": "3.0",
                "max_rating": "5.0",
                "page": "1",
                "sort": "rating_high"
            }
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=False)

        # フィルターパラメータは含まれない
        assert "name" not in params
        assert "location" not in params
        assert "min_rating" not in params
        assert "max_rating" not in params

        # ページとソートは有効
        assert params["page"] == 1
        assert params["sort_by"] == "rating_high"

    @pytest.mark.asyncio
    async def test_parse_search_params_rating_type_conversion(self, db):
        """評価範囲の型変換（文字列→float）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument
        def mock_get_argument(key, default=None):
            params = {"min_rating": "2.5", "max_rating": "4.0"}
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=True)

        assert isinstance(params["min_rating"], float)
        assert isinstance(params["max_rating"], float)
        assert params["min_rating"] == 2.5
        assert params["max_rating"] == 4.0

    @pytest.mark.asyncio
    async def test_parse_search_params_invalid_rating_ignored(self, db):
        """不正な評価値形式の場合、無視される"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument with invalid rating
        def mock_get_argument(key, default=None):
            params = {"min_rating": "invalid", "max_rating": "xyz"}
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=True)

        # 不正な値は無視される
        assert "min_rating" not in params
        assert "max_rating" not in params

    @pytest.mark.asyncio
    async def test_parse_search_params_page_integer_conversion(self, db):
        """ページ番号の型変換（文字列→int）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument
        def mock_get_argument(key, default=None):
            params = {"page": "5"}
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=True)

        assert isinstance(params["page"], int)
        assert params["page"] == 5

    @pytest.mark.asyncio
    async def test_parse_search_params_invalid_page_defaults_to_1(self, db):
        """不正なページ番号の場合、デフォルト1に設定"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument with invalid page
        def mock_get_argument(key, default=None):
            params = {"page": "abc"}
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=True)

        assert params["page"] == 1

    @pytest.mark.asyncio
    async def test_parse_search_params_empty_strings_ignored(self, db):
        """空文字列のフィルターパラメータは無視される"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock get_argument with empty strings
        def mock_get_argument(key, default=None):
            params = {"name": "", "location": ""}
            return params.get(key, default)

        handler.get_argument = Mock(side_effect=mock_get_argument)

        params = handler.parse_search_params(can_filter=True)

        # 空文字列は無視される
        assert "name" not in params
        assert "location" not in params


class TestReviewListHandlerAccessControl:
    """Task 3.1: アクセス制御チェックのテスト"""

    @pytest.mark.asyncio
    async def test_check_review_list_access_integration_full_access(self, db):
        """AccessControlMiddleware.check_review_list_access() の統合（フルアクセス）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock user_service
        with patch.object(
            handler.access_control,
            'user_service',
            Mock()
        ):
            handler.access_control.user_service.check_review_access_within_one_year = AsyncMock(
                return_value=True
            )

            access_result = await handler.access_control.check_review_list_access(
                "user123",
                "Test Browser"
            )

            assert access_result["access_level"] == "full"
            assert access_result["can_filter"] is True

    @pytest.mark.asyncio
    async def test_check_review_list_access_integration_preview_mode(self, db):
        """AccessControlMiddleware.check_review_list_access() の統合（プレビューモード）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        access_result = await handler.access_control.check_review_list_access(
            None,  # unauthenticated
            "Test Browser"
        )

        assert access_result["access_level"] == "preview"
        assert access_result["can_filter"] is False

    @pytest.mark.asyncio
    async def test_check_review_list_access_integration_denied(self, db):
        """AccessControlMiddleware.check_review_list_access() の統合（アクセス拒否）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        # Mock user_service
        with patch.object(
            handler.access_control,
            'user_service',
            Mock()
        ):
            handler.access_control.user_service.check_review_access_within_one_year = AsyncMock(
                return_value=False
            )

            access_result = await handler.access_control.check_review_list_access(
                "user456",
                "Test Browser"
            )

            assert access_result["access_level"] == "denied"
            assert access_result["can_filter"] is False
            assert "閲覧権限" in access_result["message"]

    @pytest.mark.asyncio
    async def test_check_review_list_access_integration_crawler(self, db):
        """AccessControlMiddleware.check_review_list_access() の統合（クローラー検出）"""
        handler = ReviewListHandler.__new__(ReviewListHandler)
        handler.initialize()

        access_result = await handler.access_control.check_review_list_access(
            None,
            "Googlebot/2.1"
        )

        assert access_result["access_level"] == "crawler"
        assert access_result["can_filter"] is False
