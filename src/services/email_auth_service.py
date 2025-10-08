"""
Email Authentication Service
Task 5.1: メール認証用トークンとコード管理機能
"""
import logging
import secrets
import re
import bcrypt
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from ..services.email_encryption_service import EmailEncryptionService
from ..database import get_db_service
from ..utils.result import Result

logger = logging.getLogger(__name__)


class EmailAuthError(Exception):
    """Email authentication error"""
    pass


class EmailAuthService:
    """Email authentication service for token and code management"""

    COLLECTION_NAME = "email_verifications"
    VALID_VERIFICATION_TYPES = ["registration", "login"]
    TOKEN_EXPIRY_HOURS = 1  # 1 hour for verification tokens
    CODE_EXPIRY_MINUTES = 5  # 5 minutes for login codes
    MAX_ATTEMPTS = 3  # Maximum login attempts

    def __init__(self):
        """Initialize email auth service with required dependencies"""
        self.email_service = EmailEncryptionService()
        self.db_service = get_db_service()
        # Get secret key from environment
        import os
        secret_key = os.getenv('EMAIL_AUTH_SECRET_KEY', 'default-secret-key-change-in-production')
        self.serializer = URLSafeTimedSerializer(secret_key)

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_verification_type(self, verification_type: str) -> bool:
        """Validate verification type"""
        return verification_type in self.VALID_VERIFICATION_TYPES

    async def generate_verification_token(self, email: str, verification_type: str) -> Result[Dict[str, Any], EmailAuthError]:
        """Generate secure verification token"""
        try:
            # Validate email format
            if not self._validate_email(email):
                return Result.failure(EmailAuthError("Invalid email format"))

            # Validate verification type
            if not self._validate_verification_type(verification_type):
                return Result.failure(EmailAuthError("Invalid verification type"))

            # Generate secure token
            token = secrets.token_urlsafe(32)

            # Hash email for database storage
            email_hash = self.email_service.hash_email(email)

            # Calculate expiry time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.TOKEN_EXPIRY_HOURS)

            # Encrypt email for storage
            email_encrypted_result = self.email_service.encrypt_email(email)
            if not email_encrypted_result.is_success:
                return Result.failure(EmailAuthError("Failed to encrypt email"))

            # Create verification record
            verification_data = {
                'email_hash': email_hash,
                'email_encrypted': email_encrypted_result.data.encrypted,
                'verification_type': verification_type,
                'token': token,
                'expires_at': expires_at,
                'verified_at': None,
                'attempts': 0,
                'created_at': datetime.now(timezone.utc)
            }

            # Save to database
            verification_id = await self.db_service.create(self.COLLECTION_NAME, verification_data)

            return Result.success({
                'token': token,
                'expires_at': expires_at,
                'verification_id': verification_id
            })

        except Exception as e:
            logger.exception("Failed to generate verification token: %s", e)
            return Result.failure(EmailAuthError(f"Token generation failed: {e}"))

    async def verify_verification_token(self, token: str) -> Result[Dict[str, Any], EmailAuthError]:
        """Verify verification token"""
        try:
            logger.info("Searching for token in database: %s...", token[:20])
            # Find token in database
            verification = await self.db_service.find_one(
                self.COLLECTION_NAME,
                {'token': token, 'verified_at': None}
            )

            if not verification:
                logger.error("Token not found or already used")
                return Result.failure(EmailAuthError("Invalid or already used token"))

            logger.info("Token found in database - verification_type: %s, created_at: %s",
                       verification.get('verification_type'), verification.get('created_at'))

            # Check expiration - MongoDB returns timezone-naive datetime, treat as UTC
            expires_at = verification['expires_at']
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            logger.info("Token expires at: %s, current time: %s", expires_at, datetime.now(timezone.utc))

            if expires_at < datetime.now(timezone.utc):
                logger.error("Token has expired")
                return Result.failure(EmailAuthError("Token expired"))

            # Mark as verified
            logger.info("Marking token as verified")
            await self.db_service.update_one(
                self.COLLECTION_NAME,
                {'_id': verification['_id']},
                {'verified_at': datetime.now(timezone.utc)}
            )

            # Decrypt email for return
            email_encrypted = verification.get('email_encrypted')
            if email_encrypted:
                decrypted_email_result = self.email_service.decrypt_email(email_encrypted)
                if decrypted_email_result.is_success:
                    email = decrypted_email_result.data
                else:
                    logger.error("Failed to decrypt email: %s", decrypted_email_result.error)
                    email = 'unknown@example.com'
            else:
                logger.warning("No encrypted email found in verification record")
                email = 'unknown@example.com'

            logger.info("Token verification successful for email: %s", email)
            return Result.success({
                'email': email,
                'verification_type': verification['verification_type'],
                'verified_at': datetime.now(timezone.utc)
            })

        except Exception as e:
            logger.exception("Failed to verify token: %s", e)
            return Result.failure(EmailAuthError(f"Token verification failed: {e}"))

    async def generate_login_code(self, email: str) -> Result[Dict[str, Any], EmailAuthError]:
        """Generate 6-digit login code with bcrypt hashing"""
        try:
            # Validate email format
            if not self._validate_email(email):
                return Result.failure(EmailAuthError("Invalid email format"))

            # Generate 6-digit code using cryptographically secure random
            code = f"{secrets.randbelow(1000000):06d}"

            # Hash code with bcrypt
            code_hash = bcrypt.hashpw(code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Hash email for database storage
            email_hash = self.email_service.hash_email(email)

            # Calculate expiry time
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.CODE_EXPIRY_MINUTES)

            # Create verification record with hashed code
            verification_data = {
                'email_hash': email_hash,
                'verification_type': 'login',
                'code_hash': code_hash,
                'expires_at': expires_at,
                'verified_at': None,
                'attempts': 0,
                'created_at': datetime.now(timezone.utc)
            }

            # Save to database
            verification_id = await self.db_service.create(self.COLLECTION_NAME, verification_data)

            return Result.success({
                'code': code,
                'expires_at': expires_at,
                'verification_id': verification_id
            })

        except Exception as e:
            logger.exception("Failed to generate login code: %s", e)
            return Result.failure(EmailAuthError(f"Code generation failed: {e}"))

    async def verify_login_code(self, email: str, code: str) -> Result[bool, EmailAuthError]:
        """Verify 6-digit login code using bcrypt"""
        try:
            # Hash email for database lookup
            email_hash = self.email_service.hash_email(email)

            # Find verification record
            verification = await self.db_service.find_one(
                self.COLLECTION_NAME,
                {
                    'email_hash': email_hash,
                    'verification_type': 'login',
                    'verified_at': None
                }
            )

            if not verification:
                return Result.failure(EmailAuthError("No verification code found"))

            # Check expiration - MongoDB returns timezone-naive datetime, treat as UTC
            expires_at = verification['expires_at']
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                return Result.failure(EmailAuthError("Code expired"))

            # Check attempt limit
            if verification['attempts'] >= self.MAX_ATTEMPTS:
                return Result.failure(EmailAuthError("Too many attempts"))

            # Verify code with bcrypt
            code_hash = verification['code_hash']
            if not bcrypt.checkpw(code.encode('utf-8'), code_hash.encode('utf-8')):
                # Increment attempts
                await self.db_service.update_one(
                    self.COLLECTION_NAME,
                    {'_id': verification['_id']},
                    {'$inc': {'attempts': 1}}
                )
                return Result.failure(EmailAuthError("Invalid code"))

            # Mark as verified
            await self.db_service.update_one(
                self.COLLECTION_NAME,
                {'_id': verification['_id']},
                {'verified_at': datetime.now(timezone.utc)}
            )

            return Result.success(True)

        except Exception as e:
            logger.exception("Failed to verify login code: %s", e)
            return Result.failure(EmailAuthError(f"Code verification failed: {e}"))

    async def cleanup_expired_tokens(self) -> Result[int, EmailAuthError]:
        """Cleanup expired tokens and codes"""
        try:
            current_time = datetime.now(timezone.utc)

            # Delete expired verifications
            result = await self.db_service.delete_many(
                self.COLLECTION_NAME,
                {'expires_at': {'$lt': current_time}}
            )

            deleted_count = result.deleted_count if result else 0
            logger.info(f"Cleaned up {deleted_count} expired verifications")

            return Result.success(deleted_count)

        except Exception as e:
            logger.exception("Failed to cleanup expired tokens: %s", e)
            return Result.failure(EmailAuthError(f"Cleanup failed: {e}"))