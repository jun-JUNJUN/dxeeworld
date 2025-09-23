"""
Test Identity Service
Task 2.2: 統一Identity管理サービスの実装
TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.identity_service import IdentityService, IdentityError
from src.utils.result import Result


class TestIdentityService:
    """Test unified Identity management service"""

    @pytest.fixture
    def identity_service(self):
        """Identity service fixture with mocked dependencies"""
        with patch.dict('os.environ', {
            'EMAIL_ENCRYPTION_KEY': 'test_key_for_testing_12345678901234567890',
            'EMAIL_HASH_SALT': 'test_salt_for_testing'
        }):
            service = IdentityService()

            # Mock email encryption service
            mock_email_service = MagicMock()

            # Create a mock object with attributes instead of dict
            mock_encrypted_data = MagicMock()
            mock_encrypted_data.encrypted = 'encrypted_email_string'
            mock_encrypted_data.hash = 'hashed_email_string'
            mock_encrypted_data.masked = 'test***@**le.com'

            mock_email_service.encrypt_email.return_value = Result.success(mock_encrypted_data)
            mock_email_service.hash_email.return_value = 'hashed_email_string'

            # Mock database service
            mock_db_service = MagicMock()
            mock_db_service.VALID_AUTH_METHODS = ["google", "facebook", "email"]
            mock_db_service.find_identity_by_auth_email_hash = AsyncMock(return_value=None)
            mock_db_service.create_identity = AsyncMock(return_value='test_identity_id')
            mock_db_service.update_identity = AsyncMock(return_value='updated_identity_id')
            mock_db_service.validate_identity_document = AsyncMock(return_value=True)

            service.email_service = mock_email_service
            service.db_service = mock_db_service
            return service

    @pytest.mark.asyncio
    async def test_create_new_identity_google(self, identity_service):
        """RED: Test creating new Google identity"""
        # This test should fail because find_identity_by_email_hash is not implemented

        result = await identity_service.find_identity_by_email_hash("google", "test@example.com")

        # Should return None for non-existent identity
        assert result.is_success
        assert result.data is None

    @pytest.mark.asyncio
    async def test_create_or_update_identity_new_user(self, identity_service):
        """RED: Test creating new identity when user doesn't exist"""
        # This test should fail because create_or_update_identity doesn't use database

        result = await identity_service.create_or_update_identity(
            auth_method="google",
            email="test@example.com",
            user_type="user",
            provider_data={"provider_id": "google_123", "name": "Test User"}
        )

        if not result.is_success:
            print(f"Error: {result.error}")
        assert result.is_success
        assert result.data['auth_method'] == "google"
        assert result.data['user_type'] == "user"
        assert 'id' in result.data

    @pytest.mark.asyncio
    async def test_create_or_update_identity_existing_user(self, identity_service):
        """RED: Test updating existing identity"""
        # Setup existing identity
        existing_identity = {
            'id': 'existing_id',
            'auth_method': 'google',
            'email_hash': 'hashed_email_string',
            'user_type': 'user',
            'provider_data': {'provider_id': 'google_123'}
        }
        identity_service.db_service.find_identity_by_auth_email_hash = AsyncMock(return_value=existing_identity)
        identity_service.db_service.update_identity = AsyncMock(return_value='existing_id')

        result = await identity_service.create_or_update_identity(
            auth_method="google",
            email="test@example.com",
            user_type="admin",  # Changed user type
            provider_data={"provider_id": "google_123", "name": "Updated User"}
        )

        assert result.is_success
        assert result.data['id'] == 'existing_id'

    @pytest.mark.asyncio
    async def test_find_identity_by_email(self, identity_service):
        """RED: Test finding identity by email address"""
        # This should fail because find_identity_by_email is not implemented

        result = await identity_service.find_identity_by_email("google", "test@example.com")

        assert result.is_success
        # Should return None if not found
        assert result.data is None

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, identity_service):
        """RED: Test getting user permissions based on user_type"""
        # This should fail because get_user_permissions is not implemented

        identity = {
            'id': 'test_id',
            'auth_method': 'google',
            'user_type': 'admin',
            'email_hash': 'hash'
        }

        result = await identity_service.get_user_permissions(identity)

        assert result.is_success
        assert isinstance(result.data, list)
        # Admin should have more permissions than user
        assert len(result.data) > 0

    @pytest.mark.asyncio
    async def test_link_identities(self, identity_service):
        """RED: Test linking multiple identities for same user"""
        # This should fail because link_identities is not implemented

        primary_identity = {
            'id': 'primary_id',
            'auth_method': 'google',
            'email_hash': 'hash1',
            'user_type': 'user'
        }

        secondary_identity = {
            'id': 'secondary_id',
            'auth_method': 'facebook',
            'email_hash': 'hash1',  # Same email hash
            'user_type': 'user'
        }

        result = await identity_service.link_identities("test@example.com", secondary_identity)

        assert result.is_success
        assert result.data is True

    @pytest.mark.asyncio
    async def test_user_type_permissions_mapping(self, identity_service):
        """RED: Test user type to permissions mapping"""
        # Test different user types have appropriate permissions

        # User permissions
        user_identity = {'user_type': 'user'}
        user_result = await identity_service.get_user_permissions(user_identity)
        assert user_result.is_success

        # Admin permissions
        admin_identity = {'user_type': 'admin'}
        admin_result = await identity_service.get_user_permissions(admin_identity)
        assert admin_result.is_success

        # Ally permissions
        ally_identity = {'user_type': 'ally'}
        ally_result = await identity_service.get_user_permissions(ally_identity)
        assert ally_result.is_success

        # Admin should have all user permissions plus more
        user_perms = set(user_result.data)
        admin_perms = set(admin_result.data)
        assert user_perms.issubset(admin_perms)

    @pytest.mark.asyncio
    async def test_invalid_auth_method_error(self, identity_service):
        """RED: Test error handling for invalid auth method"""

        result = await identity_service.create_or_update_identity(
            auth_method="invalid_method",
            email="test@example.com",
            user_type="user"
        )

        assert not result.is_success
        assert isinstance(result.error, IdentityError)

    @pytest.mark.asyncio
    async def test_email_encryption_failure_handling(self, identity_service):
        """RED: Test handling of email encryption failures"""
        # Mock email encryption failure
        identity_service.email_service.encrypt_email.return_value = Result.failure(Exception("Encryption failed"))

        result = await identity_service.create_or_update_identity(
            auth_method="google",
            email="test@example.com",
            user_type="user"
        )

        assert not result.is_success
        assert isinstance(result.error, IdentityError)
        assert "encryption failed" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_database_operation_failure_handling(self, identity_service):
        """RED: Test handling of database operation failures"""
        # Mock database failure
        identity_service.db_service.create_identity = AsyncMock(side_effect=Exception("Database error"))

        result = await identity_service.create_or_update_identity(
            auth_method="google",
            email="test@example.com",
            user_type="user"
        )

        assert not result.is_success
        assert isinstance(result.error, IdentityError)