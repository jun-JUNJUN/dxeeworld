"""
Identity Database Service
MongoDB Identityコレクションとインデックス管理サービス
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from ..database import get_db_service

logger = logging.getLogger(__name__)


class IdentityDatabaseService:
    """Identity collection management service"""

    COLLECTION_NAME = "identities"
    VALID_AUTH_METHODS = ["google", "facebook", "email"]
    VALID_USER_TYPES = ["user", "admin", "ally"]

    def __init__(self):
        self.db_service = get_db_service()

    async def validate_identity_document(self, identity: Dict[str, Any]) -> bool:
        """Validate identity document structure and constraints"""

        # Required fields validation
        required_fields = ["auth_method", "email_encrypted", "email_hash", "user_type"]
        for field in required_fields:
            if field not in identity:
                raise ValueError(f"{field} is required")

        # Auth method enum validation
        if identity["auth_method"] not in self.VALID_AUTH_METHODS:
            raise ValueError(f"auth_method must be one of: {self.VALID_AUTH_METHODS}")

        # User type enum validation
        if identity["user_type"] not in self.VALID_USER_TYPES:
            raise ValueError(f"user_type must be one of: {self.VALID_USER_TYPES}")

        return True

    async def create_unique_auth_email_index(self) -> str:
        """Create unique index for (auth_method, email_hash)"""
        try:
            # Create unique compound index for auth_method and email_hash
            index_spec = [("auth_method", 1), ("email_hash", 1)]
            result = await self.db_service.create_index(
                collection=self.COLLECTION_NAME,
                index_spec=index_spec,
                unique=True,
                name="auth_method_1_email_hash_1"
            )
            logger.info(f"Unique index created: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create unique index: {e}")
            raise

    async def create_email_usertype_index(self) -> str:
        """Create index for (email_hash, user_type)"""
        try:
            # Create compound index for email_hash and user_type
            index_spec = [("email_hash", 1), ("user_type", 1)]
            result = await self.db_service.create_index(
                collection=self.COLLECTION_NAME,
                index_spec=index_spec,
                name="email_usertype"
            )
            logger.info(f"Email usertype index created: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create email_usertype index: {e}")
            raise

    async def create_identity(self, identity: Dict[str, Any]) -> Optional[str]:
        """Create new identity document"""
        try:
            # Validate document before creation
            await self.validate_identity_document(identity)

            # Add timestamps
            now = datetime.now(timezone.utc)
            identity["created_at"] = now
            identity["updated_at"] = now

            # Set default values
            if "email_verified" not in identity:
                identity["email_verified"] = False
            if "is_active" not in identity:
                identity["is_active"] = True

            # Create document
            result = await self.db_service.create(self.COLLECTION_NAME, identity)
            logger.info(f"Identity created with ID: {result}")
            return result

        except DuplicateKeyError as e:
            logger.error(f"Duplicate identity: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create identity: {e}")
            raise

    async def setup_indexes(self) -> Dict[str, str]:
        """Setup all required indexes for identity collection"""
        try:
            results = {}

            # Create unique index for (auth_method, email_hash)
            unique_index = await self.create_unique_auth_email_index()
            results["unique_auth_email"] = unique_index

            # Create index for (email_hash, user_type)
            usertype_index = await self.create_email_usertype_index()
            results["email_usertype"] = usertype_index

            logger.info("All identity indexes created successfully")
            return results

        except Exception as e:
            logger.error(f"Failed to setup indexes: {e}")
            raise

    async def find_identity_by_auth_email_hash(self, auth_method: str, email_hash: str) -> Optional[Dict[str, Any]]:
        """Find identity by auth_method and email_hash"""
        try:
            filter_dict = {
                "auth_method": auth_method,
                "email_hash": email_hash
            }
            result = await self.db_service.find_one(self.COLLECTION_NAME, filter_dict)
            return result
        except Exception as e:
            logger.error(f"Failed to find identity: {e}")
            return None

    async def list_indexes(self) -> list:
        """List all indexes on identity collection"""
        try:
            indexes = await self.db_service.list_indexes(self.COLLECTION_NAME)
            return indexes
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []

    async def update_identity(self, identity_id: str, updated_data: Dict[str, Any]) -> Optional[str]:
        """Update existing identity document"""
        try:
            # Validate updated document before updating
            await self.validate_identity_document(updated_data)

            # Add updated timestamp
            updated_data["updated_at"] = datetime.now(timezone.utc)

            # Update document
            filter_dict = {"_id": ObjectId(identity_id)}
            result = await self.db_service.update_one(self.COLLECTION_NAME, filter_dict, {"$set": updated_data})

            if result and result.modified_count > 0:
                logger.info(f"Identity updated: {identity_id}")
                return identity_id
            else:
                logger.warning(f"No identity updated for ID: {identity_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to update identity: {e}")
            raise