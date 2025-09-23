"""
Test MongoDB Identity Collection and Indexes Setup
Task 1.1: MongoDB Identityコレクションとインデックスの作成
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.database import get_db_service
from src.services.identity_database_service import IdentityDatabaseService


class TestIdentityCollectionSetup:
    """Test Identity collection and indexes setup"""

    @pytest.fixture
    def identity_db_service(self):
        """Identity database service fixture with mocked database"""
        service = IdentityDatabaseService()

        # Mock the database service to avoid actual database connections
        mock_db_service = MagicMock()

        # Mock create_index to return proper index names
        def mock_create_index(collection, index_spec, **options):
            if options.get('name') == 'auth_method_1_email_hash_1':
                return "auth_method_1_email_hash_1"
            elif options.get('name') == 'email_usertype':
                return "email_usertype"
            else:
                return "generic_index_id"

        mock_db_service.create_index = AsyncMock(side_effect=mock_create_index)

        # Mock create to return unique IDs
        create_call_count = 0
        def mock_create(collection, document):
            nonlocal create_call_count
            create_call_count += 1
            return f"test_document_id_{create_call_count}"

        mock_db_service.create = AsyncMock(side_effect=mock_create)
        mock_db_service.find_one = AsyncMock(return_value=None)

        service.db_service = mock_db_service
        return service

    @pytest.mark.asyncio
    async def test_identity_collection_structure_validation(self, identity_db_service):
        """Test identity collection validates required fields"""
        # RED: テスト先行 - まだサービスが実装されていないので失敗する

        # 必須フィールドが欠けている無効なIdentityドキュメント
        invalid_identity = {
            "auth_method": "google",
            # email_encrypted missing
            # email_hash missing
            "user_type": "user"
        }

        with pytest.raises(ValueError, match="email_encrypted is required"):
            await identity_db_service.validate_identity_document(invalid_identity)

    @pytest.mark.asyncio
    async def test_create_unique_index_auth_method_email_hash(self, identity_db_service):
        """Test unique index creation for (auth_method, email_hash)"""
        # RED: テスト先行 - インデックス作成機能がまだ実装されていない

        result = await identity_db_service.create_unique_auth_email_index()

        assert result is not None
        assert "auth_method_1_email_hash_1" in result

    @pytest.mark.asyncio
    async def test_create_email_usertype_index(self, identity_db_service):
        """Test email_usertype index creation for (email_hash, user_type)"""
        # RED: テスト先行 - インデックス作成機能がまだ実装されていない

        result = await identity_db_service.create_email_usertype_index()

        assert result is not None
        assert "email_usertype" in result

    @pytest.mark.asyncio
    async def test_identity_document_constraints(self, identity_db_service):
        """Test identity document field constraints"""
        # RED: テスト先行 - バリデーション機能がまだ実装されていない

        # 有効なIdentityドキュメント
        valid_identity = {
            "auth_method": "google",
            "email_encrypted": "encrypted_email_string",
            "email_hash": "hashed_email_string",
            "email_masked": "ab***@**le.com",
            "user_type": "user",
            "provider_data": {
                "provider_id": "google_123",
                "name": "Test User"
            }
        }

        # バリデーションが成功することを確認
        result = await identity_db_service.validate_identity_document(valid_identity)
        assert result is True

    @pytest.mark.asyncio
    async def test_auth_method_enum_validation(self, identity_db_service):
        """Test auth_method field accepts only valid values"""
        # RED: テスト先行 - enum バリデーションがまだ実装されていない

        # 無効な認証方式
        invalid_identity = {
            "auth_method": "invalid_method",
            "email_encrypted": "encrypted_email_string",
            "email_hash": "hashed_email_string",
            "email_masked": "ab***@**le.com",
            "user_type": "user"
        }

        with pytest.raises(ValueError, match="auth_method must be one of"):
            await identity_db_service.validate_identity_document(invalid_identity)

    @pytest.mark.asyncio
    async def test_user_type_enum_validation(self, identity_db_service):
        """Test user_type field accepts only valid values"""
        # RED: テスト先行 - enum バリデーションがまだ実装されていない

        # 無効なユーザータイプ
        invalid_identity = {
            "auth_method": "google",
            "email_encrypted": "encrypted_email_string",
            "email_hash": "hashed_email_string",
            "email_masked": "ab***@**le.com",
            "user_type": "invalid_type"
        }

        with pytest.raises(ValueError, match="user_type must be one of"):
            await identity_db_service.validate_identity_document(invalid_identity)

    @pytest.mark.asyncio
    async def test_unique_constraint_enforcement(self, identity_db_service):
        """Test unique constraint enforcement for (auth_method, email_hash)"""
        # RED: テスト先行 - 一意制約の実装がまだされていない

        from pymongo.errors import DuplicateKeyError

        identity1 = {
            "auth_method": "google",
            "email_encrypted": "encrypted_email1",
            "email_hash": "same_hash",
            "email_masked": "test***@**le.com",
            "user_type": "user"
        }

        identity2 = {
            "auth_method": "google",
            "email_encrypted": "encrypted_email2",
            "email_hash": "same_hash",  # 同じハッシュ
            "email_masked": "test***@**le.com",
            "user_type": "admin"  # 異なるuser_type
        }

        # 最初の挿入は成功
        result1 = await identity_db_service.create_identity(identity1)
        assert result1 is not None

        # 2回目の挿入では DuplicateKeyError を発生させるようにモック
        identity_db_service.db_service.create.side_effect = DuplicateKeyError("E11000 duplicate key error")

        # 同じ(auth_method, email_hash)の組み合わせは失敗
        with pytest.raises(DuplicateKeyError):
            await identity_db_service.create_identity(identity2)

    @pytest.mark.asyncio
    async def test_different_auth_method_same_email_allowed(self, identity_db_service):
        """Test same email_hash with different auth_method is allowed"""
        # RED: テスト先行 - 複数認証方式対応がまだ実装されていない

        identity_google = {
            "auth_method": "google",
            "email_encrypted": "encrypted_email",
            "email_hash": "same_hash",
            "email_masked": "test***@**le.com",
            "user_type": "user"
        }

        identity_facebook = {
            "auth_method": "facebook",
            "email_encrypted": "encrypted_email",
            "email_hash": "same_hash",  # 同じハッシュ
            "email_masked": "test***@**le.com",
            "user_type": "user"
        }

        # 異なる認証方式では同じメールハッシュが許可される
        result1 = await identity_db_service.create_identity(identity_google)
        result2 = await identity_db_service.create_identity(identity_facebook)

        assert result1 is not None
        assert result2 is not None
        assert result1 != result2  # 異なるID