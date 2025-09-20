"""
企業データベース機能のテスト
"""
import pytest
from unittest.mock import AsyncMock, Mock
from src.services.company_service import CompanyService
from src.models.company import Company, IndustryType, CompanySize


class TestCompanyDatabase:
    """企業データベース機能のテストクラス"""

    @pytest.fixture
    def mock_db_service(self):
        """モックデータベースサービス"""
        mock_db = AsyncMock()
        return mock_db

    @pytest.fixture
    def company_service(self, mock_db_service):
        """企業サービスインスタンス"""
        return CompanyService(mock_db_service)

    @pytest.mark.asyncio
    async def test_create_company_indexes_success(self, company_service):
        """企業コレクションインデックス作成の正常テスト"""
        # Arrange
        company_service.db_service.create_index = AsyncMock(return_value=True)

        # Act
        result = await company_service.create_company_indexes()

        # Assert
        assert result is True
        # 複数のインデックスが作成されることを確認
        assert company_service.db_service.create_index.call_count >= 5

    @pytest.mark.asyncio
    async def test_upsert_company_from_csv_new_company(self, company_service):
        """CSVデータから新規企業作成テスト"""
        # Arrange
        csv_data = {
            'name_normalized': 'apple',
            'name_original': 'Apple Inc.',
            'industry': 'technology',
            'size': 'enterprise',
            'country': 'United States',
            'location': 'California, USA',
            'foreign_company_data': {
                'region': 'North America',
                'country': 'USA',
                'market_cap': 3000.0,
                'employee_count': 150000
            },
            'construction_data': {},
            'source_files': ['foreign_companies.csv']
        }

        company_service.db_service.find_one = AsyncMock(return_value=None)
        company_service.db_service.create = AsyncMock(return_value='company_id_123')

        # Act
        result = await company_service.upsert_company_from_csv(csv_data)

        # Assert
        assert result.is_success
        company = result.data
        assert isinstance(company, Company)
        assert company.name == 'apple'
        assert company.industry == IndustryType.TECHNOLOGY
        assert company.size == CompanySize.ENTERPRISE

    @pytest.mark.asyncio
    async def test_upsert_company_from_csv_update_existing(self, company_service):
        """CSVデータから既存企業更新テスト"""
        # Arrange
        existing_company = {
            '_id': 'existing_id',
            'name': 'apple',
            'industry': 'technology',
            'size': 'large',
            'created_at': '2023-01-01T00:00:00Z',
            'foreign_company_data': {
                'region': 'North America',
                'country': 'USA',
                'market_cap': 2800.0
            },
            'construction_data': {},
            'source_files': ['old_file.csv']
        }

        csv_data = {
            'name_normalized': 'apple',
            'name_original': 'Apple Inc.',
            'industry': 'technology',
            'size': 'enterprise',
            'country': 'United States',
            'foreign_company_data': {
                'region': 'North America',
                'country': 'USA',
                'market_cap': 3000.0,
                'employee_count': 150000
            },
            'construction_data': {},
            'source_files': ['foreign_companies.csv']
        }

        company_service.db_service.find_one = AsyncMock(return_value=existing_company)
        company_service.db_service.update_one = AsyncMock(return_value=True)
        company_service.get_company = AsyncMock(return_value=Company(
            id='existing_id',
            name='apple',
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.ENTERPRISE,
            country='United States'
        ))

        # Act
        result = await company_service.upsert_company_from_csv(csv_data)

        # Assert
        assert result.is_success
        company = result.data
        assert company.size == CompanySize.ENTERPRISE

        # 更新が呼ばれたことを確認
        company_service.db_service.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_max_employee_count(self, company_service):
        """従業員数最大値取得テスト"""
        # Test case 1: 外資系データが大きい場合
        csv_data1 = {
            'foreign_company_data': {'employee_count': 150000},
            'construction_data': {'employee_count': 5000}
        }
        result1 = company_service._get_max_employee_count(csv_data1)
        assert result1 == 150000

        # Test case 2: 建設業データが大きい場合
        csv_data2 = {
            'foreign_company_data': {'employee_count': 1000},
            'construction_data': {'employee_count': 8000}
        }
        result2 = company_service._get_max_employee_count(csv_data2)
        assert result2 == 8000

        # Test case 3: どちらもゼロの場合
        csv_data3 = {
            'foreign_company_data': {'employee_count': 0},
            'construction_data': {'employee_count': 0}
        }
        result3 = company_service._get_max_employee_count(csv_data3)
        assert result3 is None

        # Test case 4: データが不完全な場合
        csv_data4 = {
            'foreign_company_data': {},
            'construction_data': {}
        }
        result4 = company_service._get_max_employee_count(csv_data4)
        assert result4 is None

    @pytest.mark.asyncio
    async def test_data_integrity_check(self, company_service):
        """データ整合性チェックテスト"""
        # Arrange
        csv_data = {
            'name_normalized': '',  # 空の企業名（不正）
            'name_original': 'Apple Inc.',
            'industry': 'invalid_industry',  # 不正な業界
            'size': 'invalid_size'  # 不正なサイズ
        }

        # Act & Assert
        # バリデーションエラーが発生することを期待
        result = await company_service.upsert_company_from_csv(csv_data)
        assert not result.is_success

    @pytest.mark.asyncio
    async def test_source_files_tracking(self, company_service):
        """データソースファイル追跡テスト"""
        # Arrange
        existing_company = {
            '_id': 'existing_id',
            'name': 'apple',
            'source_files': ['file1.csv'],
            'foreign_company_data': {},
            'construction_data': {},
            'created_at': '2023-01-01T00:00:00Z'
        }

        csv_data = {
            'name_normalized': 'apple',
            'name_original': 'Apple Inc.',
            'industry': 'technology',
            'size': 'enterprise',
            'country': 'United States',
            'source_files': ['file2.csv'],
            'foreign_company_data': {},
            'construction_data': {}
        }

        company_service.db_service.find_one = AsyncMock(return_value=existing_company)
        company_service.db_service.update_one = AsyncMock(return_value=True)
        company_service.get_company = AsyncMock(return_value=Company(
            id='existing_id',
            name='apple',
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.ENTERPRISE,
            country='United States'
        ))

        # Act
        result = await company_service.upsert_company_from_csv(csv_data)

        # Assert
        assert result.is_success

        # 更新呼び出し時の引数を確認
        call_args = company_service.db_service.update_one.call_args
        update_doc = call_args[0][2]  # 3番目の引数（更新ドキュメント）

        # ソースファイルが統合されていることを確認
        assert set(update_doc['source_files']) == {'file1.csv', 'file2.csv'}

    @pytest.mark.asyncio
    async def test_company_data_merge(self, company_service):
        """企業データマージテスト"""
        # Arrange
        existing_company = {
            '_id': 'existing_id',
            'name': 'apple',
            'foreign_company_data': {
                'region': 'North America',
                'market_cap': 2800.0
            },
            'construction_data': {
                'license_type': 'General'
            },
            'created_at': '2023-01-01T00:00:00Z'
        }

        csv_data = {
            'name_normalized': 'apple',
            'name_original': 'Apple Inc.',
            'industry': 'technology',
            'size': 'enterprise',
            'country': 'United States',
            'foreign_company_data': {
                'country': 'USA',
                'market_cap': 3000.0  # 上書き
            },
            'construction_data': {
                'project_types': ['Office', 'Residential']  # 追加
            }
        }

        company_service.db_service.find_one = AsyncMock(return_value=existing_company)
        company_service.db_service.update_one = AsyncMock(return_value=True)
        company_service.get_company = AsyncMock(return_value=Company(
            id='existing_id',
            name='apple',
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.ENTERPRISE,
            country='United States'
        ))

        # Act
        result = await company_service.upsert_company_from_csv(csv_data)

        # Assert
        assert result.is_success

        # マージされたデータの確認
        call_args = company_service.db_service.update_one.call_args
        update_doc = call_args[0][2]

        # 外資系データのマージ確認
        foreign_data = update_doc['foreign_company_data']
        assert foreign_data['region'] == 'North America'  # 既存データ保持
        assert foreign_data['country'] == 'USA'  # 新規データ追加
        assert foreign_data['market_cap'] == 3000.0  # 新規データで上書き

        # 建設業データのマージ確認
        construction_data = update_doc['construction_data']
        assert construction_data['license_type'] == 'General'  # 既存データ保持
        assert construction_data['project_types'] == ['Office', 'Residential']  # 新規データ追加