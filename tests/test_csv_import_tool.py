"""
CSVインポート実行ツールのテスト
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, Mock, patch
from src.tools.csv_import_tool import CSVImportTool
from src.services.csv_import_service import ImportStatus


class TestCSVImportTool:
    """CSVインポート実行ツールのテストクラス"""

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
    def mock_csv_import_service(self):
        """モックCSVインポートサービス"""
        mock_service = AsyncMock()
        return mock_service

    @pytest.fixture
    def csv_import_tool(self, mock_db_service, mock_company_service, mock_csv_import_service):
        """CSVインポートツールインスタンス"""
        return CSVImportTool(mock_db_service, mock_company_service, mock_csv_import_service)

    @pytest.mark.asyncio
    async def test_import_csv_files_success(self, csv_import_tool, mock_csv_import_service):
        """CSVファイル正常インポートテスト"""
        # Arrange
        foreign_csv_path = "foreign_companies.csv"
        japan_csv_path = "japan_construction.csv"

        # モックのレスポンス設定
        from src.services.csv_import_service import ImportResult
        mock_foreign_result = ImportResult(
            status=ImportStatus.SUCCESS,
            processed_count=200,
            error_count=0,
            errors=[]
        )
        mock_japan_result = ImportResult(
            status=ImportStatus.SUCCESS,
            processed_count=421,
            error_count=0,
            errors=[]
        )

        mock_csv_import_service.import_foreign_companies_csv.return_value = mock_foreign_result
        mock_csv_import_service.import_japan_construction_csv.return_value = mock_japan_result

        # Act
        result = await csv_import_tool.import_csv_files(foreign_csv_path, japan_csv_path)

        # Assert
        assert result.is_success
        assert result.total_processed == 621
        assert result.total_errors == 0
        mock_csv_import_service.import_foreign_companies_csv.assert_called_once_with(foreign_csv_path)
        mock_csv_import_service.import_japan_construction_csv.assert_called_once_with(japan_csv_path)

    @pytest.mark.asyncio
    async def test_import_csv_files_with_errors(self, csv_import_tool, mock_csv_import_service):
        """エラーありCSVインポートテスト"""
        # Arrange
        foreign_csv_path = "foreign_companies.csv"
        japan_csv_path = "japan_construction.csv"

        # モックのレスポンス設定（エラーあり）
        from src.services.csv_import_service import ImportResult
        mock_foreign_result = ImportResult(
            status=ImportStatus.PARTIAL,
            processed_count=180,
            error_count=20,
            errors=["Invalid industry data", "Missing country field"]
        )
        mock_japan_result = ImportResult(
            status=ImportStatus.SUCCESS,
            processed_count=421,
            error_count=0,
            errors=[]
        )

        mock_csv_import_service.import_foreign_companies_csv.return_value = mock_foreign_result
        mock_csv_import_service.import_japan_construction_csv.return_value = mock_japan_result

        # Act
        result = await csv_import_tool.import_csv_files(foreign_csv_path, japan_csv_path)

        # Assert
        assert result.is_success  # 部分的成功でも全体は成功
        assert result.total_processed == 601
        assert result.total_errors == 20
        assert len(result.errors) == 2

    @pytest.mark.asyncio
    async def test_validate_csv_files_exist(self, csv_import_tool):
        """CSVファイル存在確認テスト"""
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Company,Industry\nApple,Technology")
            temp_path = temp_file.name

        try:
            # Act & Assert - 存在するファイル
            assert csv_import_tool.validate_csv_file_exists(temp_path) is True

            # Act & Assert - 存在しないファイル
            assert csv_import_tool.validate_csv_file_exists("nonexistent.csv") is False

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_database_connection_handling(self, csv_import_tool, mock_db_service):
        """データベース接続処理テスト"""
        # Arrange
        mock_db_service.connect.return_value = None
        mock_db_service.disconnect.return_value = None

        # Act
        async with csv_import_tool.database_connection():
            pass

        # Assert
        mock_db_service.connect.assert_called_once()
        mock_db_service.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self, csv_import_tool, mock_db_service):
        """データベース接続エラー処理テスト"""
        # Arrange
        mock_db_service.connect.side_effect = Exception("Connection failed")

        # Act & Assert
        with pytest.raises(Exception, match="Connection failed"):
            async with csv_import_tool.database_connection():
                pass

    @pytest.mark.asyncio
    async def test_generate_import_statistics(self, csv_import_tool, mock_company_service):
        """インポート統計情報生成テスト"""
        # Arrange
        mock_stats = {
            'total_companies': 621,
            'active_companies': 621,
            'inactive_companies': 0,
            'industry_distribution': {'technology': 420, 'finance': 201},
            'size_distribution': {'medium': 421, 'enterprise': 200},
            'source_file_distribution': {'foreign_companies.csv': 200, 'japan_construction.csv': 421}
        }
        mock_company_service.get_import_statistics.return_value = mock_stats

        # Act
        stats = await csv_import_tool.generate_import_statistics()

        # Assert
        assert stats['total_companies'] == 621
        assert stats['industry_distribution']['technology'] == 420
        mock_company_service.get_import_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_line_argument_parsing(self):
        """コマンドライン引数解析テスト"""
        # Arrange
        from src.tools.csv_import_tool import parse_arguments
        test_args = [
            "--foreign-csv", "foreign.csv",
            "--japan-csv", "japan.csv",
            "--verbose"
        ]

        # Act
        args = parse_arguments(test_args)

        # Assert
        assert args.foreign_csv == "foreign.csv"
        assert args.japan_csv == "japan.csv"
        assert args.verbose is True

    @pytest.mark.asyncio
    async def test_detailed_logging_output(self, csv_import_tool, caplog):
        """詳細ログ出力テスト"""
        # Arrange
        csv_import_tool.enable_verbose_logging()

        # Act
        csv_import_tool.log_import_start("test.csv")
        csv_import_tool.log_import_completion(100, 5, ["error1", "error2"])

        # Assert
        assert "Starting CSV import: test.csv" in caplog.text
        assert "Import completed: 100 processed, 5 errors" in caplog.text

    @pytest.mark.asyncio
    async def test_data_integrity_check(self, csv_import_tool, mock_company_service):
        """データ整合性チェックテスト"""
        # Arrange
        mock_company_service.validate_data_integrity.return_value = {
            'is_valid': True,
            'validation_errors': [],
            'missing_required_fields': 0,
            'duplicate_entries': 0
        }

        # Act
        integrity_result = await csv_import_tool.check_data_integrity()

        # Assert
        assert integrity_result['is_valid'] is True
        assert integrity_result['validation_errors'] == []
        mock_company_service.validate_data_integrity.assert_called_once()