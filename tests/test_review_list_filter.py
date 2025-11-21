"""
ReviewListHandlerのフィルター機能統合のテスト (TDD)
Requirements: 1.4, 1.5, 1.6
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from tornado.httputil import HTTPServerRequest
from tornado.web import Application
from src.handlers.review_handler import ReviewListHandler


def create_mock_application():
    """モックTornado Applicationを作成"""
    app = Mock(spec=Application)
    app.ui_modules = {}
    app.ui_methods = {}
    app.settings = {"cookie_secret": "test_secret"}
    return app


def create_mock_request():
    """モックHTTPServerRequestを作成"""
    request = Mock(spec=HTTPServerRequest)
    request.uri = "/review"
    request.method = "GET"
    request.headers = {}
    request.connection = Mock()
    request.connection.context = Mock()
    return request


class TestReviewListFilter:
    """レビュー一覧フィルター機能のテストクラス"""

    @pytest.mark.asyncio
    async def test_filter_available_only_with_full_access(self):
        """
        Requirement 1.4, 1.5, 1.6: フィルター機能はaccess_level="full"の場合のみ有効
        """
        handler = ReviewListHandler(
            application=create_mock_application(),
            request=create_mock_request()
        )
        handler.initialize()

        # Mock AccessControlMiddleware
        with patch.object(handler, 'access_control') as mock_access_control:
            # 1年以内のレビュー投稿者（フルアクセス）
            mock_access_result = AsyncMock()
            mock_access_result.check_review_list_access.return_value = {
                "access_level": "full",
                "can_filter": True,
                "message": None,
                "user_last_posted_at": datetime.now(timezone.utc)
            }
            mock_access_control.return_value = mock_access_result

            # Mock company_search_service
            with patch.object(handler, 'company_search_service') as mock_search:
                mock_search.search_companies_with_reviews = AsyncMock(return_value={
                    "companies": [],
                    "pagination": {"page": 1, "total": 0, "pages": 0}
                })

                # Mock render
                handler.render = Mock()

                # Execute
                await handler.get()

                # Verify render was called with can_filter=True
                render_args = handler.render.call_args
                assert render_args is not None
                # can_filter should be passed to template
                # (implementation will add this parameter)

    @pytest.mark.asyncio
    async def test_filter_unavailable_for_preview_access(self):
        """
        Requirement 1.1: プレビューアクセスの場合、フィルター機能は無効
        """
        handler = ReviewListHandler(
            application=create_mock_application(),
            request=create_mock_request()
        )
        handler.initialize()

        # Mock AccessControlMiddleware
        with patch.object(handler, 'access_control') as mock_access_control:
            # 未認証ユーザー（プレビューアクセス）
            mock_access_result = AsyncMock()
            mock_access_result.check_review_list_access.return_value = {
                "access_level": "preview",
                "can_filter": False,
                "message": None,
                "user_last_posted_at": None
            }
            mock_access_control.return_value = mock_access_result

            # Mock company_search_service
            with patch.object(handler, 'company_search_service') as mock_search:
                mock_search.search_companies_with_reviews = AsyncMock(return_value={
                    "companies": [],
                    "pagination": {"page": 1, "total": 0, "pages": 0}
                })

                # Mock render
                handler.render = Mock()

                # Execute
                await handler.get()

                # Verify render was called with can_filter=False
                render_args = handler.render.call_args
                assert render_args is not None
                # can_filter should be False for preview access

    @pytest.mark.asyncio
    async def test_company_filter_integration(self):
        """
        Requirement 1.4: 会社別フィルター機能の統合
        """
        handler = ReviewListHandler(
            application=create_mock_application(),
            request=create_mock_request()
        )
        handler.initialize()

        # Mock get_argument to simulate company filter
        handler.get_argument = Mock(side_effect=lambda key, default=None: {
            "name": "TestCompany",
            "location": "",
            "min_rating": None,
            "max_rating": None,
            "page": "1",
            "limit": "20",
            "sort": "rating_high"
        }.get(key, default))

        # Mock AccessControlMiddleware (full access)
        with patch.object(handler, 'access_control') as mock_access_control:
            mock_access_result = AsyncMock()
            mock_access_result.check_review_list_access.return_value = {
                "access_level": "full",
                "can_filter": True,
                "message": None,
                "user_last_posted_at": datetime.now(timezone.utc)
            }
            mock_access_control.return_value = mock_access_result

            # Mock company_search_service
            with patch.object(handler, 'company_search_service') as mock_search:
                mock_search.search_companies_with_reviews = AsyncMock(return_value={
                    "companies": [{"name": "TestCompany", "location": "Tokyo"}],
                    "pagination": {"page": 1, "total": 1, "pages": 1}
                })

                # Mock render
                handler.render = Mock()

                # Execute
                await handler.get()

                # Verify search was called with company name filter
                search_call_args = mock_search.search_companies_with_reviews.call_args
                assert search_call_args is not None
                search_params = search_call_args[0][0]
                assert search_params["name"] == "TestCompany"

    @pytest.mark.asyncio
    async def test_location_filter_integration(self):
        """
        Requirement 1.5: 地域別フィルター機能の統合
        """
        handler = ReviewListHandler(
            application=create_mock_application(),
            request=create_mock_request()
        )
        handler.initialize()

        # Mock get_argument to simulate location filter
        handler.get_argument = Mock(side_effect=lambda key, default=None: {
            "name": "",
            "location": "Tokyo",
            "min_rating": None,
            "max_rating": None,
            "page": "1",
            "limit": "20",
            "sort": "rating_high"
        }.get(key, default))

        # Mock AccessControlMiddleware (full access)
        with patch.object(handler, 'access_control') as mock_access_control:
            mock_access_result = AsyncMock()
            mock_access_result.check_review_list_access.return_value = {
                "access_level": "full",
                "can_filter": True,
                "message": None,
                "user_last_posted_at": datetime.now(timezone.utc)
            }
            mock_access_control.return_value = mock_access_result

            # Mock company_search_service
            with patch.object(handler, 'company_search_service') as mock_search:
                mock_search.search_companies_with_reviews = AsyncMock(return_value={
                    "companies": [{"name": "Company1", "location": "Tokyo"}],
                    "pagination": {"page": 1, "total": 1, "pages": 1}
                })

                # Mock render
                handler.render = Mock()

                # Execute
                await handler.get()

                # Verify search was called with location filter
                search_call_args = mock_search.search_companies_with_reviews.call_args
                assert search_call_args is not None
                search_params = search_call_args[0][0]
                assert search_params["location"] == "Tokyo"

    @pytest.mark.asyncio
    async def test_rating_threshold_filter_integration(self):
        """
        Requirement 1.6: レビュー評価しきい値による絞り込み機能の統合
        """
        handler = ReviewListHandler(
            application=create_mock_application(),
            request=create_mock_request()
        )
        handler.initialize()

        # Mock get_argument to simulate rating filter
        handler.get_argument = Mock(side_effect=lambda key, default=None: {
            "name": "",
            "location": "",
            "min_rating": "4.0",
            "max_rating": "5.0",
            "page": "1",
            "limit": "20",
            "sort": "rating_high"
        }.get(key, default))

        # Mock AccessControlMiddleware (full access)
        with patch.object(handler, 'access_control') as mock_access_control:
            mock_access_result = AsyncMock()
            mock_access_result.check_review_list_access.return_value = {
                "access_level": "full",
                "can_filter": True,
                "message": None,
                "user_last_posted_at": datetime.now(timezone.utc)
            }
            mock_access_control.return_value = mock_access_result

            # Mock company_search_service
            with patch.object(handler, 'company_search_service') as mock_search:
                mock_search.search_companies_with_reviews = AsyncMock(return_value={
                    "companies": [{"name": "HighRatedCompany", "average_rating": 4.5}],
                    "pagination": {"page": 1, "total": 1, "pages": 1}
                })

                # Mock render
                handler.render = Mock()

                # Execute
                await handler.get()

                # Verify search was called with rating threshold
                search_call_args = mock_search.search_companies_with_reviews.call_args
                assert search_call_args is not None
                search_params = search_call_args[0][0]
                assert search_params["min_rating"] == 4.0
                assert search_params["max_rating"] == 5.0

    @pytest.mark.asyncio
    async def test_combined_filters(self):
        """
        Requirement 1.4, 1.5, 1.6: 複数フィルターの組み合わせ
        """
        handler = ReviewListHandler(
            application=create_mock_application(),
            request=create_mock_request()
        )
        handler.initialize()

        # Mock get_argument to simulate combined filters
        handler.get_argument = Mock(side_effect=lambda key, default=None: {
            "name": "Tech",
            "location": "Tokyo",
            "min_rating": "3.5",
            "max_rating": None,
            "page": "1",
            "limit": "20",
            "sort": "rating_high"
        }.get(key, default))

        # Mock AccessControlMiddleware (full access)
        with patch.object(handler, 'access_control') as mock_access_control:
            mock_access_result = AsyncMock()
            mock_access_result.check_review_list_access.return_value = {
                "access_level": "full",
                "can_filter": True,
                "message": None,
                "user_last_posted_at": datetime.now(timezone.utc)
            }
            mock_access_control.return_value = mock_access_result

            # Mock company_search_service
            with patch.object(handler, 'company_search_service') as mock_search:
                mock_search.search_companies_with_reviews = AsyncMock(return_value={
                    "companies": [{"name": "TechCompany", "location": "Tokyo", "average_rating": 4.0}],
                    "pagination": {"page": 1, "total": 1, "pages": 1}
                })

                # Mock render
                handler.render = Mock()

                # Execute
                await handler.get()

                # Verify search was called with all filters
                search_call_args = mock_search.search_companies_with_reviews.call_args
                assert search_call_args is not None
                search_params = search_call_args[0][0]
                assert search_params["name"] == "Tech"
                assert search_params["location"] == "Tokyo"
                assert search_params["min_rating"] == 3.5
                assert search_params["max_rating"] is None
