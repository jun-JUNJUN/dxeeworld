"""
CSVインポート実行ツール
"""
import os
import logging
import argparse
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.services.csv_import_service import CSVImportService, ImportResult, ImportStatus
from src.services.company_service import CompanyService
from src.database import DatabaseService


@dataclass
class ImportToolResult:
    """インポートツール実行結果"""
    is_success: bool
    total_processed: int
    total_errors: int
    errors: List[str]
    execution_time: float
    foreign_result: Optional[ImportResult] = None
    japan_result: Optional[ImportResult] = None


class CSVImportTool:
    """CSVインポート実行ツール"""

    def __init__(self, db_service: DatabaseService, company_service: CompanyService, csv_import_service: CSVImportService):
        self.db_service = db_service
        self.company_service = company_service
        self.csv_import_service = csv_import_service
        self.logger = logging.getLogger(__name__)
        self.verbose = False

    def enable_verbose_logging(self):
        """詳細ログ出力を有効化"""
        self.verbose = True
        logging.getLogger().setLevel(logging.DEBUG)

    def validate_csv_file_exists(self, file_path: str) -> bool:
        """CSVファイルの存在確認"""
        return os.path.exists(file_path) and os.path.isfile(file_path)

    @asynccontextmanager
    async def database_connection(self):
        """データベース接続コンテキストマネージャー"""
        try:
            await self.db_service.connect()
            self.logger.info("Database connection established")
            yield
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
        finally:
            await self.db_service.disconnect()
            self.logger.info("Database connection closed")

    async def import_csv_files(self, foreign_csv_path: str, japan_csv_path: str) -> ImportToolResult:
        """CSVファイルのインポート実行"""
        start_time = datetime.now()
        all_errors = []

        try:
            # 外資系企業CSVインポート
            self.log_import_start(foreign_csv_path)
            foreign_result = await self.csv_import_service.import_foreign_companies_csv(foreign_csv_path)
            all_errors.extend(foreign_result.errors)

            # 日本建設業CSVインポート
            self.log_import_start(japan_csv_path)
            japan_result = await self.csv_import_service.import_japan_construction_csv(japan_csv_path)
            all_errors.extend(japan_result.errors)

            # 結果集計
            total_processed = foreign_result.processed_count + japan_result.processed_count
            total_errors = foreign_result.error_count + japan_result.error_count

            execution_time = (datetime.now() - start_time).total_seconds()

            # 成功判定（部分的成功も含む）
            is_success = (
                foreign_result.status != ImportStatus.FAILED and
                japan_result.status != ImportStatus.FAILED
            )

            self.log_import_completion(total_processed, total_errors, all_errors[:5])

            return ImportToolResult(
                is_success=is_success,
                total_processed=total_processed,
                total_errors=total_errors,
                errors=all_errors,
                execution_time=execution_time,
                foreign_result=foreign_result,
                japan_result=japan_result
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Import failed with exception: {e}")
            return ImportToolResult(
                is_success=False,
                total_processed=0,
                total_errors=1,
                errors=[str(e)],
                execution_time=execution_time
            )

    def log_import_start(self, file_path: str):
        """インポート開始ログ"""
        message = f"Starting CSV import: {file_path}"
        if self.verbose:
            self.logger.info(message)
        print(message)

    def log_import_completion(self, processed: int, errors: int, error_samples: List[str]):
        """インポート完了ログ"""
        message = f"Import completed: {processed} processed, {errors} errors"
        if self.verbose:
            self.logger.info(message)
            if error_samples:
                self.logger.warning(f"Error samples: {error_samples}")
        print(message)

    async def generate_import_statistics(self) -> Dict[str, Any]:
        """インポート統計情報の生成"""
        return await self.company_service.get_import_statistics()

    async def check_data_integrity(self) -> Dict[str, Any]:
        """データ整合性チェック"""
        return await self.company_service.validate_data_integrity()


def parse_arguments(args: List[str] = None) -> argparse.Namespace:
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="CSV Import Tool for Company Data")

    parser.add_argument(
        "--foreign-csv",
        required=True,
        help="Path to foreign companies CSV file"
    )

    parser.add_argument(
        "--japan-csv",
        required=True,
        help="Path to Japan construction companies CSV file"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--check-integrity",
        action="store_true",
        help="Run data integrity check after import"
    )

    return parser.parse_args(args)


async def main():
    """メイン実行関数"""
    # 引数解析
    args = parse_arguments()

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # サービス初期化
    db_service = DatabaseService()
    company_service = CompanyService(db_service)
    csv_import_service = CSVImportService(db_service, company_service)

    # ツール初期化
    import_tool = CSVImportTool(db_service, company_service, csv_import_service)

    if args.verbose:
        import_tool.enable_verbose_logging()

    # ファイル存在確認
    if not import_tool.validate_csv_file_exists(args.foreign_csv):
        print(f"Error: Foreign companies CSV file not found: {args.foreign_csv}")
        return 1

    if not import_tool.validate_csv_file_exists(args.japan_csv):
        print(f"Error: Japan construction CSV file not found: {args.japan_csv}")
        return 1

    try:
        # データベース接続とインポート実行
        async with import_tool.database_connection():
            print("=" * 60)
            print("CSV IMPORT TOOL - EXECUTION START")
            print("=" * 60)
            print(f"Start time: {datetime.now()}")
            print(f"Foreign CSV: {args.foreign_csv}")
            print(f"Japan CSV: {args.japan_csv}")
            print()

            # インポート実行
            result = await import_tool.import_csv_files(args.foreign_csv, args.japan_csv)

            # 結果表示
            print("=" * 60)
            print("IMPORT RESULTS")
            print("=" * 60)
            print(f"Status: {'SUCCESS' if result.is_success else 'FAILED'}")
            print(f"Total processed: {result.total_processed}")
            print(f"Total errors: {result.total_errors}")
            print(f"Execution time: {result.execution_time:.2f} seconds")

            if result.errors:
                print(f"\nFirst 5 errors:")
                for i, error in enumerate(result.errors[:5], 1):
                    print(f"  {i}. {error}")

            # 統計情報表示
            print("\n" + "=" * 60)
            print("DATABASE STATISTICS")
            print("=" * 60)

            stats = await import_tool.generate_import_statistics()
            print(f"Total companies: {stats.get('total_companies', 0)}")
            print(f"Active companies: {stats.get('active_companies', 0)}")
            print(f"Inactive companies: {stats.get('inactive_companies', 0)}")

            print("\nIndustry distribution:")
            industry_dist = stats.get('industry_distribution', {})
            for industry, count in sorted(industry_dist.items(), key=lambda x: x[1], reverse=True):
                print(f"  {industry}: {count} companies")

            print("\nCompany size distribution:")
            size_dist = stats.get('size_distribution', {})
            for size, count in sorted(size_dist.items(), key=lambda x: x[1], reverse=True):
                print(f"  {size}: {count} companies")

            # データ整合性チェック（オプション）
            if args.check_integrity:
                print("\n" + "=" * 60)
                print("DATA INTEGRITY CHECK")
                print("=" * 60)

                integrity = await import_tool.check_data_integrity()
                print(f"Data integrity: {'VALID' if integrity.get('is_valid') else 'INVALID'}")
                print(f"Validation errors: {len(integrity.get('validation_errors', []))}")
                print(f"Missing required fields: {integrity.get('missing_required_fields', 0)}")
                print(f"Duplicate entries: {integrity.get('duplicate_entries', 0)}")

            print("\n" + "=" * 60)
            print("IMPORT COMPLETED")
            print("=" * 60)

            return 0 if result.is_success else 1

    except Exception as e:
        print(f"Fatal error during import: {e}")
        import_tool.logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)