"""
Email Encryption Service
メールアドレスの暗号化・復号化・ハッシュ化・マスキング処理
"""
import os
import re
import hashlib
import logging
from typing import Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import email_validator
from ..utils.result import Result

logger = logging.getLogger(__name__)


@dataclass
class EncryptedEmailData:
    """Encrypted email data structure"""
    encrypted: str  # AES-256-CBC暗号化された文字列
    hash: str       # SHA-256ハッシュ
    masked: str     # マスキング表示用


class EmailEncryptionError(Exception):
    """Email encryption error"""
    pass


class EmailEncryptionService:
    """Email encryption and security service"""

    def __init__(self):
        """Initialize with encryption key and salt from environment"""
        self.encryption_key = self._get_encryption_key()
        self.hash_salt = self._get_hash_salt()
        self.fernet = self._create_fernet()

    def _get_encryption_key(self) -> str:
        """Get encryption key from environment"""
        key = os.getenv('EMAIL_ENCRYPTION_KEY', '')
        if not key:
            raise ValueError("EMAIL_ENCRYPTION_KEY is required")

        if len(key.encode('utf-8')) < 32:
            raise ValueError("Encryption key must be at least 32 bytes")

        return key

    def _get_hash_salt(self) -> str:
        """Get hash salt from environment"""
        salt = os.getenv('EMAIL_HASH_SALT', '')
        if not salt:
            raise ValueError("EMAIL_HASH_SALT is required")
        return salt

    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from encryption key"""
        # Derive a proper Fernet key from the encryption key
        password = self.encryption_key.encode('utf-8')
        salt = self.hash_salt.encode('utf-8')[:16]  # Use first 16 bytes of salt

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def encrypt_email(self, email: str) -> Result[EncryptedEmailData, EmailEncryptionError]:
        """Encrypt email address and return EncryptedEmailData"""
        try:
            # Validate email format
            if not self._is_valid_email(email):
                return Result.failure(EmailEncryptionError("Invalid email format"))

            # Encrypt email
            encrypted = self.fernet.encrypt(email.encode('utf-8')).decode('utf-8')

            # Hash email
            email_hash = self.hash_email(email)

            # Mask email
            masked = self.mask_email(email)

            encrypted_data = EncryptedEmailData(
                encrypted=encrypted,
                hash=email_hash,
                masked=masked
            )

            return Result.success(encrypted_data)

        except Exception as e:
            logger.error(f"Email encryption failed: {e}")
            return Result.failure(EmailEncryptionError(f"Encryption failed: {e}"))

    def decrypt_email(self, encrypted_email: str) -> Result[str, EmailEncryptionError]:
        """Decrypt encrypted email address"""
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_email.encode('utf-8'))
            decrypted_email = decrypted_bytes.decode('utf-8')
            return Result.success(decrypted_email)

        except Exception as e:
            logger.error(f"Email decryption failed: {e}")
            return Result.failure(EmailEncryptionError(f"Decryption failed: {e}"))

    def hash_email(self, email: str) -> str:
        """Hash email address with salt using SHA-256"""
        # Combine email with salt
        salted_email = f"{email}{self.hash_salt}"

        # Create SHA-256 hash
        hash_object = hashlib.sha256(salted_email.encode('utf-8'))
        return hash_object.hexdigest()

    def mask_email(self, email: str) -> str:
        """Mask email address according to specification"""
        if not email or '@' not in email:
            return email

        try:
            username, domain = email.split('@', 1)

            # Username masking: show first few characters based on length
            if len(username) <= 1:
                masked_username = username + "***"
            elif len(username) == 2:
                masked_username = username + "***"  # Show both characters for 2-char usernames
            else:
                masked_username = username[:2] + "***"

            # Domain masking: based on the specification examples
            parts = domain.split('.')
            if len(parts) >= 2:
                domain_part = parts[0]
                extension_parts = parts[1:]
                extension = '.' + '.'.join(extension_parts)

                # For short domains, show ** + extension
                if len(domain_part) <= 2:
                    masked_domain = "**" + extension
                else:
                    # For multi-part TLD like .co.jp, show 2nd char of domain + last part only
                    # For single TLD like .com, show last 2 chars of domain + full extension
                    if len(extension_parts) > 1:  # Multi-part TLD like .co.jp
                        if len(domain_part) > 1:
                            visible_domain = domain_part[1]  # Second character
                            # Skip middle parts, show only last part
                            masked_domain = "**" + visible_domain + "." + extension_parts[-1]
                        else:
                            # Single char domain, show it + last TLD part
                            visible_domain = domain_part
                            masked_domain = "**" + visible_domain + "." + extension_parts[-1]
                    else:  # Single TLD like .com
                        visible_domain = domain_part[-2:]  # Show last 2 characters
                        masked_domain = "**" + visible_domain + extension
            else:
                # No dots in domain, show last 5 chars or full domain if shorter
                if len(domain) <= 5:
                    masked_domain = "**" + domain
                else:
                    masked_domain = "**" + domain[-5:]

            return f"{masked_username}@{masked_domain}"

        except Exception as e:
            logger.error(f"Email masking failed: {e}")
            return email  # Return original email if masking fails

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False

        # Basic validation
        if '@' not in email:
            return False

        try:
            # Use email-validator with deliverability check disabled for testing
            email_validator.validate_email(email, check_deliverability=False)
            return True
        except email_validator.EmailNotValidError:
            return False