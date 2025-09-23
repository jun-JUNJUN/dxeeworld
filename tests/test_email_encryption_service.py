"""
Test Email Encryption Service
Task 2.1: メールアドレス暗号化とセキュリティサービスの実装
"""
import pytest
import os
from unittest.mock import patch
from src.services.email_encryption_service import EmailEncryptionService, EncryptedEmailData


class TestEmailEncryptionService:
    """Test Email Encryption Service implementation"""

    @pytest.fixture
    def encryption_service(self):
        """Email encryption service fixture"""
        # Mock environment variables for testing
        test_env = {
            'EMAIL_ENCRYPTION_KEY': 'test_encryption_key_32_bytes_long!',
            'EMAIL_HASH_SALT': 'test_salt_for_hashing_emails'
        }
        with patch.dict(os.environ, test_env):
            return EmailEncryptionService()

    def test_encrypt_email_returns_encrypted_data(self, encryption_service):
        """Test email encryption returns EncryptedEmailData"""
        # RED: テスト先行 - EmailEncryptionServiceがまだ実装されていない

        email = "user@example.com"
        result = encryption_service.encrypt_email(email)

        assert isinstance(result.data, EncryptedEmailData)
        assert result.is_success

        encrypted_data = result.data
        assert encrypted_data.encrypted != email  # 暗号化されていること
        assert encrypted_data.hash != email  # ハッシュ化されていること
        assert encrypted_data.masked != email  # マスキングされていること
        assert len(encrypted_data.encrypted) > 0
        assert len(encrypted_data.hash) > 0

    def test_decrypt_email_returns_original_email(self, encryption_service):
        """Test email decryption returns original email"""
        # RED: テスト先行 - 復号化機能がまだ実装されていない

        original_email = "test@example.com"

        # 暗号化
        encrypt_result = encryption_service.encrypt_email(original_email)
        assert encrypt_result.is_success

        encrypted_data = encrypt_result.data

        # 復号化
        decrypt_result = encryption_service.decrypt_email(encrypted_data.encrypted)
        assert decrypt_result.is_success
        assert decrypt_result.data == original_email

    def test_hash_email_is_consistent(self, encryption_service):
        """Test email hashing is consistent for same input"""
        # RED: テスト先行 - ハッシュ機能がまだ実装されていない

        email = "consistent@test.com"

        hash1 = encryption_service.hash_email(email)
        hash2 = encryption_service.hash_email(email)

        assert hash1 == hash2  # 同じメールアドレスは同じハッシュ
        assert hash1 != email  # ハッシュは元のメールアドレスと異なる
        assert len(hash1) == 64  # SHA-256のハッシュは64文字の16進数

    def test_hash_email_different_for_different_emails(self, encryption_service):
        """Test different emails produce different hashes"""
        # RED: テスト先行 - 異なるメールの異なるハッシュ確認がまだ実装されていない

        email1 = "user1@example.com"
        email2 = "user2@example.com"

        hash1 = encryption_service.hash_email(email1)
        hash2 = encryption_service.hash_email(email2)

        assert hash1 != hash2  # 異なるメールは異なるハッシュ

    def test_mask_email_follows_specification(self, encryption_service):
        """Test email masking follows the specification"""
        # RED: テスト先行 - マスキング機能がまだ実装されていない

        test_cases = [
            ("user@example.com", "us***@**le.com"),
            ("a@domain.co.jp", "a***@**o.jp"),
            ("longuser@company.com", "lo***@**ny.com"),
            ("ab@test.jp", "ab***@**st.jp"),
            ("verylongusername@verylongdomain.com", "ve***@**in.com")
        ]

        for email, expected_mask in test_cases:
            masked = encryption_service.mask_email(email)
            assert masked == expected_mask, f"Email {email} should mask to {expected_mask}, got {masked}"

    def test_mask_email_edge_cases(self, encryption_service):
        """Test email masking edge cases"""
        # RED: テスト先行 - エッジケースのマスキングがまだ実装されていない

        # 短いユーザー名
        assert encryption_service.mask_email("x@domain.com") == "x***@**in.com"

        # 短いドメイン
        assert encryption_service.mask_email("user@ab.co") == "us***@**.co"

        # 最小ケース
        assert encryption_service.mask_email("a@b.c") == "a***@**.c"

    def test_encryption_with_invalid_key_fails(self):
        """Test encryption fails with invalid key"""
        # RED: テスト先行 - 無効なキーでの暗号化失敗がまだ実装されていない

        invalid_env = {
            'EMAIL_ENCRYPTION_KEY': 'too_short',  # 32バイト未満
            'EMAIL_HASH_SALT': 'test_salt'
        }

        with patch.dict(os.environ, invalid_env):
            with pytest.raises(ValueError, match="Encryption key must be at least 32 bytes"):
                EmailEncryptionService()

    def test_hash_email_with_salt(self, encryption_service):
        """Test email hashing uses salt from environment"""
        # RED: テスト先行 - ソルト使用のハッシュ化がまだ実装されていない

        email = "test@example.com"

        # 異なるソルトで異なるハッシュが生成されることを確認
        hash1 = encryption_service.hash_email(email)

        # 異なるソルトでサービスを作成
        different_salt_env = {
            'EMAIL_ENCRYPTION_KEY': 'test_encryption_key_32_bytes_long!',
            'EMAIL_HASH_SALT': 'different_salt_for_testing'
        }

        with patch.dict(os.environ, different_salt_env):
            service2 = EmailEncryptionService()
            hash2 = service2.hash_email(email)

        assert hash1 != hash2  # 異なるソルトは異なるハッシュを生成

    def test_encryption_roundtrip_multiple_emails(self, encryption_service):
        """Test encryption/decryption roundtrip for multiple emails"""
        # RED: テスト先行 - 複数メールの暗号化往復がまだ実装されていない

        test_emails = [
            "user1@example.com",
            "admin@company.co.jp",
            "test+tag@domain.org",
            "user.name@sub.domain.com"
        ]

        for email in test_emails:
            # 暗号化
            encrypt_result = encryption_service.encrypt_email(email)
            assert encrypt_result.is_success

            # 復号化
            encrypted_data = encrypt_result.data
            decrypt_result = encryption_service.decrypt_email(encrypted_data.encrypted)
            assert decrypt_result.is_success
            assert decrypt_result.data == email

    def test_encrypted_email_data_structure(self, encryption_service):
        """Test EncryptedEmailData contains all required fields"""
        # RED: テスト先行 - EncryptedEmailDataクラスがまだ実装されていない

        email = "structure@test.com"
        result = encryption_service.encrypt_email(email)

        assert result.is_success
        encrypted_data = result.data

        # 必須フィールドが存在することを確認
        assert hasattr(encrypted_data, 'encrypted')
        assert hasattr(encrypted_data, 'hash')
        assert hasattr(encrypted_data, 'masked')

        # フィールドが文字列であることを確認
        assert isinstance(encrypted_data.encrypted, str)
        assert isinstance(encrypted_data.hash, str)
        assert isinstance(encrypted_data.masked, str)

        # 値が空でないことを確認
        assert len(encrypted_data.encrypted) > 0
        assert len(encrypted_data.hash) > 0
        assert len(encrypted_data.masked) > 0

    def test_email_encryption_uses_fernet(self, encryption_service):
        """Test email encryption uses Fernet (AES-256-CBC + HMAC-SHA256)"""
        # RED: テスト先行 - Fernet暗号化の使用がまだ実装されていない

        email = "fernet@test.com"
        result = encryption_service.encrypt_email(email)

        assert result.is_success
        encrypted_data = result.data

        # Fernetで暗号化されたデータは特定の形式を持つ
        # Base64エンコードされた文字列で、gAAAAAから始まる
        encrypted_string = encrypted_data.encrypted

        # Fernetトークンの基本検証
        assert isinstance(encrypted_string, str)
        assert len(encrypted_string) > 44  # Fernetトークンの最小長

        # 復号化できることで暗号化形式が正しいことを確認
        decrypt_result = encryption_service.decrypt_email(encrypted_string)
        assert decrypt_result.is_success
        assert decrypt_result.data == email

    def test_invalid_email_format_handling(self, encryption_service):
        """Test handling of invalid email formats"""
        # RED: テスト先行 - 無効なメールフォーマットの処理がまだ実装されていない

        invalid_emails = [
            "",  # 空文字列
            "invalid",  # @がない
            "@domain.com",  # ユーザー名がない
            "user@",  # ドメインがない
            "user@domain",  # TLDがない
        ]

        for invalid_email in invalid_emails:
            result = encryption_service.encrypt_email(invalid_email)
            assert not result.is_success  # 無効なメールアドレスはエラーになる

    def test_key_rotation_support(self, encryption_service):
        """Test support for key rotation"""
        # RED: テスト先行 - キーローテーション対応がまだ実装されていない

        email = "rotation@test.com"

        # 元のキーで暗号化
        original_result = encryption_service.encrypt_email(email)
        assert original_result.is_success
        original_encrypted = original_result.data.encrypted

        # 新しいキーでサービスを作成
        new_key_env = {
            'EMAIL_ENCRYPTION_KEY': 'new_encryption_key_32_bytes_long!!',
            'EMAIL_HASH_SALT': 'test_salt_for_hashing_emails'
        }

        with patch.dict(os.environ, new_key_env):
            new_service = EmailEncryptionService()

            # 古いキーで暗号化されたデータは復号化できない
            old_decrypt_result = new_service.decrypt_email(original_encrypted)
            assert not old_decrypt_result.is_success  # 復号化失敗

            # 新しいキーで暗号化
            new_result = new_service.encrypt_email(email)
            assert new_result.is_success

            # 新しいキーで復号化
            new_decrypt_result = new_service.decrypt_email(new_result.data.encrypted)
            assert new_decrypt_result.is_success
            assert new_decrypt_result.data == email