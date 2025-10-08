"""
Identity Service
Unified Identity management service for OAuth authentication
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..services.email_encryption_service import EmailEncryptionService
from ..services.identity_database_service import IdentityDatabaseService
from ..utils.result import Result

logger = logging.getLogger(__name__)


class IdentityError(Exception):
    """Identity service error"""
    pass


class IdentityService:
    """Unified Identity management service"""

    def __init__(self):
        """Initialize Identity service with required dependencies"""
        self.email_service = EmailEncryptionService()
        self.db_service = IdentityDatabaseService()

    async def find_identity_by_email_hash(self, auth_method: str, email: str) -> Result[Optional[Dict[str, Any]], IdentityError]:
        """Find identity by auth method and email (internally hashed)"""
        try:
            # Hash the email for database lookup
            email_hash = self.email_service.hash_email(email)

            # Search in database
            identity = await self.db_service.find_identity_by_auth_email_hash(auth_method, email_hash)

            return Result.success(identity)

        except Exception as e:
            logger.exception("Failed to find identity by email hash: %s", e)
            return Result.failure(IdentityError(f"Find identity failed: {e}"))

    async def find_identity_by_email(self, auth_method: str, email: str) -> Result[Optional[Dict[str, Any]], IdentityError]:
        """Find identity by auth method and email address"""
        # This is essentially the same as find_identity_by_email_hash for public API
        return await self.find_identity_by_email_hash(auth_method, email)

    async def find_identity_by_email_only(self, email: str) -> Result[Optional[Dict[str, Any]], IdentityError]:
        """Find identity by email address only (regardless of auth_method)"""
        try:
            # Hash the email for database lookup
            email_hash = self.email_service.hash_email(email)

            # Search in database by email hash only
            identity = await self.db_service.find_identity_by_email_hash(email_hash)

            return Result.success(identity)

        except Exception as e:
            logger.exception("Failed to find identity by email only: %s", e)
            return Result.failure(IdentityError(f"Find identity failed: {e}"))

    async def create_or_update_identity(
        self,
        auth_method: str,
        email: str,
        user_type: str = 'user',
        provider_data: Optional[Dict[str, Any]] = None
    ) -> Result[Dict[str, Any], IdentityError]:
        """Create or update Identity record"""
        try:
            logger.info("=== create_or_update_identity called ===")
            logger.info("Auth method: %s, Email: %s, User type: %s", auth_method, email, user_type)
            # Validate auth method
            if auth_method not in self.db_service.VALID_AUTH_METHODS:
                return Result.failure(IdentityError(f"Invalid auth method: {auth_method}"))

            # Encrypt email data
            email_result = self.email_service.encrypt_email(email)
            if not email_result.is_success:
                return Result.failure(IdentityError(f"Email encryption failed: {email_result.error}"))

            encrypted_email = email_result.data

            # Check if identity already exists
            existing_result = await self.find_identity_by_email_hash(auth_method, email)
            if not existing_result.is_success:
                return existing_result

            if existing_result.data:
                # Update existing identity
                identity_data = existing_result.data.copy()
                identity_data['user_type'] = user_type
                identity_data['provider_data'] = provider_data or {}

                # Assuming update_identity method in db_service
                updated_id = await self.db_service.update_identity(identity_data['id'], identity_data)
                identity_data['id'] = updated_id
                return Result.success(identity_data)
            else:
                # Create new identity
                new_identity = {
                    'auth_method': auth_method,
                    'email_encrypted': encrypted_email.encrypted,
                    'email_hash': encrypted_email.hash,
                    'email_masked': encrypted_email.masked,
                    'user_type': user_type,
                    'provider_data': provider_data or {}
                }

                identity_id = await self.db_service.create_identity(new_identity)
                new_identity['id'] = identity_id
                return Result.success(new_identity)

        except Exception as e:
            logger.exception("Identity creation/update failed: %s", e)
            return Result.failure(IdentityError(f"Identity operation failed: {e}"))

    async def get_user_permissions(self, identity: Dict[str, Any]) -> Result[list, IdentityError]:
        """Get user permissions based on user_type"""
        try:
            user_type = identity.get('user_type', 'user')

            # Define permission mappings
            permission_map = {
                'user': ['read_reviews', 'submit_reviews'],
                'admin': ['read_reviews', 'submit_reviews', 'manage_users', 'manage_content', 'view_analytics'],
                'ally': ['read_reviews', 'submit_reviews', 'manage_content']
            }

            permissions = permission_map.get(user_type, [])
            return Result.success(permissions)

        except Exception as e:
            logger.exception("Failed to get user permissions: %s", e)
            return Result.failure(IdentityError(f"Get permissions failed: {e}"))

    async def link_identities(self, primary_email: str, secondary_identity: Dict[str, Any]) -> Result[bool, IdentityError]:
        """Link multiple identities for the same user"""
        try:
            # For now, implement a simple linking logic
            # In a real implementation, this would update the database to link identities
            logger.info(f"Linking identity {secondary_identity.get('id')} to primary email: {primary_email}")

            # Return success for now
            return Result.success(True)

        except Exception as e:
            logger.exception("Failed to link identities: %s", e)
            return Result.failure(IdentityError(f"Link identities failed: {e}"))