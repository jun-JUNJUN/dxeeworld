"""
Test Access Control Middleware - Review List Access
Task 2.2: AccessControlMiddleware にレビュー一覧アクセス制御を追加
Requirements: 1.1, 1.2, 1.3, 1.7

TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from src.middleware.access_control_middleware import AccessControlMiddleware
from src.services.user_service import UserService
from src.utils.result import Result


class TestReviewListAccessControl:
    """Test review list access control functionality"""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance with mocked dependencies"""
        middleware = AccessControlMiddleware()

        # Mock user service
        mock_user_service = MagicMock()
        mock_user_service.check_review_access_within_one_year = AsyncMock()
        middleware.user_service = mock_user_service

        return middleware

    @pytest.mark.asyncio
    async def test_check_review_list_access_unauthenticated_returns_preview(self, middleware):
        """未認証ユーザーは preview アクセスレベルを返す (Requirement 1.1)"""
        # Act
        result = await middleware.check_review_list_access(user_id=None, user_agent=None)

        # Assert
        assert result["access_level"] == "preview"
        assert result["can_filter"] is False
        assert result["message"] is None
        assert result["user_last_posted_at"] is None

    @pytest.mark.asyncio
    async def test_check_review_list_access_crawler_detected(self, middleware):
        """Webクローラーは crawler アクセスレベルを返す (Requirement 1.2)"""
        # Arrange
        crawler_user_agents = [
            "Googlebot/2.1",
            "Mozilla/5.0 (compatible; bingbot/2.0)",
            "Mozilla/5.0 (compatible; Yahoo! Slurp)",
            "DuckDuckBot/1.0",
        ]

        for user_agent in crawler_user_agents:
            # Act
            result = await middleware.check_review_list_access(
                user_id=None,
                user_agent=user_agent
            )

            # Assert
            assert result["access_level"] == "crawler", f"Failed for user agent: {user_agent}"
            assert result["can_filter"] is False
            assert result["message"] is None

    @pytest.mark.asyncio
    async def test_check_review_list_access_authenticated_with_recent_review(self, middleware):
        """1年以内のレビュー投稿者は full アクセスレベルを返す (Requirement 1.3)"""
        # Arrange
        user_id = "user123"
        middleware.user_service.check_review_access_within_one_year.return_value = True

        # Act
        result = await middleware.check_review_list_access(
            user_id=user_id,
            user_agent="Mozilla/5.0"
        )

        # Assert
        assert result["access_level"] == "full"
        assert result["can_filter"] is True
        assert result["message"] is None
        middleware.user_service.check_review_access_within_one_year.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_check_review_list_access_authenticated_no_recent_review(self, middleware):
        """1年以上前または投稿履歴なしのユーザーは denied アクセスレベルを返す (Requirement 1.7)"""
        # Arrange
        user_id = "user123"
        middleware.user_service.check_review_access_within_one_year.return_value = False

        # Act
        result = await middleware.check_review_list_access(
            user_id=user_id,
            user_agent="Mozilla/5.0"
        )

        # Assert
        assert result["access_level"] == "denied"
        assert result["can_filter"] is False
        assert "Reviewを投稿いただいた方に閲覧権限を付与しています" in result["message"]

    @pytest.mark.asyncio
    async def test_check_review_list_access_priority_crawler_over_authenticated(self, middleware):
        """認証済みでもWebクローラーの場合はクローラー扱い (優先順位テスト)"""
        # Arrange
        user_id = "user123"
        crawler_user_agent = "Googlebot/2.1"
        middleware.user_service.check_review_access_within_one_year.return_value = True

        # Act
        result = await middleware.check_review_list_access(
            user_id=user_id,
            user_agent=crawler_user_agent
        )

        # Assert
        assert result["access_level"] == "crawler"
        # UserService は呼ばれない（クローラー判定が優先）
        middleware.user_service.check_review_access_within_one_year.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_web_crawler_various_user_agents(self, middleware):
        """様々なWebクローラーのUser-Agentを検出する"""
        # Arrange
        crawler_patterns = [
            "Googlebot",
            "bingbot",
            "Slurp",  # Yahoo
            "DuckDuckBot",
            "Baiduspider",
            "YandexBot",
            "facebookexternalhit",
            "Twitterbot",
            "rogerbot",
            "linkedinbot",
            "embedly",
        ]

        for pattern in crawler_patterns:
            user_agent = f"Mozilla/5.0 (compatible; {pattern}/1.0)"

            # Act
            result = await middleware.check_review_list_access(
                user_id=None,
                user_agent=user_agent
            )

            # Assert
            assert result["access_level"] == "crawler", f"Failed to detect: {pattern}"

    @pytest.mark.asyncio
    async def test_check_review_list_access_handles_service_error_gracefully(self, middleware):
        """UserServiceのエラーを適切にハンドリングする"""
        # Arrange
        user_id = "user123"
        middleware.user_service.check_review_access_within_one_year.side_effect = Exception("DB error")

        # Act
        result = await middleware.check_review_list_access(
            user_id=user_id,
            user_agent="Mozilla/5.0"
        )

        # Assert
        # エラー時は denied として扱う（セキュアフェイル）
        assert result["access_level"] == "denied"
        assert result["can_filter"] is False

    @pytest.mark.asyncio
    async def test_check_review_list_access_empty_user_agent(self, middleware):
        """User-Agentが空の場合は preview として扱う"""
        # Act
        result = await middleware.check_review_list_access(
            user_id=None,
            user_agent=""
        )

        # Assert
        assert result["access_level"] == "preview"

    @pytest.mark.asyncio
    async def test_check_review_list_access_normal_browser_user_agent(self, middleware):
        """通常のブラウザのUser-Agentはクローラー扱いしない"""
        # Arrange
        normal_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
        ]

        for user_agent in normal_user_agents:
            # Act
            result = await middleware.check_review_list_access(
                user_id=None,
                user_agent=user_agent
            )

            # Assert
            assert result["access_level"] == "preview", f"Incorrectly detected as crawler: {user_agent}"
