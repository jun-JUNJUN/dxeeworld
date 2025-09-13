"""
ユーザーサービスの拡張機能テスト
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from bson import ObjectId
from src.services.user_service import UserService, ValidationError, AuthenticationError
from src.models.user import User, UserType
from src.utils.result import Result


class TestUserServiceProfile:
    """ユーザープロファイル管理テスト"""

    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        """ユーザープロファイル取得テスト"""
        user_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.find_one.return_value = {
            '_id': user_id,
            'email': 'test@example.com',
            'name': 'Test User',
            'user_type': 'individual',
            'password_hash': 'hashed_password',
            'company_id': None,
            'position': None,
            'profile': {
                'bio': 'Software developer',
                'skills': ['Python', 'JavaScript'],
                'experience_years': 5,
                'location': 'Tokyo, Japan',
                'linkedin_url': 'https://linkedin.com/in/testuser',
                'github_url': 'https://github.com/testuser',
                'portfolio_url': 'https://testuser.dev'
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }

        service = UserService(mock_db)

        profile = await service.get_user_profile(user_id)
        assert profile is not None
        assert profile['bio'] == 'Software developer'
        assert 'Python' in profile['skills']

    @pytest.mark.asyncio
    async def test_update_user_profile(self):
        """ユーザープロファイル更新テスト"""
        user_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.find_one.return_value = {
            '_id': user_id,
            'email': 'test@example.com',
            'name': 'Test User',
            'profile': {}
        }
        mock_db.update_one.return_value = True

        service = UserService(mock_db)

        profile_data = {
            'bio': 'Updated bio',
            'skills': ['Python', 'JavaScript', 'React'],
            'experience_years': 6,
            'location': 'Osaka, Japan'
        }

        result = await service.update_user_profile(user_id, profile_data)
        assert result.is_success
        mock_db.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_profile_data(self):
        """プロファイルデータのバリデーション"""
        service = UserService()

        # 有効なプロファイルデータ
        valid_profile = {
            'bio': 'Software developer with 5 years experience',
            'skills': ['Python', 'JavaScript'],
            'experience_years': 5,
            'location': 'Tokyo, Japan',
            'linkedin_url': 'https://linkedin.com/in/user',
            'github_url': 'https://github.com/user',
            'portfolio_url': 'https://user.dev'
        }

        result = service.validate_profile_data(valid_profile)
        assert result.is_success

        # 無効なプロファイルデータ
        invalid_profile = {
            'bio': 'x' * 600,  # 長すぎるバイオ
            'skills': [''],  # 空文字列を含むスキルリスト
            'experience_years': -1,  # 負の経験年数
            'linkedin_url': 'invalid-url'  # 無効なURL
        }

        result = service.validate_profile_data(invalid_profile)
        assert not result.is_success
        assert 'bio' in result.error.field_errors
        assert 'skills' in result.error.field_errors
        assert 'experience_years' in result.error.field_errors
        assert 'linkedin_url' in result.error.field_errors


class TestUserServiceSearch:
    """ユーザー検索機能テスト"""

    @pytest.mark.asyncio
    async def test_search_users_by_skills(self):
        """スキルによるユーザー検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'email': 'user1@example.com',
                'name': 'User 1',
                'user_type': 'individual',
                'profile': {
                    'skills': ['Python', 'JavaScript']
                }
            },
            {
                '_id': str(ObjectId()),
                'email': 'user2@example.com',
                'name': 'User 2',
                'user_type': 'individual',
                'profile': {
                    'skills': ['Python', 'React']
                }
            }
        ]

        service = UserService(mock_db)

        users = await service.search_users_by_skills(['Python'], limit=10)
        assert len(users) == 2
        mock_db.find_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_users_by_location(self):
        """地域によるユーザー検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'email': 'user1@example.com',
                'name': 'Tokyo User',
                'user_type': 'individual',
                'profile': {
                    'location': 'Tokyo, Japan'
                }
            }
        ]

        service = UserService(mock_db)

        users = await service.search_users_by_location('Tokyo', limit=10)
        assert len(users) == 1
        assert users[0]['name'] == 'Tokyo User'

    @pytest.mark.asyncio
    async def test_search_users_by_experience(self):
        """経験年数によるユーザー検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'email': 'senior@example.com',
                'name': 'Senior Dev',
                'user_type': 'individual',
                'profile': {
                    'experience_years': 8
                }
            }
        ]

        service = UserService(mock_db)

        users = await service.search_users_by_experience(min_years=5, max_years=10)
        assert len(users) == 1
        assert users[0]['name'] == 'Senior Dev'


class TestUserServiceCompanyManagement:
    """企業関連ユーザー管理テスト"""

    @pytest.mark.asyncio
    async def test_get_company_members(self):
        """企業メンバー取得テスト"""
        company_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'email': 'employee1@company.com',
                'name': 'Employee 1',
                'user_type': 'company',
                'company_id': company_id,
                'position': 'Developer'
            },
            {
                '_id': str(ObjectId()),
                'email': 'employee2@company.com',
                'name': 'Employee 2',
                'user_type': 'company',
                'company_id': company_id,
                'position': 'Designer'
            }
        ]

        service = UserService(mock_db)

        members = await service.get_company_members(company_id)
        assert len(members) == 2
        assert all(member['company_id'] == company_id for member in members)

    @pytest.mark.asyncio
    async def test_update_user_company_info(self):
        """ユーザーの企業情報更新テスト"""
        user_id = str(ObjectId())
        company_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.find_one.return_value = {
            '_id': user_id,
            'email': 'user@example.com',
            'name': 'Test User',
            'user_type': 'company'
        }
        mock_db.update_one.return_value = True

        service = UserService(mock_db)

        result = await service.update_user_company_info(
            user_id,
            company_id,
            'Senior Developer'
        )
        assert result.is_success
        mock_db.update_one.assert_called_once()


class TestUserServiceBulkOperations:
    """ユーザー一括操作テスト"""

    @pytest.mark.asyncio
    async def test_bulk_create_users(self):
        """複数ユーザーの一括作成テスト"""
        mock_db = AsyncMock()
        mock_db.find_one.return_value = None  # 重複なし
        mock_db.bulk_insert.return_value = ['id1', 'id2', 'id3']

        service = UserService(mock_db)

        users_data = [
            {
                'email': 'user1@example.com',
                'password': 'password123!',
                'name': 'User 1',
                'user_type': 'individual'
            },
            {
                'email': 'user2@example.com',
                'password': 'password123!',
                'name': 'User 2',
                'user_type': 'company'
            },
            {
                'email': 'user3@example.com',
                'password': 'password123!',
                'name': 'User 3',
                'user_type': 'individual'
            }
        ]

        result = await service.bulk_create_users(users_data)
        assert result.is_success
        assert len(result.data) == 3

    @pytest.mark.asyncio
    async def test_bulk_update_user_status(self):
        """複数ユーザーの状態一括更新テスト"""
        mock_db = AsyncMock()
        mock_db.bulk_update.return_value = 2

        service = UserService(mock_db)

        user_ids = ['id1', 'id2']
        result = await service.bulk_update_user_status(user_ids, is_active=False)
        assert result == 2


class TestUserServiceIndexing:
    """ユーザー検索インデックス機能テスト"""

    @pytest.mark.asyncio
    async def test_create_user_indexes(self):
        """ユーザーコレクションのインデックス作成テスト"""
        mock_db = AsyncMock()
        mock_db.create_index.return_value = "index_name"

        service = UserService(mock_db)

        result = await service.create_user_indexes()
        assert result is True

        # インデックス作成が複数回呼ばれることを確認
        assert mock_db.create_index.call_count >= 3

    @pytest.mark.asyncio
    async def test_search_users_by_text(self):
        """テキスト検索によるユーザー検索テスト"""
        mock_db = AsyncMock()
        mock_db.aggregate.return_value = [
            {
                '_id': str(ObjectId()),
                'email': 'developer@example.com',
                'name': 'Full Stack Developer',
                'user_type': 'individual',
                'profile': {
                    'bio': 'Full stack web developer',
                    'skills': ['JavaScript', 'Python']
                },
                'score': 2.5
            }
        ]

        service = UserService(mock_db)

        users = await service.search_users_by_text('full stack developer')
        assert len(users) == 1
        assert users[0]['name'] == 'Full Stack Developer'