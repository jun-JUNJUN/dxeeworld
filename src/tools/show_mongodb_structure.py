"""
MongoDB データ構造表示ツール

実行方法:
    uv run python src/tools/show_mongodb_structure.py
"""
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
from src.database import DatabaseService

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MongoDBStructureViewer:
    """MongoDB のデータ構造を表示"""

    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    async def show_database_info(self):
        """データベース情報を表示"""
        logger.info("=" * 80)
        logger.info("MongoDB データベース構造")
        logger.info("=" * 80)
        logger.info(f"データベース名: {self.db.config['db_name']}")
        logger.info(f"接続URI: {self.db.config['uri']}")
        logger.info("")

    async def list_collections(self) -> List[str]:
        """コレクション一覧を取得"""
        collections = await self.db.db.list_collection_names()
        return sorted(collections)

    async def show_collection_stats(self, collection_name: str):
        """コレクションの統計情報を表示"""
        try:
            # ドキュメント数
            count = await self.db.count_documents(collection_name, {})

            # インデックス一覧
            indexes = await self.db.list_indexes(collection_name)

            # サンプルドキュメント（最新1件）
            sample = await self.db.find_many(
                collection_name,
                {},
                limit=1,
                sort=[("_id", -1)]
            )

            logger.info(f"📦 {collection_name}")
            logger.info(f"   ドキュメント数: {count:,} 件")

            if indexes:
                logger.info(f"   インデックス数: {len(indexes)} 個")
                for idx in indexes:
                    index_name = idx.get('name', 'unknown')
                    index_keys = idx.get('key', {})
                    keys_str = ", ".join([f"{k}: {v}" for k, v in index_keys.items()])
                    logger.info(f"      - {index_name}: {{ {keys_str} }}")

            if sample:
                doc = sample[0]
                logger.info(f"   フィールド構造:")
                self._show_document_structure(doc, indent=6)

            logger.info("")

        except Exception as e:
            logger.error(f"   エラー: {e}")
            logger.info("")

    def _show_document_structure(self, doc: Dict[str, Any], indent: int = 0):
        """ドキュメントの構造を表示"""
        prefix = " " * indent

        for key, value in doc.items():
            value_type = type(value).__name__

            if isinstance(value, dict):
                logger.info(f"{prefix}{key}: <dict> {{")
                self._show_document_structure(value, indent + 3)
                logger.info(f"{prefix}}}")
            elif isinstance(value, list):
                if value:
                    logger.info(f"{prefix}{key}: <list> [{len(value)} items]")
                    if isinstance(value[0], dict):
                        logger.info(f"{prefix}   [0]: {{")
                        self._show_document_structure(value[0], indent + 6)
                        logger.info(f"{prefix}   }}")
                    else:
                        logger.info(f"{prefix}   例: {value[0]}")
                else:
                    logger.info(f"{prefix}{key}: <list> []")
            elif isinstance(value, datetime):
                logger.info(f"{prefix}{key}: <datetime> {value.isoformat()}")
            elif isinstance(value, str) and len(value) > 50:
                logger.info(f"{prefix}{key}: <str> \"{value[:50]}...\" (長さ: {len(value)})")
            else:
                logger.info(f"{prefix}{key}: <{value_type}> {value}")

    async def show_reviews_structure(self):
        """reviews コレクションの詳細構造を表示"""
        logger.info("=" * 80)
        logger.info("Reviews コレクション詳細構造")
        logger.info("=" * 80)

        try:
            # 最新レビュー1件
            latest = await self.db.find_many("reviews", {}, limit=1, sort=[("created_at", -1)])

            if latest:
                review = latest[0]
                logger.info("\n📄 最新レビューのフィールド:")
                logger.info("-" * 80)
                self._show_document_structure(review, indent=3)

                # 多言語フィールドの確認
                logger.info("\n🌐 多言語対応フィールド:")
                logger.info(f"   language: {review.get('language', 'なし')}")
                logger.info(f"   comments_ja: {'あり' if 'comments_ja' in review else 'なし'}")
                logger.info(f"   comments_zh: {'あり' if 'comments_zh' in review else 'なし'}")
                logger.info(f"   comments_en: {'あり' if 'comments_en' in review else 'なし'}")

            # 言語別統計
            logger.info("\n📊 言語別統計:")
            for lang in ["ja", "en", "zh"]:
                count = await self.db.count_documents("reviews", {"language": lang})
                logger.info(f"   {lang}: {count:,} 件")

            # language フィールドがないレビュー
            no_lang = await self.db.count_documents("reviews", {"language": {"$exists": False}})
            logger.info(f"   language なし: {no_lang:,} 件")

            logger.info("")

        except Exception as e:
            logger.error(f"エラー: {e}")

    async def show_users_structure(self):
        """users コレクションの詳細構造を表示"""
        logger.info("=" * 80)
        logger.info("Users コレクション詳細構造")
        logger.info("=" * 80)

        try:
            # 最新ユーザー1件
            latest = await self.db.find_many("users", {}, limit=1, sort=[("created_at", -1)])

            if latest:
                user = latest[0]
                logger.info("\n👤 最新ユーザーのフィールド:")
                logger.info("-" * 80)
                # パスワードハッシュは表示しない
                display_user = {k: v for k, v in user.items() if k != 'password_hash'}
                if 'password_hash' in user:
                    display_user['password_hash'] = '<hidden>'
                self._show_document_structure(display_user, indent=3)

                # レビューアクセス権限の確認
                logger.info("\n🔑 レビューアクセス権限フィールド:")
                logger.info(f"   last_review_posted_at: {user.get('last_review_posted_at', 'なし')}")

            # last_review_posted_at 統計
            logger.info("\n📊 レビュー投稿履歴統計:")
            with_review = await self.db.count_documents(
                "users",
                {"last_review_posted_at": {"$exists": True, "$ne": None}}
            )
            without_review = await self.db.count_documents(
                "users",
                {"$or": [
                    {"last_review_posted_at": {"$exists": False}},
                    {"last_review_posted_at": None}
                ]}
            )
            logger.info(f"   レビュー投稿履歴あり: {with_review:,} 件")
            logger.info(f"   レビュー投稿履歴なし: {without_review:,} 件")

            logger.info("")

        except Exception as e:
            logger.error(f"エラー: {e}")

    async def show_companies_structure(self):
        """companies コレクションの詳細構造を表示"""
        logger.info("=" * 80)
        logger.info("Companies コレクション詳細構造")
        logger.info("=" * 80)

        try:
            # 最新企業1件
            latest = await self.db.find_many("companies", {}, limit=1, sort=[("created_at", -1)])

            if latest:
                company = latest[0]
                logger.info("\n🏢 最新企業のフィールド:")
                logger.info("-" * 80)
                self._show_document_structure(company, indent=3)

            logger.info("")

        except Exception as e:
            logger.error(f"エラー: {e}")

    async def run(self):
        """全ての構造情報を表示"""
        # データベース情報
        await self.show_database_info()

        # コレクション一覧
        collections = await self.list_collections()

        logger.info("📚 コレクション一覧:")
        logger.info("-" * 80)
        for col in collections:
            count = await self.db.count_documents(col, {})
            logger.info(f"   {col}: {count:,} 件")
        logger.info("")

        # 各コレクションの詳細統計
        logger.info("=" * 80)
        logger.info("コレクション詳細情報")
        logger.info("=" * 80)
        logger.info("")

        for col in collections:
            await self.show_collection_stats(col)

        # Reviews の詳細構造
        if "reviews" in collections:
            await self.show_reviews_structure()

        # Users の詳細構造
        if "users" in collections:
            await self.show_users_structure()

        # Companies の詳細構造
        if "companies" in collections:
            await self.show_companies_structure()

        # サマリー
        logger.info("=" * 80)
        logger.info("サマリー")
        logger.info("=" * 80)
        logger.info(f"総コレクション数: {len(collections)}")

        total_docs = 0
        for col in collections:
            count = await self.db.count_documents(col, {})
            total_docs += count

        logger.info(f"総ドキュメント数: {total_docs:,}")
        logger.info("")


async def main():
    """メイン実行関数"""
    db_service = DatabaseService()

    try:
        logger.info("MongoDB に接続中...\n")
        await db_service.connect()

        viewer = MongoDBStructureViewer(db_service)
        await viewer.run()

        return 0

    except Exception as e:
        logger.error(f"\n致命的エラー: {e}")
        logger.error("MongoDB が起動していることを確認してください:")
        logger.error("  docker ps | grep mongo")
        logger.error("  docker start dxeeworld-mongodb")
        return 1

    finally:
        await db_service.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
