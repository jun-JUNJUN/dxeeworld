"""
CSVインポートサービスのテスト
"""
import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import AsyncMock, Mock
from src.services.csv_import_service import CSVImportService, ImportResult, ImportStatus


class TestCSVImportService:
    """CSVインポートサービスのテストクラス"""

    @pytest.fixture
    def mock_db_service(self):
        """モックデータベースサービス"""
        mock_db = AsyncMock()
        return mock_db

    @pytest.fixture
    def mock_company_service(self):
        """モック企業サービス"""
        mock_service = AsyncMock()
        return mock_service

    @pytest.fixture
    def csv_import_service(self, mock_db_service, mock_company_service):
        """CSVインポートサービスインスタンス"""
        return CSVImportService(mock_db_service, mock_company_service)

    @pytest.fixture
    def sample_foreign_companies_csv(self):
        """外資系企業CSVサンプルデータ"""
        data = {
            'Company Name': ['Apple Inc.', 'Google LLC', 'Microsoft Corp.'],
            'Industry': ['Technology', 'Technology', 'Technology'],
            'Region': ['North America', 'North America', 'North America'],
            'Country': ['USA', 'USA', 'USA'],
            'Market Cap (B)': [3000, 1800, 2500],
            'Employees': [150000, 140000, 200000]
        }

        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(data)
            df.to_csv(f.name, index=False)
            return f.name

    @pytest.fixture
    def sample_japan_construction_csv(self):
        """日本建設業CSVサンプルデータ"""
        data = {
            '会社名': ['大成建設', '清水建設', '竹中工務店'],
            '業種': ['建設業', '建設業', '建設業'],
            '所在地': ['東京都', '東京都', '大阪府'],
            'ライセンス種別': ['総合建設業', '総合建設業', '総合建設業'],
            'プロジェクト種類': ['マンション,オフィス', 'インフラ,住宅', 'オフィス,商業施設'],
            '年間売上(億円)': [1500, 1200, 800],
            '従業員数': [8500, 10000, 7500]
        }

        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            df = pd.DataFrame(data)
            df.to_csv(f.name, index=False)
            return f.name

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        # 一時ファイルを削除
        pass

    @pytest.mark.asyncio
    async def test_import_foreign_companies_csv_success(self, csv_import_service, sample_foreign_companies_csv):
        """外資系企業CSVの正常インポートテスト"""
        # Arrange
        csv_import_service.company_service.upsert_company_from_csv = AsyncMock(return_value=True)

        # Act
        result = await csv_import_service.import_foreign_companies_csv(sample_foreign_companies_csv)

        # Assert
        assert isinstance(result, ImportResult)
        assert result.status == ImportStatus.SUCCESS
        assert result.processed_count == 3
        assert result.error_count == 0
        assert len(result.errors) == 0

        # CSVファイルを削除
        os.unlink(sample_foreign_companies_csv)

    @pytest.mark.asyncio
    async def test_import_japan_construction_csv_success(self, csv_import_service, sample_japan_construction_csv):
        """日本建設業CSVの正常インポートテスト"""
        # Arrange
        csv_import_service.company_service.upsert_company_from_csv = AsyncMock(return_value=True)

        # Act
        result = await csv_import_service.import_japan_construction_csv(sample_japan_construction_csv)

        # Assert
        assert isinstance(result, ImportResult)
        assert result.status == ImportStatus.SUCCESS
        assert result.processed_count == 3
        assert result.error_count == 0
        assert len(result.errors) == 0

        # CSVファイルを削除
        os.unlink(sample_japan_construction_csv)

    @pytest.mark.asyncio
    async def test_import_csv_file_not_found(self, csv_import_service):
        """存在しないCSVファイルのインポートテスト"""
        # Act
        result = await csv_import_service.import_foreign_companies_csv('/nonexistent/file.csv')

        # Assert
        assert isinstance(result, ImportResult)
        assert result.status == ImportStatus.FAILED
        assert result.processed_count == 0
        assert result.error_count == 1
        assert len(result.errors) == 1
        assert 'not found' in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_merge_company_data_success(self, csv_import_service):
        """企業データマージの正常テスト"""
        # Arrange
        foreign_data = [
            {
                'name_normalized': 'apple',
                'name_original': 'Apple Inc.',
                'industry': 'technology',
                'foreign_company_data': {
                    'region': 'North America',
                    'country': 'USA',
                    'market_cap': 3000.0
                }
            }
        ]

        japan_data = [
            {
                'name_normalized': 'apple',
                'name_original': 'Apple Inc.',
                'industry': 'technology',
                'construction_data': {
                    'license_type': '',
                    'project_types': [],
                    'annual_revenue': 0.0
                }
            }
        ]

        # Act
        result = await csv_import_service.merge_company_data(foreign_data, japan_data)

        # Assert
        assert len(result) == 1
        merged_company = result[0]
        assert merged_company['name_normalized'] == 'apple'
        assert 'foreign_company_data' in merged_company
        assert 'construction_data' in merged_company

    @pytest.mark.asyncio
    async def test_normalize_company_name(self, csv_import_service):
        """企業名正規化テスト"""
        # Act & Assert
        assert csv_import_service.normalize_company_name('Apple Inc.') == 'apple'
        assert csv_import_service.normalize_company_name('  Google LLC  ') == 'google'
        assert csv_import_service.normalize_company_name('株式会社東芝') == '株式会社東芝'
        assert csv_import_service.normalize_company_name('Microsoft Corporation') == 'microsoft'

    @pytest.mark.asyncio
    async def test_clean_csv_data_foreign_companies(self, csv_import_service):
        """外資系企業CSVデータクリーニングテスト"""
        # Arrange
        raw_data = pd.DataFrame({
            'Company Name': ['Apple Inc.', '', 'Google'],
            'Industry': ['Technology', 'Unknown', 'Technology'],
            'Region': ['North America', '', 'North America'],
            'Market Cap (B)': [3000, None, 1800],
            'Employees': [150000, 0, 140000]
        })

        # Act
        cleaned_data = csv_import_service.clean_foreign_companies_data(raw_data)

        # Assert
        assert len(cleaned_data) == 2  # 空の企業名は除外
        assert all('name_normalized' in item for item in cleaned_data)
        assert all('foreign_company_data' in item for item in cleaned_data)

    @pytest.mark.asyncio
    async def test_partial_import_with_errors(self, csv_import_service, sample_foreign_companies_csv):
        """一部エラーありの部分インポートテスト"""
        # Arrange
        call_count = 0

        async def mock_upsert(data):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # 2番目のレコードでエラー
                raise Exception("Database error")
            return True

        csv_import_service.company_service.upsert_company_from_csv = mock_upsert

        # Act
        result = await csv_import_service.import_foreign_companies_csv(sample_foreign_companies_csv)

        # Assert
        assert isinstance(result, ImportResult)
        assert result.status == ImportStatus.PARTIAL
        assert result.processed_count == 2
        assert result.error_count == 1
        assert len(result.errors) == 1

        # CSVファイルを削除
        os.unlink(sample_foreign_companies_csv)