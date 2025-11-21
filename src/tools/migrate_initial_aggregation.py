"""
既存レビューデータの初回集計スクリプト

このスクリプトは、既存のレビューデータに対して企業ごとの集計を実行し、
Company.review_summary フィールドを初期化します。
"""
import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseService
from src.services.review_aggregation_service import ReviewAggregationService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InitialAggregationMigrator:
    """既存データの初回集計を実行するクラス"""

    def __init__(self, db_service):
        """
        Args:
            db_service: データベースサービス
        """
        self.db = db_service
        self.aggregation_service = ReviewAggregationService(db_service)

    async def get_companies_with_reviews(self):
        """
        レビューが存在する企業のリストを取得

        Returns:
            企業IDのリスト
        """
        try:
            # レビューが存在する企業IDを取得
            pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$company_id"}},
                {"$sort": {"_id": 1}}
            ]

            results = await self.db.aggregate("reviews", pipeline)
            company_ids = [str(item["_id"]) for item in results]

            logger.info("Found %d companies with reviews", len(company_ids))
            return company_ids

        except Exception:
            logger.exception("Failed to get companies with reviews")
            return []

    async def migrate_initial_aggregation(self):
        """既存レビューデータの初回集計を実行"""
        logger.info("=" * 80)
        logger.info("Starting initial aggregation migration")
        logger.info("=" * 80)

        # レビューが存在する企業を取得
        company_ids = await self.get_companies_with_reviews()

        if not company_ids:
            logger.info("No companies with reviews found")
            return {
                "success": True,
                "total_companies": 0,
                "successful": 0,
                "failed": 0
            }

        # 集計処理を順次実行
        successful_count = 0
        failed_count = 0
        failed_companies = []

        for i, company_id in enumerate(company_ids, 1):
            try:
                logger.info("[%d/%d] Aggregating company %s...", i, len(company_ids), company_id)

                result = await self.aggregation_service.aggregate_and_update_company(company_id)

                if result.get("success"):
                    successful_count += 1
                    logger.info(
                        "[%d/%d] ✓ Company %s: %d reviews, avg=%.2f",
                        i, len(company_ids), company_id,
                        result['total_reviews'], result['overall_average']
                    )
                else:
                    failed_count += 1
                    failed_companies.append((company_id, result.get("error", "Unknown error")))
                    logger.error(
                        "[%d/%d] ✗ Failed to aggregate company %s: %s",
                        i, len(company_ids), company_id, result.get('error')
                    )

            except Exception:
                failed_count += 1
                failed_companies.append((company_id, "Exception during aggregation"))
                logger.exception("[%d/%d] ✗ Exception for company %s", i, len(company_ids), company_id)

            # レート制限（100ms間隔）
            await asyncio.sleep(0.1)

        # サマリー表示
        logger.info("=" * 80)
        logger.info("Migration Summary")
        logger.info("=" * 80)
        logger.info("Total companies: %d", len(company_ids))
        logger.info("Successful: %d", successful_count)
        logger.info("Failed: %d", failed_count)

        if failed_companies:
            logger.info("\nFailed companies:")
            for company_id, error in failed_companies:
                logger.info("  - %s: %s", company_id, error)

        logger.info("=" * 80)
        logger.info("Initial aggregation migration completed")
        logger.info("=" * 80)

        return {
            "success": failed_count == 0,
            "total_companies": len(company_ids),
            "successful": successful_count,
            "failed": failed_count,
            "failed_companies": failed_companies
        }

    async def validate_aggregation_results(self):
        """
        集計結果のバリデーション

        Returns:
            バリデーション結果
        """
        logger.info("=" * 80)
        logger.info("Validating aggregation results")
        logger.info("=" * 80)

        validation_errors = []

        try:
            # review_summary が存在するすべての企業を取得
            companies = await self.db.find_many(
                "companies",
                {"review_summary": {"$exists": True}},
                limit=10000
            )

            logger.info("Found %d companies with review_summary", len(companies))

            for company in companies:
                company_id = str(company["_id"])
                review_summary = company.get("review_summary", {})

                # total_reviews の検証
                # company_idは文字列として保存されているため、文字列で検索
                actual_review_count = await self.db.count_documents(
                    "reviews",
                    {"company_id": company_id, "is_active": True}
                )

                if review_summary.get("total_reviews") != actual_review_count:
                    validation_errors.append(
                        f"Company {company_id}: total_reviews mismatch "
                        f"(expected {actual_review_count}, got {review_summary.get('total_reviews')})"
                    )

                # overall_average の範囲検証
                overall_avg = review_summary.get("overall_average", 0)
                if not (0.0 <= overall_avg <= 5.0):
                    validation_errors.append(
                        f"Company {company_id}: overall_average out of range ({overall_avg})"
                    )

                # category_averages の検証
                category_averages = review_summary.get("category_averages", {})
                required_categories = [
                    "recommendation",
                    "foreign_support",
                    "company_culture",
                    "employee_relations",
                    "evaluation_system",
                    "promotion_treatment"
                ]

                for category in required_categories:
                    if category not in category_averages:
                        validation_errors.append(
                            f"Company {company_id}: missing category '{category}'"
                        )

            # バリデーション結果サマリー
            logger.info("=" * 80)
            logger.info("Validation Summary")
            logger.info("=" * 80)
            logger.info("Companies validated: %d", len(companies))
            logger.info("Validation errors: %d", len(validation_errors))

            if validation_errors:
                logger.info("\nValidation errors:")
                for error in validation_errors[:20]:  # 最初の20件のみ表示
                    logger.info("  - %s", error)

                if len(validation_errors) > 20:
                    logger.info("  ... and %d more errors", len(validation_errors) - 20)

            logger.info("=" * 80)

            return {
                "success": len(validation_errors) == 0,
                "companies_validated": len(companies),
                "error_count": len(validation_errors),
                "errors": validation_errors
            }

        except Exception as e:
            logger.exception("Validation failed")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """メイン関数"""
    db_service = None

    try:
        # データベース接続
        logger.info("Connecting to database...")
        db_service = DatabaseService()
        await db_service.connect()

        # 移行実行
        migrator = InitialAggregationMigrator(db_service)

        # 初回集計実行
        migration_result = await migrator.migrate_initial_aggregation()

        # バリデーション実行
        validation_result = await migrator.validate_aggregation_results()

        # 総合結果
        if migration_result.get("success") and validation_result.get("success"):
            logger.info("\n✓ Migration and validation completed successfully!")
            return 0
        else:
            logger.error("\n✗ Migration or validation failed!")
            return 1

    except Exception:
        logger.exception("Fatal error during migration")
        return 1

    finally:
        # データベース接続クローズ
        if db_service:
            try:
                await db_service.close()
                logger.info("Database connection closed")
            except Exception:
                logger.exception("Error closing database connection")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
