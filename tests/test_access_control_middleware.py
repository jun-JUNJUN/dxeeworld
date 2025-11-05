"""
Test Access Control Middleware
Task 7.1-7.3: アクセス制御ミドルウェアの実装
TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.middleware.access_control_middleware import AccessControlMiddleware, AccessControlError
from src.utils.result import Result


class TestAccessControlMiddleware:
    """Test access control middleware for URL pattern matching and permission checking"""

    @pytest.fixture
    def access_control_middleware(self):
        """Access control middleware fixture with mocked dependencies"""
        middleware = AccessControlMiddleware()

        # Mock OAuth session service
        mock_session_service = MagicMock()
        mock_session_service.validate_oauth_session = AsyncMock()
        middleware.session_service = mock_session_service

        return middleware

    @pytest.mark.asyncio
    async def test_load_access_control_rules(self, access_control_middleware):
        """RED: Test loading access control rules from environment"""
        # This test should fail because load_access_control_rules is not implemented

        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/details,user,admin,ally;/reviews/submit,user,admin;/admin,admin'
        }):
            await access_control_middleware.load_access_control_rules()

        rules = access_control_middleware.access_rules
        assert len(rules) == 3

        # Check rule structure
        assert rules[0]['pattern'] == '/reviews/details'
        assert set(rules[0]['permissions']) == {'user', 'admin', 'ally'}

        assert rules[1]['pattern'] == '/reviews/submit'
        assert set(rules[1]['permissions']) == {'user', 'admin'}

        assert rules[2]['pattern'] == '/admin'
        assert rules[2]['permissions'] == ['admin']

    @pytest.mark.asyncio
    async def test_url_pattern_matching(self, access_control_middleware):
        """RED: Test URL pattern matching functionality"""
        # This test should fail because URL pattern matching is not implemented

        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/details,user,admin,ally;/reviews/submit,user,admin;/admin,admin'
        }):
            await access_control_middleware.load_access_control_rules()

        # Test exact matches
        match = access_control_middleware.match_url_pattern('/reviews/details')
        assert match is not None
        assert match['pattern'] == '/reviews/details'

        # Test partial matches (URL contains pattern)
        match = access_control_middleware.match_url_pattern('/reviews/details/123')
        assert match is not None
        assert match['pattern'] == '/reviews/details'

        # Test non-matches
        match = access_control_middleware.match_url_pattern('/public/home')
        assert match is None

    @pytest.mark.asyncio
    async def test_permission_validation_authenticated_user(self, access_control_middleware):
        """RED: Test permission validation for authenticated user"""
        # This test should fail because permission validation is not implemented

        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/details,user,admin,ally;/reviews/submit,user,admin;/admin,admin'
        }):
            await access_control_middleware.load_access_control_rules()

        # Mock valid session
        session_data = {
            'identity_id': 'user_123',
            'user_type': 'user',
            'auth_method': 'google',
            'is_active': True
        }
        access_control_middleware.session_service.validate_oauth_session.return_value = Result.success(session_data)

        # Test user with required permission
        result = await access_control_middleware.check_access('/reviews/details', 'session_123')
        assert result.is_success
        assert result.data['access_granted'] is True
        assert result.data['user_context']['user_type'] == 'user'

    @pytest.mark.asyncio
    async def test_permission_validation_insufficient_permissions(self, access_control_middleware):
        """RED: Test permission validation with insufficient permissions"""
        # This test should fail because permission validation is not implemented

        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/details,user,admin,ally;/reviews/submit,user,admin;/admin,admin'
        }):
            await access_control_middleware.load_access_control_rules()

        # Mock valid session with user type that doesn't have permission
        session_data = {
            'identity_id': 'guest_123',
            'user_type': 'guest',  # guest not in required permissions
            'auth_method': 'email',
            'is_active': True
        }
        access_control_middleware.session_service.validate_oauth_session.return_value = Result.success(session_data)

        # Test user without required permission
        result = await access_control_middleware.check_access('/admin', 'session_123')
        assert not result.is_success
        assert isinstance(result.error, AccessControlError)
        assert "insufficient permissions" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_unauthenticated_access_to_protected_url(self, access_control_middleware):
        """RED: Test unauthenticated access to protected URL"""
        # This test should fail because authentication validation is not implemented

        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/details,user,admin,ally;/reviews/submit,user,admin;/admin,admin'
        }):
            await access_control_middleware.load_access_control_rules()

        # Mock invalid session
        access_control_middleware.session_service.validate_oauth_session.return_value = Result.failure(
            Exception("Session not found")
        )

        result = await access_control_middleware.check_access('/reviews/details', 'invalid_session')
        assert not result.is_success
        assert isinstance(result.error, AccessControlError)
        assert "authentication required" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_access_to_unprotected_url(self, access_control_middleware):
        """RED: Test access to unprotected URL"""
        # This test should fail because unprotected URL handling is not implemented

        await access_control_middleware.load_access_control_rules()

        # No session needed for unprotected URLs
        result = await access_control_middleware.check_access('/public/home', None)
        assert result.is_success
        assert result.data['access_granted'] is True
        assert result.data['authentication_required'] is False

    @pytest.mark.asyncio
    async def test_multiple_pattern_matching_priority(self, access_control_middleware):
        """RED: Test multiple pattern matching with priority (first match wins)"""
        # This test should fail because priority handling is not implemented

        # Override with rules that could conflict
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews,user;/reviews/details,admin'
        }):
            middleware = AccessControlMiddleware()
            await middleware.load_access_control_rules()

            # Should match first rule (/reviews) not second (/reviews/details)
            match = middleware.match_url_pattern('/reviews/details/123')
            assert match is not None
            assert match['pattern'] == '/reviews'
            assert 'user' in match['permissions']

    @pytest.mark.asyncio
    async def test_configuration_reload(self, access_control_middleware):
        """RED: Test configuration reload functionality"""
        # This test should fail because configuration reload is not implemented

        await access_control_middleware.load_access_control_rules()
        initial_count = len(access_control_middleware.access_rules)

        # Simulate configuration change
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/new/pattern,admin;/another/pattern,user'
        }):
            await access_control_middleware.reload_configuration()

            # Should have new rules
            assert len(access_control_middleware.access_rules) == 2
            assert access_control_middleware.access_rules[0]['pattern'] == '/new/pattern'

    @pytest.mark.asyncio
    async def test_malformed_configuration_handling(self, access_control_middleware):
        """RED: Test handling of malformed configuration"""
        # This test should fail because error handling is not implemented

        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': 'invalid-format;/reviews/details'  # Missing permissions
        }):
            middleware = AccessControlMiddleware()

            with pytest.raises(AccessControlError, match="Malformed configuration"):
                await middleware.load_access_control_rules()

    @pytest.mark.asyncio
    async def test_empty_configuration_handling(self, access_control_middleware):
        """RED: Test handling of empty configuration"""
        # This test should fail because empty configuration handling is not implemented

        with patch.dict('os.environ', {}, clear=True):
            middleware = AccessControlMiddleware()
            await middleware.load_access_control_rules()

            # Should handle empty configuration gracefully
            assert middleware.access_rules == []

            # Should allow access to any URL when no rules defined
            result = await middleware.check_access('/any/url', None)
            assert result.is_success

    @pytest.mark.asyncio
    async def test_session_validation_with_ip_security(self, access_control_middleware):
        """RED: Test session validation with IP address security"""
        # This test should fail because IP security validation is not implemented

        await access_control_middleware.load_access_control_rules()

        session_data = {
            'identity_id': 'user_123',
            'user_type': 'admin',
            'auth_method': 'google',
            'is_active': True
        }
        access_control_middleware.session_service.validate_oauth_session.return_value = Result.success(session_data)

        # Test with IP address validation
        result = await access_control_middleware.check_access('/admin', 'session_123', '192.168.1.1')
        assert result.is_success

    @pytest.mark.asyncio
    async def test_access_logging_security(self, access_control_middleware):
        """RED: Test that access control logs don't expose sensitive information"""
        # This test should fail because secure logging is not implemented

        await access_control_middleware.load_access_control_rules()

        with patch('src.middleware.access_control_middleware.logger') as mock_logger:
            session_data = {
                'identity_id': 'user_123',
                'user_type': 'user',
                'auth_method': 'google',
                'is_active': True
            }
            access_control_middleware.session_service.validate_oauth_session.return_value = Result.success(session_data)

            await access_control_middleware.check_access('/reviews/details', 'secret_session_123')

            # Check that logs don't contain sensitive session information
            for call in mock_logger.info.call_args_list + mock_logger.debug.call_args_list:
                log_message = str(call)
                assert 'secret_session_123' not in log_message  # Session ID should be masked
                assert 'user_123' not in log_message  # Identity ID should be masked

    @pytest.mark.asyncio
    async def test_concurrent_access_control_checks(self, access_control_middleware):
        """RED: Test concurrent access control checks"""
        # This test should fail because concurrent handling is not implemented

        await access_control_middleware.load_access_control_rules()

        # Mock valid session
        session_data = {
            'identity_id': 'user_123',
            'user_type': 'user',
            'auth_method': 'google',
            'is_active': True
        }
        access_control_middleware.session_service.validate_oauth_session.return_value = Result.success(session_data)

        # Test multiple concurrent checks
        tasks = [
            access_control_middleware.check_access('/reviews/details', f'session_{i}')
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(result.is_success for result in results)

    @pytest.mark.asyncio
    async def test_middleware_integration_with_request_context(self, access_control_middleware):
        """RED: Test middleware integration with request context"""
        # This test should fail because request context integration is not implemented

        await access_control_middleware.load_access_control_rules()

        # Mock request context
        request_context = {
            'method': 'GET',
            'path': '/reviews/details/123',
            'headers': {'User-Agent': 'test-browser'},
            'remote_addr': '192.168.1.1'
        }

        session_data = {
            'identity_id': 'user_123',
            'user_type': 'user',
            'auth_method': 'google',
            'is_active': True
        }
        access_control_middleware.session_service.validate_oauth_session.return_value = Result.success(session_data)

        result = await access_control_middleware.process_request(request_context, 'session_123')
        assert result.is_success
        assert 'access_granted' in result.data
        assert 'user_context' in result.data


class TestReviewListAccessControl:
    """
    Task 10.1: レビュー一覧アクセス制御のテスト
    Requirements: 1.1, 1.2, 1.3, 1.7
    """

    @pytest.fixture
    def access_control_middleware(self):
        """Access control middleware fixture with mocked UserService"""
        middleware = AccessControlMiddleware()

        # Mock UserService
        mock_user_service = MagicMock()
        mock_user_service.check_review_access_within_one_year = AsyncMock()
        middleware.user_service = mock_user_service

        return middleware

    @pytest.mark.asyncio
    async def test_unauthenticated_user_gets_preview_access(self, access_control_middleware):
        """
        未認証ユーザーのアクセスレベル判定テスト
        Requirement 1.1: 未認証ユーザーはプレビューアクセスを取得
        """
        result = await access_control_middleware.check_review_list_access(
            user_id=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        assert result["access_level"] == "preview"
        assert result["can_filter"] is False
        assert result["message"] is None
        assert result["user_last_posted_at"] is None

    @pytest.mark.asyncio
    async def test_web_crawler_detection_googlebot(self, access_control_middleware):
        """
        Webクローラー検出テスト - Googlebot
        Requirement 1.2: Webクローラーは crawler アクセスレベルを取得
        """
        result = await access_control_middleware.check_review_list_access(
            user_id=None,
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        )

        assert result["access_level"] == "crawler"
        assert result["can_filter"] is False
        assert result["message"] is None

    @pytest.mark.asyncio
    async def test_web_crawler_detection_bingbot(self, access_control_middleware):
        """
        Webクローラー検出テスト - Bingbot
        Requirement 1.2: Webクローラーは crawler アクセスレベルを取得
        """
        result = await access_control_middleware.check_review_list_access(
            user_id=None,
            user_agent="Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        )

        assert result["access_level"] == "crawler"
        assert result["can_filter"] is False

    @pytest.mark.asyncio
    async def test_web_crawler_detection_case_insensitive(self, access_control_middleware):
        """
        Webクローラー検出テスト - 大文字小文字を区別しない
        Requirement 1.2: User-Agent の大文字小文字を区別せずに検出
        """
        result = await access_control_middleware.check_review_list_access(
            user_id=None,
            user_agent="Mozilla/5.0 (compatible; GOOGLEBOT/2.1)"
        )

        assert result["access_level"] == "crawler"

    @pytest.mark.asyncio
    async def test_user_with_recent_review_gets_full_access(self, access_control_middleware):
        """
        1年以内のレビュー投稿者のアクセスレベル判定テスト
        Requirement 1.3: 1年以内にレビューを投稿したユーザーはフルアクセスを取得
        """
        # Mock: ユーザーは1年以内にレビュー投稿済み
        access_control_middleware.user_service.check_review_access_within_one_year.return_value = True

        result = await access_control_middleware.check_review_list_access(
            user_id="user_123",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        assert result["access_level"] == "full"
        assert result["can_filter"] is True
        assert result["message"] is None

        # Verify UserService was called with correct user_id
        access_control_middleware.user_service.check_review_access_within_one_year.assert_called_once_with("user_123")

    @pytest.mark.asyncio
    async def test_user_with_old_review_gets_denied_access(self, access_control_middleware):
        """
        1年以上前の投稿者のアクセスレベル判定テスト
        Requirement 1.7: 1年以上前に投稿したユーザーはアクセス拒否
        """
        # Mock: ユーザーの最終レビュー投稿は1年以上前
        access_control_middleware.user_service.check_review_access_within_one_year.return_value = False

        result = await access_control_middleware.check_review_list_access(
            user_id="user_456",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        assert result["access_level"] == "denied"
        assert result["can_filter"] is False
        assert result["message"] == "Reviewを投稿いただいた方に閲覧権限を付与しています"

    @pytest.mark.asyncio
    async def test_user_without_review_history_gets_denied_access(self, access_control_middleware):
        """
        レビュー履歴なしユーザーのアクセスレベル判定テスト
        Requirement 1.7: レビュー履歴のないユーザーはアクセス拒否
        """
        # Mock: ユーザーはレビュー投稿履歴なし
        access_control_middleware.user_service.check_review_access_within_one_year.return_value = False

        result = await access_control_middleware.check_review_list_access(
            user_id="new_user_789",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        assert result["access_level"] == "denied"
        assert result["can_filter"] is False
        assert result["message"] == "Reviewを投稿いただいた方に閲覧権限を付与しています"

    @pytest.mark.asyncio
    async def test_crawler_detection_priority_over_authentication(self, access_control_middleware):
        """
        Webクローラー検出の優先度テスト
        Requirement 1.2: 認証済みユーザーでもクローラーUser-Agentならcrawlerアクセスレベル
        """
        # Mock: ユーザーは1年以内にレビュー投稿済み（通常ならfullアクセス）
        access_control_middleware.user_service.check_review_access_within_one_year.return_value = True

        result = await access_control_middleware.check_review_list_access(
            user_id="user_123",
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)"
        )

        # クローラー検出が優先される
        assert result["access_level"] == "crawler"
        assert result["can_filter"] is False

    @pytest.mark.asyncio
    async def test_error_handling_returns_denied_access(self, access_control_middleware):
        """
        エラーハンドリングテスト: エラー時は denied アクセスを返す
        Secure fail: システムエラー時はアクセス拒否
        """
        # Mock: UserService がエラーをスロー
        access_control_middleware.user_service.check_review_access_within_one_year.side_effect = Exception("Database error")

        result = await access_control_middleware.check_review_list_access(
            user_id="user_123",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        assert result["access_level"] == "denied"
        assert result["can_filter"] is False
        assert "エラーが発生しました" in result["message"]

    @pytest.mark.asyncio
    async def test_various_crawler_patterns(self, access_control_middleware):
        """
        さまざまなクローラーパターンの検出テスト
        Requirement 1.2: 主要なWebクローラーを検出
        """
        crawler_user_agents = [
            "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
            "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
            "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
            "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
            "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
            "Twitterbot/1.0",
        ]

        for user_agent in crawler_user_agents:
            result = await access_control_middleware.check_review_list_access(
                user_id=None,
                user_agent=user_agent
            )

            assert result["access_level"] == "crawler", f"Failed to detect crawler: {user_agent}"

    @pytest.mark.asyncio
    async def test_normal_browser_not_detected_as_crawler(self, access_control_middleware):
        """
        通常のブラウザがクローラーとして検出されないことを確認
        Requirement 1.2: 通常のブラウザUser-Agentはクローラーとして扱わない
        """
        normal_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
        ]

        for user_agent in normal_user_agents:
            result = await access_control_middleware.check_review_list_access(
                user_id=None,
                user_agent=user_agent
            )

            assert result["access_level"] == "preview", f"Normal browser incorrectly detected as crawler: {user_agent}"