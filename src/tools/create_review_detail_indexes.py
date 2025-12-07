#!/usr/bin/env python3
"""
レビュー詳細ページ用のMongoDBインデックス作成スクリプト

個別レビュー詳細ページと質問別レビュー一覧ページのクエリパフォーマンスを
最適化するためのインデックスを作成します。

使用方法:
    uv run python src/tools/create_review_detail_indexes.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseService

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_review_detail_indexes(db_service: DatabaseService) -> bool:
    """
    レビュー詳細ページ用のインデックスを作成

    Args:
        db_service: データベースサービスインスタンス

    Returns:
        bool: 成功時True、失敗時False
    """
    try:
        collection = db_service.db['reviews']

        # 1. company_id + is_active + created_atの複合インデックス
        # 個別レビュー詳細ページと質問別レビュー一覧ページの基本クエリ用
        logger.info("company_id + is_active + created_at インデックスを作成中...")
        index_name_1 = await collection.create_index(
            [
                ("company_id", 1),
                ("is_active", 1),
                ("created_at", -1)
            ],
            name="company_id_1_is_active_1_created_at_-1"
        )
        logger.info(f"✓ インデックス作成完了: {index_name_1}")

        # 2. 各評価項目の複合インデックス
        # 質問別レビュー一覧ページのフィルタリング用
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment"
        ]

        for category in categories:
            logger.info(f"company_id + ratings.{category} + is_active + created_at インデックスを作成中...")
            index_name = await collection.create_index(
                [
                    ("company_id", 1),
                    (f"ratings.{category}", 1),
                    ("is_active", 1),
                    ("created_at", -1)
                ],
                name=f"company_id_1_ratings.{category}_1_is_active_1_created_at_-1"
            )
            logger.info(f"✓ インデックス作成完了: {index_name}")

        logger.info(f"\n✓ すべてのインデックス作成が完了しました（合計 {1 + len(categories)} 個）")
        return True

    except Exception as e:
        logger.exception(f"インデックス作成中にエラーが発生しました: {e}")
        return False


async def verify_indexes(db_service: DatabaseService) -> bool:
    """
    作成されたインデックスを検証

    Args:
        db_service: データベースサービスインスタンス

    Returns:
        bool: すべてのインデックスが存在する場合True、それ以外False
    """
    try:
        collection = db_service.db['reviews']
        indexes = await collection.index_information()

        # 必要なインデックスリスト
        required_indexes = [
            'company_id_1_is_active_1_created_at_-1',
            'company_id_1_ratings.recommendation_1_is_active_1_created_at_-1',
            'company_id_1_ratings.foreign_support_1_is_active_1_created_at_-1',
            'company_id_1_ratings.company_culture_1_is_active_1_created_at_-1',
            'company_id_1_ratings.employee_relations_1_is_active_1_created_at_-1',
            'company_id_1_ratings.evaluation_system_1_is_active_1_created_at_-1',
            'company_id_1_ratings.promotion_treatment_1_is_active_1_created_at_-1'
        ]

        logger.info("\n必要なインデックスの確認:")
        all_present = True
        for required_index in required_indexes:
            if required_index in indexes:
                logger.info(f"  ✓ {required_index} - 存在")
            else:
                logger.error(f"  ✗ {required_index} - 不足")
                all_present = False

        if all_present:
            logger.info(f"\n✓ すべての必要なインデックスが存在します（合計 {len(required_indexes)} 個）")
            return True
        else:
            logger.error("\n✗ 一部のインデックスが不足しています")
            return False

    except Exception as e:
        logger.exception(f"インデックス検証中にエラーが発生しました: {e}")
        return False


async def main():
    """メイン処理"""
    db_service = None
    try:
        logger.info("=" * 60)
        logger.info("レビュー詳細ページ用インデックス作成スクリプトを開始")
        logger.info("=" * 60)

        # データベース接続
        logger.info("\nMongoDBに接続中...")
        db_service = DatabaseService()
        await db_service.connect()
        logger.info("✓ MongoDB接続成功")

        # 既存のインデックスを確認
        logger.info("\n既存のインデックスを確認中...")
        collection = db_service.db['reviews']
        existing_indexes = await collection.index_information()

        logger.info(f"既存のインデックス数: {len(existing_indexes)}")
        for index_name, index_info in existing_indexes.items():
            logger.info(f"  - {index_name}: {index_info.get('key', [])}")

        # インデックスを作成
        logger.info("\n" + "-" * 60)
        create_success = await create_review_detail_indexes(db_service)

        if not create_success:
            logger.error("✗ インデックス作成に失敗しました")
            sys.exit(1)

        # 作成後のインデックスを確認
        logger.info("\n作成後のインデックスを確認中...")
        updated_indexes = await collection.index_information()
        logger.info(f"現在のインデックス数: {len(updated_indexes)}")

        # 新しく作成されたインデックスを表示
        new_indexes = set(updated_indexes.keys()) - set(existing_indexes.keys())
        if new_indexes:
            logger.info(f"\n新しく作成されたインデックス ({len(new_indexes)}件):")
            for index_name in sorted(new_indexes):
                index_info = updated_indexes[index_name]
                logger.info(f"  ✓ {index_name}: {index_info.get('key', [])}")
        else:
            logger.info("\n既存のインデックスがすべて存在していました（新規作成なし）")

        # インデックスを検証
        logger.info("\n" + "-" * 60)
        verify_success = await verify_indexes(db_service)

        if not verify_success:
            logger.error("✗ インデックス検証に失敗しました")
            sys.exit(1)

        logger.info("\n" + "=" * 60)
        logger.info("✓ すべての処理が正常に完了しました")
        logger.info("=" * 60)
        sys.exit(0)

    except Exception as e:
        logger.exception(f"スクリプト実行中にエラーが発生しました: {e}")
        sys.exit(1)

    finally:
        # データベース接続をクローズ
        if db_service:
            await db_service.close()
            logger.info("\nMongoDB接続をクローズしました")


if __name__ == "__main__":
    asyncio.run(main())
