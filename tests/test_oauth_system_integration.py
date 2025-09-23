"""
Test OAuth System Integration
Task 9.2: 全認証システムの統合テストと検証
Integration tests to verify complete OAuth authentication system
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.oauth_session_service import OAuthSessionService
from src.middleware.access_control_middleware import AccessControlMiddleware
from src.services.ui_auth_service import UIAuthService
from src.services.auth_error_handler import AuthErrorHandler
from src.utils.result import Result


class TestOAuthSystemIntegration:
    """Integration tests for complete OAuth authentication system"""

    @pytest.fixture
    def oauth_system(self):
        """Complete OAuth system fixture"""
        # Initialize all components
        session_service = OAuthSessionService()
        access_control = AccessControlMiddleware()
        ui_service = UIAuthService()
        error_handler = AuthErrorHandler()

        # Mock database service
        mock_db_service = MagicMock()
        mock_db_service.create = AsyncMock(return_value='test_session_id')
        mock_db_service.find_one = AsyncMock(return_value=None)
        mock_db_service.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_db_service.update_many = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_db_service.delete_many = AsyncMock(return_value=MagicMock(deleted_count=1))

        # Mock find method with async cursor
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db_service.find = MagicMock(return_value=mock_cursor)

        session_service.db_service = mock_db_service

        # Configure access control with test rules
        access_control.access_rules = [
            {'pattern': '/reviews/details', 'permissions': ['user', 'admin', 'ally']},
            {'pattern': '/reviews/submit', 'permissions': ['user', 'admin']},
            {'pattern': '/admin', 'permissions': ['admin']}
        ]

        # Link services
        ui_service.session_service = session_service
        ui_service.access_control = access_control

        return {
            'session_service': session_service,
            'access_control': access_control,
            'ui_service': ui_service,
            'error_handler': error_handler
        }

    @pytest.mark.asyncio
    async def test_complete_google_auth_flow(self, oauth_system):
        """Integration test: Complete Google authentication flow"""
        session_service = oauth_system['session_service']
        ui_service = oauth_system['ui_service']

        # Step 1: User accesses protected content without authentication
        result = await ui_service.get_login_panel_state('/reviews/details', None)
        assert result.is_success
        assert result.data['show_panel'] is True
        assert 'google' in result.data['auth_methods']

        # Step 2: Simulate successful Google authentication
        identity = {
            'id': 'google_user_123',
            'auth_method': 'google',
            'email_masked': 'user***@**le.com',
            'user_type': 'user'
        }

        session_result = await session_service.create_oauth_session(identity, 'browser', '192.168.1.1')
        assert session_result.is_success
        session_id = session_result.data['session_id']

        # Step 3: Verify access to protected content
        access_result = await ui_service.check_review_access('/reviews/details', session_id)
        assert access_result.is_success
        assert access_result.data['access_granted'] is True

        # Step 4: Verify login panel is hidden
        panel_result = await ui_service.get_login_panel_state('/reviews/details', session_id)
        assert panel_result.is_success
        assert panel_result.data['show_panel'] is False

        # Step 5: Verify user menu shows authenticated state
        menu_result = await ui_service.get_user_menu_info(session_id)
        assert menu_result.is_success
        assert menu_result.data['authenticated'] is True
        assert menu_result.data['auth_method'] == 'google'

    @pytest.mark.asyncio
    async def test_access_control_integration(self, oauth_system):
        """Integration test: Access control with different user types"""
        session_service = oauth_system['session_service']
        access_control = oauth_system['access_control']

        # Test admin access
        admin_identity = {
            'id': 'admin_123',
            'auth_method': 'email',
            'user_type': 'admin'
        }
        admin_session = await session_service.create_oauth_session(admin_identity, 'browser', '192.168.1.1')
        admin_session_id = admin_session.data['session_id']

        # Mock session validation for admin
        session_service.db_service.find_one.return_value = {
            'session_id': admin_session_id,
            'identity_id': 'admin_123',
            'user_type': 'admin',
            'auth_method': 'email',
            'is_active': True,
            'expires_at': '2024-12-31T23:59:59Z',
            'last_accessed': '2024-01-01T00:00:00Z'
        }

        # Admin should access all protected areas
        admin_access = await access_control.check_access('/admin', admin_session_id)
        assert admin_access.is_success
        assert admin_access.data['access_granted'] is True

        # Test user access to admin area (should fail)
        user_identity = {
            'id': 'user_123',
            'auth_method': 'facebook',
            'user_type': 'user'
        }
        user_session = await session_service.create_oauth_session(user_identity, 'browser', '192.168.1.2')
        user_session_id = user_session.data['session_id']

        # Mock session validation for user
        session_service.db_service.find_one.return_value = {
            'session_id': user_session_id,
            'identity_id': 'user_123',
            'user_type': 'user',
            'auth_method': 'facebook',
            'is_active': True,
            'expires_at': '2024-12-31T23:59:59Z',
            'last_accessed': '2024-01-01T00:00:00Z'
        }

        user_access = await access_control.check_access('/admin', user_session_id)
        assert not user_access.is_success

    @pytest.mark.asyncio
    async def test_session_security_integration(self, oauth_system):
        """Integration test: Session security validation"""
        session_service = oauth_system['session_service']
        ui_service = oauth_system['ui_service']

        # Create session from specific IP
        identity = {
            'id': 'user_123',
            'auth_method': 'google',
            'user_type': 'user'
        }
        session_result = await session_service.create_oauth_session(identity, 'browser', '192.168.1.1')
        session_id = session_result.data['session_id']

        # Mock session with IP validation
        session_service.db_service.find_one.return_value = {
            'session_id': session_id,
            'identity_id': 'user_123',
            'user_type': 'user',
            'ip_address': '192.168.1.1',
            'is_active': True,
            'expires_at': '2024-12-31T23:59:59Z',
            'last_accessed': '2024-01-01T00:00:00Z'
        }

        # Access from same IP should succeed
        request_context = {
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0',
            'path': '/reviews/details'
        }
        result = await ui_service.validate_session_for_ui(session_id, request_context)
        assert result.is_success
        assert result.data['security_validated'] is True

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, oauth_system):
        """Integration test: Error handling across system"""
        error_handler = oauth_system['error_handler']
        ui_service = oauth_system['ui_service']

        # Test OAuth provider error
        google_error = Exception("invalid_grant: Code was already redeemed")
        error_result = error_handler.handle_oauth_error('google', google_error)

        assert error_result.retry_allowed is True
        assert "認証コード" in error_result.user_message
        assert 'error_id' in error_result.metadata

        # Test service unavailable error cascading through UI
        ui_service.session_service.validate_oauth_session = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        ui_result = await ui_service.get_user_menu_info('session_123')
        assert not ui_result.is_success

    @pytest.mark.asyncio
    async def test_concurrent_session_management(self, oauth_system):
        """Integration test: Concurrent session management"""
        session_service = oauth_system['session_service']

        identity = {
            'id': 'user_123',
            'auth_method': 'email',
            'user_type': 'user'
        }

        # Create multiple sessions for same user
        sessions = []
        for i in range(5):
            result = await session_service.create_oauth_session(identity, f'browser_{i}', f'192.168.1.{i+1}')
            if result.is_success:
                sessions.append(result.data['session_id'])

        # Verify sessions were created
        assert len(sessions) > 0

    @pytest.mark.asyncio
    async def test_logout_and_cleanup_integration(self, oauth_system):
        """Integration test: Logout and session cleanup"""
        session_service = oauth_system['session_service']
        ui_service = oauth_system['ui_service']

        # Create session
        identity = {
            'id': 'user_123',
            'auth_method': 'google',
            'user_type': 'user'
        }
        session_result = await session_service.create_oauth_session(identity, 'browser', '192.168.1.1')
        session_id = session_result.data['session_id']

        # Logout
        logout_result = await ui_service.handle_logout(session_id, '/current/page')
        assert logout_result.is_success
        assert logout_result.data['logout_successful'] is True

        # Cleanup expired sessions
        cleanup_result = await session_service.cleanup_expired_sessions()
        assert cleanup_result.is_success

    @pytest.mark.asyncio
    async def test_ui_state_consistency(self, oauth_system):
        """Integration test: UI state consistency across components"""
        ui_service = oauth_system['ui_service']

        # Test unauthenticated state consistency
        panel_state = await ui_service.get_login_panel_state('/reviews/details', None)
        menu_info = await ui_service.get_user_menu_info(None)

        assert panel_state.data['show_panel'] is True
        assert menu_info.data['authenticated'] is False

        # Verify auth methods are consistent
        assert 'auth_methods' in panel_state.data
        assert 'login_methods' in menu_info.data

    @pytest.mark.asyncio
    async def test_data_protection_and_security(self, oauth_system):
        """Integration test: Data protection and security measures"""
        session_service = oauth_system['session_service']
        error_handler = oauth_system['error_handler']

        # Test sensitive data masking in logs
        with patch('src.services.oauth_session_service.logger') as mock_logger:
            identity = {
                'id': 'sensitive_user_id_123',
                'auth_method': 'google',
                'user_type': 'user',
                'email_masked': 'user***@**le.com'
            }
            await session_service.create_oauth_session(identity, 'browser', '192.168.1.1')

            # Verify sensitive data is masked in logs
            logged_calls = [str(call) for call in mock_logger.info.call_args_list]
            for call in logged_calls:
                assert 'sensitive_user_id_123' not in call

        # Test error context doesn't expose sensitive data
        context = {
            'user_id': 'sensitive_123',
            'auth_method': 'google',
            'ip_address': '192.168.1.1'
        }
        error_result = error_handler.handle_error_with_context(Exception("Test error"), context)
        assert 'user_id' not in error_result.metadata.get('context', {})
        assert 'ip_address' not in error_result.metadata.get('context', {})

    @pytest.mark.asyncio
    async def test_system_resilience(self, oauth_system):
        """Integration test: System resilience under failure conditions"""
        ui_service = oauth_system['ui_service']

        # Test graceful handling of service failures
        ui_service.session_service.validate_oauth_session = AsyncMock(
            side_effect=Exception("Service temporarily unavailable")
        )

        # UI should still provide meaningful responses
        menu_result = await ui_service.get_user_menu_info('session_123')
        assert not menu_result.is_success

        panel_result = await ui_service.get_login_panel_state('/reviews/details', 'session_123')
        # Should fall back to showing login panel
        assert panel_result.is_success