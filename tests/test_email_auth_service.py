"""
Test Email Authentication Service
Task 5.1: メール認証用トークンとコード管理機能
TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from src.services.email_auth_service import EmailAuthService, EmailAuthError
from src.utils.result import Result


class TestEmailAuthService:
    """Test email authentication service for token and code management"""

    @pytest.fixture
    def email_auth_service(self):
        """Email auth service fixture with mocked dependencies"""
        with patch.dict('os.environ', {
            'EMAIL_ENCRYPTION_KEY': 'test_key_for_testing_12345678901234567890',
            'EMAIL_HASH_SALT': 'test_salt_for_testing'
        }):
            service = EmailAuthService()

            # Mock database service
            mock_db_service = MagicMock()
            mock_db_service.create = AsyncMock(return_value='test_verification_id')
            mock_db_service.find_one = AsyncMock(return_value=None)
            mock_db_service.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            mock_db_service.delete_many = AsyncMock(return_value=MagicMock(deleted_count=1))

            service.db_service = mock_db_service
            return service

    @pytest.mark.asyncio
    async def test_generate_verification_token(self, email_auth_service):
        """RED: Test generating secure verification token"""
        # This test should fail because generate_verification_token is not implemented

        result = await email_auth_service.generate_verification_token("test@example.com", "registration")

        assert result.is_success
        assert 'token' in result.data
        assert 'expires_at' in result.data
        assert len(result.data['token']) > 20  # Should be secure token

    @pytest.mark.asyncio
    async def test_verify_verification_token(self, email_auth_service):
        """RED: Test verifying verification token"""
        # This test should fail because verify_verification_token is not implemented

        # First generate a token
        token_result = await email_auth_service.generate_verification_token("test@example.com", "registration")
        token = token_result.data['token']

        # Setup mock to return verification record for the token
        from datetime import datetime, timezone, timedelta
        mock_verification = {
            '_id': 'test_id',
            'token': token,
            'email_hash': 'test_hash',
            'verification_type': 'registration',
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
            'verified_at': None
        }
        email_auth_service.db_service.find_one.return_value = mock_verification

        # Then verify it
        result = await email_auth_service.verify_verification_token(token)

        assert result.is_success
        assert result.data['email'] == "test@example.com"
        assert result.data['verification_type'] == "registration"

    @pytest.mark.asyncio
    async def test_generate_login_code(self, email_auth_service):
        """RED: Test generating 6-digit login code"""
        # This test should fail because generate_login_code is not implemented

        result = await email_auth_service.generate_login_code("test@example.com")

        assert result.is_success
        assert 'code' in result.data
        assert 'expires_at' in result.data
        assert len(result.data['code']) == 6
        assert result.data['code'].isdigit()

    @pytest.mark.asyncio
    async def test_verify_login_code(self, email_auth_service):
        """RED: Test verifying 6-digit login code"""
        # This test should fail because verify_login_code is not implemented

        # First generate a code
        code_result = await email_auth_service.generate_login_code("test@example.com")
        code = code_result.data['code']

        # Setup mock to return verification record for the code
        from datetime import datetime, timezone, timedelta
        mock_verification = {
            '_id': 'test_id',
            'code': code,
            'email_hash': 'test_hash',
            'verification_type': 'login',
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
            'verified_at': None,
            'attempts': 0
        }
        email_auth_service.db_service.find_one.return_value = mock_verification

        # Then verify it
        result = await email_auth_service.verify_login_code("test@example.com", code)

        assert result.is_success
        assert result.data is True

    @pytest.mark.asyncio
    async def test_token_expiration(self, email_auth_service):
        """RED: Test token expiration handling"""
        # This test should fail because token expiration is not implemented

        # Mock expired token
        expired_token = "expired_token_12345"
        email_auth_service.db_service.find_one.return_value = {
            'token': expired_token,
            'email_hash': 'test_hash',
            'expires_at': datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            'verification_type': 'registration'
        }

        result = await email_auth_service.verify_verification_token(expired_token)

        assert not result.is_success
        assert "expired" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_code_attempt_limit(self, email_auth_service):
        """RED: Test login code attempt limit"""
        # This test should fail because attempt limit is not implemented

        email = "test@example.com"
        wrong_code = "999999"

        # Setup mock to return verification record that will exceed attempts
        from datetime import datetime, timezone, timedelta
        mock_verification = {
            '_id': 'test_id',
            'code': '123456',  # Different from wrong_code
            'email_hash': 'test_hash',
            'verification_type': 'login',
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
            'verified_at': None,
            'attempts': 2  # Already 2 attempts, next will exceed limit
        }
        email_auth_service.db_service.find_one.return_value = mock_verification

        # Try wrong code - should fail and increment attempts
        result = await email_auth_service.verify_login_code(email, wrong_code)
        assert not result.is_success

        # Next attempt should be blocked for too many attempts
        mock_verification['attempts'] = 3  # Simulate attempts exceeded
        result = await email_auth_service.verify_login_code(email, wrong_code)
        assert not result.is_success
        assert "too many attempts" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, email_auth_service):
        """RED: Test cleanup of expired tokens and codes"""
        # This test should fail because cleanup_expired_tokens is not implemented

        result = await email_auth_service.cleanup_expired_tokens()

        assert result.is_success
        assert isinstance(result.data, int)  # Number of deleted records

    @pytest.mark.asyncio
    async def test_token_one_time_use(self, email_auth_service):
        """RED: Test token can only be used once"""
        # This test should fail because one-time use is not implemented

        # Generate token
        token_result = await email_auth_service.generate_verification_token("test@example.com", "registration")
        token = token_result.data['token']

        # Setup mock to return verification record for first use
        from datetime import datetime, timezone, timedelta
        mock_verification = {
            '_id': 'test_id',
            'token': token,
            'email_hash': 'test_hash',
            'verification_type': 'registration',
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
            'verified_at': None
        }
        email_auth_service.db_service.find_one.return_value = mock_verification

        # First verification should succeed
        result1 = await email_auth_service.verify_verification_token(token)
        assert result1.is_success

        # Second verification should fail (token already used)
        email_auth_service.db_service.find_one.return_value = None  # No token found for already used
        result2 = await email_auth_service.verify_verification_token(token)
        assert not result2.is_success
        assert "already used" in str(result2.error).lower()

    @pytest.mark.asyncio
    async def test_code_one_time_use(self, email_auth_service):
        """RED: Test login code can only be used once"""
        # This test should fail because one-time use is not implemented

        email = "test@example.com"

        # Generate code
        code_result = await email_auth_service.generate_login_code(email)
        code = code_result.data['code']

        # Setup mock to return verification record for first use
        from datetime import datetime, timezone, timedelta
        mock_verification = {
            '_id': 'test_id',
            'code': code,
            'email_hash': 'test_hash',
            'verification_type': 'login',
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
            'verified_at': None,
            'attempts': 0
        }
        email_auth_service.db_service.find_one.return_value = mock_verification

        # First verification should succeed
        result1 = await email_auth_service.verify_login_code(email, code)
        assert result1.is_success

        # Second verification should fail (code already used)
        email_auth_service.db_service.find_one.return_value = None  # No code found for already used
        result2 = await email_auth_service.verify_login_code(email, code)
        assert not result2.is_success

    @pytest.mark.asyncio
    async def test_invalid_email_format(self, email_auth_service):
        """RED: Test handling of invalid email format"""
        # This test should fail because email validation is not implemented

        invalid_emails = ["invalid-email", "@domain.com", "user@", "user@domain"]

        for invalid_email in invalid_emails:
            result = await email_auth_service.generate_verification_token(invalid_email, "registration")
            assert not result.is_success
            assert isinstance(result.error, EmailAuthError)

    @pytest.mark.asyncio
    async def test_verification_type_validation(self, email_auth_service):
        """RED: Test verification type validation"""
        # This test should fail because verification type validation is not implemented

        invalid_types = ["invalid_type", "unknown", ""]

        for invalid_type in invalid_types:
            result = await email_auth_service.generate_verification_token("test@example.com", invalid_type)
            assert not result.is_success
            assert "invalid verification type" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_database_error_handling(self, email_auth_service):
        """RED: Test handling of database errors"""
        # Mock database failure
        email_auth_service.db_service.create = AsyncMock(side_effect=Exception("Database error"))

        result = await email_auth_service.generate_verification_token("test@example.com", "registration")

        assert not result.is_success
        assert isinstance(result.error, EmailAuthError)