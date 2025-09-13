"""
企業サービス機能テスト
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from bson import ObjectId
from src.services.company_service import CompanyService, ValidationError
from src.models.company import Company, IndustryType, CompanySize
from src.utils.result import Result


class TestCompanyServiceValidation:
    """企業データのバリデーションテスト"""

    def test_valid_company_data(self):
        """有効な企業データの検証"""
        service = CompanyService()

        valid_data = {
            'name': 'Tech Startup Inc.',
            'industry': 'technology',
            'size': 'startup',
            'description': 'Innovative tech company',
            'website': 'https://techstartup.com',
            'location': 'Tokyo, Japan',
            'founded_year': 2020,
            'employee_count': 50
        }

        result = service.validate_company_data(valid_data)
        assert result.is_success
        assert result.data is True

    def test_missing_required_fields(self):
        """必須フィールド不足のバリデーション"""
        service = CompanyService()

        invalid_data = {
            'name': '',  # 空の企業名
            'industry': 'invalid_industry',  # 無効な業界
            'size': 'invalid_size'  # 無効なサイズ
        }

        result = service.validate_company_data(invalid_data)
        assert not result.is_success
        assert isinstance(result.error, ValidationError)
        assert 'name' in result.error.field_errors
        assert 'industry' in result.error.field_errors
        assert 'size' in result.error.field_errors

    def test_invalid_website_url(self):
        """無効なウェブサイトURLのバリデーション"""
        service = CompanyService()

        invalid_data = {
            'name': 'Valid Company',
            'industry': 'technology',
            'size': 'startup',
            'website': 'invalid-url'
        }

        result = service.validate_company_data(invalid_data)
        assert not result.is_success
        assert 'website' in result.error.field_errors

    def test_invalid_founded_year(self):
        """無効な設立年のバリデーション"""
        service = CompanyService()

        invalid_data = {
            'name': 'Valid Company',
            'industry': 'technology',
            'size': 'startup',
            'founded_year': 1500  # 範囲外の年
        }

        result = service.validate_company_data(invalid_data)
        assert not result.is_success
        assert 'founded_year' in result.error.field_errors


class TestCompanyServiceCRUD:
    """企業サービスCRUD操作テスト"""

    @pytest.mark.asyncio
    async def test_create_company_success(self):
        """企業作成成功テスト"""
        mock_db = AsyncMock()
        mock_db.find_one.return_value = None  # 重複なし
        mock_db.create.return_value = str(ObjectId())

        service = CompanyService(mock_db)

        company_data = {
            'name': 'New Tech Company',
            'industry': 'technology',
            'size': 'startup',
            'description': 'Innovative startup',
            'location': 'Tokyo'
        }

        result = await service.create_company(company_data)
        assert result.is_success
        assert isinstance(result.data, Company)
        assert result.data.name == 'New Tech Company'

    @pytest.mark.asyncio
    async def test_create_company_duplicate_name(self):
        """企業名重複エラーテスト"""
        mock_db = AsyncMock()
        mock_db.find_one.return_value = {'name': 'Existing Company'}

        service = CompanyService(mock_db)

        company_data = {
            'name': 'Existing Company',
            'industry': 'technology',
            'size': 'startup'
        }

        result = await service.create_company(company_data)
        assert not result.is_success
        assert 'name' in result.error.field_errors

    @pytest.mark.asyncio
    async def test_get_company_by_id(self):
        """ID による企業取得テスト"""
        company_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.find_one.return_value = {
            '_id': company_id,
            'name': 'Test Company',
            'industry': 'technology',
            'size': 'startup',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        service = CompanyService(mock_db)

        company = await service.get_company(company_id)
        assert company is not None
        assert company.name == 'Test Company'

    @pytest.mark.asyncio
    async def test_search_companies_with_filters(self):
        """フィルター付き企業検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'name': 'Tech Company 1',
                'industry': 'technology',
                'size': 'startup',
                'location': 'Tokyo',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                '_id': str(ObjectId()),
                'name': 'Tech Company 2',
                'industry': 'technology',
                'size': 'small',
                'location': 'Osaka',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]

        service = CompanyService(mock_db)

        companies = await service.search_companies(
            industry='technology',
            location='Tokyo',
            limit=10
        )

        assert len(companies) == 2
        mock_db.find_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_company_success(self):
        """企業更新成功テスト"""
        company_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.find_one.return_value = None  # 重複なし
        mock_db.update_one.return_value = True

        # 更新後の企業データをモック
        updated_company_doc = {
            '_id': company_id,
            'name': 'Updated Company',
            'industry': 'technology',
            'size': 'startup',
            'description': 'Updated description',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        mock_db.find_one.side_effect = [None, updated_company_doc]

        service = CompanyService(mock_db)

        update_data = {
            'name': 'Updated Company',
            'industry': 'technology',
            'size': 'startup',
            'description': 'Updated description'
        }

        result = await service.update_company(company_id, update_data)
        assert result.is_success
        assert result.data.name == 'Updated Company'

    @pytest.mark.asyncio
    async def test_delete_company(self):
        """企業削除テスト"""
        company_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.update_one.return_value = True

        service = CompanyService(mock_db)

        result = await service.delete_company(company_id)
        assert result is True


class TestCompanyServiceIndexing:
    """企業検索インデックス機能テスト"""

    @pytest.mark.asyncio
    async def test_create_company_indexes(self):
        """企業コレクションのインデックス作成テスト"""
        mock_db = AsyncMock()
        mock_db.create_index.return_value = "index_name"

        service = CompanyService(mock_db)

        # 企業名の一意インデックス作成
        result = await service.create_company_indexes()
        assert result is True

        # インデックス作成が複数回呼ばれることを確認
        assert mock_db.create_index.call_count >= 2

    @pytest.mark.asyncio
    async def test_search_companies_by_text(self):
        """テキスト検索による企業検索テスト"""
        mock_db = AsyncMock()
        mock_db.aggregate.return_value = [
            {
                '_id': str(ObjectId()),
                'name': 'Software Development Inc.',
                'industry': 'technology',
                'size': 'medium',
                'description': 'Software development and consulting',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'score': 2.5
            }
        ]

        service = CompanyService(mock_db)

        companies = await service.search_companies_by_text('software development')
        assert len(companies) == 1
        assert companies[0].name == 'Software Development Inc.'


class TestCompanyServiceBulkOperations:
    """企業サービス一括操作テスト"""

    @pytest.mark.asyncio
    async def test_bulk_create_companies(self):
        """複数企業の一括作成テスト"""
        mock_db = AsyncMock()
        mock_db.find_one.return_value = None  # 重複なし
        mock_db.bulk_insert.return_value = ['id1', 'id2', 'id3']

        service = CompanyService(mock_db)

        companies_data = [
            {
                'name': 'Company 1',
                'industry': 'technology',
                'size': 'startup'
            },
            {
                'name': 'Company 2',
                'industry': 'finance',
                'size': 'medium'
            },
            {
                'name': 'Company 3',
                'industry': 'healthcare',
                'size': 'large'
            }
        ]

        result = await service.bulk_create_companies(companies_data)
        assert result.is_success
        assert len(result.data) == 3

    @pytest.mark.asyncio
    async def test_bulk_update_companies(self):
        """複数企業の一括更新テスト"""
        mock_db = AsyncMock()
        mock_db.bulk_update.return_value = 2

        service = CompanyService(mock_db)

        updates = [
            {
                'company_id': 'id1',
                'update_data': {'status': 'active'}
            },
            {
                'company_id': 'id2',
                'update_data': {'status': 'inactive'}
            }
        ]

        result = await service.bulk_update_companies(updates)
        assert result == 2