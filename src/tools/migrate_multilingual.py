"""
データモデル拡張のマイグレーションスクリプト
タスク 1.3: 既存データのマイグレーションスクリプト作成

実行方法:
    uv run python src/tools/migrate_multilingual.py --dry-run  # ドライラン（実際の更新なし）
    uv run python src/tools/migrate_multilingual.py           # 実際のマイグレーション実行
"""
import asyncio
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List
from src.database import DatabaseService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultilingualMigration:
    """多言語対応データモデル拡張のマイグレーション"""

    def __init__(self, db_service: DatabaseService, dry_run: bool = False):
        self.db = db_service
        self.dry_run = dry_run
        self.stats = {
            'reviews_updated': 0,
            'reviews_already_migrated': 0,
            'users_updated': 0,
            'users_without_reviews': 0,
            'errors': []
        }

    async def migrate_reviews(self) -> Dict[str, int]:
        """
        既存のレビューに language フィールドを追加

        - language フィールドがない全てのレビューに "ja" を設定
        - 既に language フィールドがあるレビューはスキップ（冪等性）
        """
        logger.info("=" * 60)
        logger.info("レビューマイグレーション開始")
        logger.info("=" * 60)

        try:
            # マイグレーション対象のレビュー数を確認
            reviews_to_migrate = await self.db.count_documents(
                "reviews",
                {"language": {"$exists": False}}
            )

            already_migrated = await self.db.count_documents(
                "reviews",
                {"language": {"$exists": True}}
            )

            logger.info(f"マイグレーション対象: {reviews_to_migrate} 件")
            logger.info(f"既にマイグレーション済み: {already_migrated} 件")

            if reviews_to_migrate == 0:
                logger.info("マイグレーション対象のレビューはありません")
                self.stats['reviews_already_migrated'] = already_migrated
                return self.stats

            if self.dry_run:
                logger.info(f"[DRY RUN] {reviews_to_migrate} 件のレビューに language='ja' を設定します")
                self.stats['reviews_updated'] = reviews_to_migrate
            else:
                # 実際のマイグレーション実行
                result = await self.db.update_many(
                    "reviews",
                    {"language": {"$exists": False}},
                    {"$set": {"language": "ja"}}
                )
                self.stats['reviews_updated'] = result.modified_count
                logger.info(f"✓ {result.modified_count} 件のレビューを更新しました")

            self.stats['reviews_already_migrated'] = already_migrated

        except Exception as e:
            error_msg = f"レビューマイグレーションエラー: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)

        return self.stats

    async def migrate_users(self) -> Dict[str, int]:
        """
        既存のユーザーに last_review_posted_at フィールドを追加

        - 各ユーザーの最新レビュー投稿日時を取得し、last_review_posted_at に設定
        - レビュー投稿履歴がないユーザーは None を設定
        """
        logger.info("=" * 60)
        logger.info("ユーザーマイグレーション開始")
        logger.info("=" * 60)

        try:
            # last_review_posted_at フィールドがないユーザーを取得
            users_to_migrate = await self.db.find_many(
                "users",
                {"last_review_posted_at": {"$exists": False}}
            )

            logger.info(f"マイグレーション対象ユーザー: {len(users_to_migrate)} 件")

            if not users_to_migrate:
                logger.info("マイグレーション対象のユーザーはありません")
                return self.stats

            for user in users_to_migrate:
                user_id = str(user['_id'])

                # ユーザーの最新レビューを取得
                pipeline = [
                    {"$match": {"user_id": user_id}},
                    {"$sort": {"created_at": -1}},
                    {"$limit": 1},
                    {"$project": {"created_at": 1}}
                ]

                latest_reviews = await self.db.aggregate("reviews", pipeline)

                if latest_reviews:
                    last_posted_at = latest_reviews[0]["created_at"]
                    logger.info(f"  ユーザー {user_id}: 最終投稿 {last_posted_at}")

                    if not self.dry_run:
                        await self.db.update_one(
                            "users",
                            {"_id": user['_id']},
                            {"$set": {"last_review_posted_at": last_posted_at}}
                        )
                    self.stats['users_updated'] += 1
                else:
                    logger.info(f"  ユーザー {user_id}: レビュー投稿履歴なし (None 設定)")

                    if not self.dry_run:
                        await self.db.update_one(
                            "users",
                            {"_id": user['_id']},
                            {"$set": {"last_review_posted_at": None}}
                        )
                    self.stats['users_without_reviews'] += 1

            logger.info(f"✓ {self.stats['users_updated']} 件のユーザーを更新しました")
            logger.info(f"  （レビュー投稿履歴なし: {self.stats['users_without_reviews']} 件）")

        except Exception as e:
            error_msg = f"ユーザーマイグレーションエラー: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)

        return self.stats

    async def create_indexes(self) -> None:
        """新規フィールド用のインデックスを作成"""
        logger.info("=" * 60)
        logger.info("インデックス作成")
        logger.info("=" * 60)

        try:
            if not self.dry_run:
                # reviews コレクションに language インデックスを作成
                await self.db.create_index("reviews", [("language", 1)])
                logger.info("✓ reviews.language インデックスを作成しました")

                # users コレクションに last_review_posted_at インデックスを作成
                await self.db.create_index("users", [("last_review_posted_at", -1)])
                logger.info("✓ users.last_review_posted_at インデックスを作成しました")
            else:
                logger.info("[DRY RUN] インデックスを作成します:")
                logger.info("  - reviews.language")
                logger.info("  - users.last_review_posted_at")

        except Exception as e:
            error_msg = f"インデックス作成エラー: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)

    async def validate_migration(self) -> bool:
        """マイグレーション後のデータ整合性を検証"""
        logger.info("=" * 60)
        logger.info("データ整合性検証")
        logger.info("=" * 60)

        validation_passed = True

        try:
            # 1. 全てのレビューに language フィールドがあることを確認
            reviews_without_language = await self.db.count_documents(
                "reviews",
                {"language": {"$exists": False}}
            )

            if reviews_without_language > 0:
                logger.error(f"✗ language フィールドがないレビューが {reviews_without_language} 件存在します")
                validation_passed = False
            else:
                logger.info("✓ 全てのレビューに language フィールドがあります")

            # 2. language フィールドの値が有効であることを確認
            invalid_languages = await self.db.count_documents(
                "reviews",
                {"language": {"$nin": ["en", "ja", "zh"]}}
            )

            if invalid_languages > 0:
                logger.error(f"✗ 無効な language 値のレビューが {invalid_languages} 件存在します")
                validation_passed = False
            else:
                logger.info("✓ 全てのレビューの language 値が有効です (en, ja, zh)")

            # 3. 全てのユーザーに last_review_posted_at フィールドがあることを確認
            users_without_field = await self.db.count_documents(
                "users",
                {"last_review_posted_at": {"$exists": False}}
            )

            if users_without_field > 0:
                logger.error(f"✗ last_review_posted_at フィールドがないユーザーが {users_without_field} 件存在します")
                validation_passed = False
            else:
                logger.info("✓ 全てのユーザーに last_review_posted_at フィールドがあります")

            # 4. 統計情報を表示
            total_reviews = await self.db.count_documents("reviews", {})
            total_users = await self.db.count_documents("users", {})

            logger.info(f"\n統計情報:")
            logger.info(f"  総レビュー数: {total_reviews}")
            logger.info(f"  総ユーザー数: {total_users}")

        except Exception as e:
            logger.error(f"検証エラー: {e}")
            validation_passed = False

        return validation_passed

    async def run(self) -> Dict[str, int]:
        """マイグレーション全体を実行"""
        start_time = datetime.now(timezone.utc)

        logger.info("\n" + "=" * 60)
        logger.info("多言語対応データモデル拡張マイグレーション")
        logger.info(f"実行モード: {'DRY RUN' if self.dry_run else '本番実行'}")
        logger.info(f"開始時刻: {start_time}")
        logger.info("=" * 60 + "\n")

        # 1. レビューマイグレーション
        await self.migrate_reviews()

        # 2. ユーザーマイグレーション
        await self.migrate_users()

        # 3. インデックス作成
        await self.create_indexes()

        # 4. 検証
        if not self.dry_run:
            validation_passed = await self.validate_migration()
            if not validation_passed:
                logger.error("\n✗ データ整合性検証に失敗しました")
            else:
                logger.info("\n✓ データ整合性検証に成功しました")

        # 結果サマリー
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("マイグレーション完了")
        logger.info("=" * 60)
        logger.info(f"終了時刻: {end_time}")
        logger.info(f"実行時間: {duration:.2f} 秒")
        logger.info(f"\n結果サマリー:")
        logger.info(f"  レビュー更新: {self.stats['reviews_updated']} 件")
        logger.info(f"  レビュー既存: {self.stats['reviews_already_migrated']} 件")
        logger.info(f"  ユーザー更新: {self.stats['users_updated']} 件")
        logger.info(f"  レビュー履歴なしユーザー: {self.stats['users_without_reviews']} 件")

        if self.stats['errors']:
            logger.error(f"\nエラー ({len(self.stats['errors'])} 件):")
            for error in self.stats['errors']:
                logger.error(f"  - {error}")
        else:
            logger.info("\nエラー: なし")

        return self.stats


async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description='多言語対応データモデル拡張マイグレーション'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='ドライラン（実際の更新は行わない）'
    )

    args = parser.parse_args()

    # データベース接続
    db_service = DatabaseService()

    try:
        await db_service.connect()
        logger.info("データベース接続成功\n")

        # マイグレーション実行
        migration = MultilingualMigration(db_service, dry_run=args.dry_run)
        stats = await migration.run()

        # 終了コード
        if stats['errors']:
            return 1  # エラーあり
        return 0  # 成功

    except Exception as e:
        logger.error(f"致命的エラー: {e}")
        return 1

    finally:
        await db_service.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
