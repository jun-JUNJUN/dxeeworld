#!/usr/bin/env python3
"""
レビュー集計データ用のMongoDBインデックス作成スクリプト

レビュー一覧ページの検索・ソート機能を最適化するためのインデックスを作成します。

使用方法:
    uv run python src/tools/create_review_indexes.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseService
from src.services.company_service import CompanyService

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_review_indexes():
    """レビュー集計データ用のインデックスを作成"""
    db_service = None
    try:
        logger.info("=" * 60)
        logger.info("レビュー集計データ用インデックス作成スクリプトを開始")
        logger.info("=" * 60)

        # データベース接続
        logger.info("MongoDBに接続中...")
        db_service = DatabaseService()
        await db_service.connect()
        logger.info("MongoDB接続成功")

        # CompanyServiceを初期化
        company_service = CompanyService(db_service)

        # 既存のインデックスを確認
        logger.info("\n既存のインデックスを確認中...")
        collection = db_service.db['companies']
        existing_indexes = await collection.index_information()

        logger.info(f"既存のインデックス数: {len(existing_indexes)}")
        for index_name, index_info in existing_indexes.items():
            logger.info(f"  - {index_name}: {index_info.get('key', [])}")

        # レビュー集計データ用のインデックスを作成
        logger.info("\nレビュー集計データ用のインデックスを作成中...")
        result = await company_service.create_review_summary_indexes()

        if result:
            logger.info("✓ レビュー集計データ用のインデックス作成に成功しました")

            # 作成後のインデックスを確認
            logger.info("\n作成後のインデックスを確認中...")
            updated_indexes = await collection.index_information()
            logger.info(f"現在のインデックス数: {len(updated_indexes)}")

            # 新しく作成されたインデックスを表示
            new_indexes = set(updated_indexes.keys()) - set(existing_indexes.keys())
            if new_indexes:
                logger.info(f"\n新しく作成されたインデックス ({len(new_indexes)}件):")
                for index_name in new_indexes:
                    index_info = updated_indexes[index_name]
                    logger.info(f"  ✓ {index_name}: {index_info.get('key', [])}")
            else:
                logger.info("\n既存のインデックスがすべて存在していました（新規作成なし）")
        else:
            logger.error("✗ レビュー集計データ用のインデックス作成に失敗しました")
            return False

        logger.info("\n" + "=" * 60)
        logger.info("レビュー集計データ用インデックス作成スクリプトが完了しました")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.exception(f"インデックス作成中にエラーが発生しました: {e}")
        return False

    finally:
        # データベース接続をクローズ
        if db_service:
            await db_service.close()
            logger.info("MongoDB接続をクローズしました")


async def verify_indexes():
    """作成されたインデックスを検証"""
    db_service = None
    try:
        logger.info("\n" + "=" * 60)
        logger.info("インデックス検証を開始")
        logger.info("=" * 60)

        # データベース接続
        db_service = DatabaseService()
        await db_service.connect()

        collection = db_service.db['companies']
        indexes = await collection.index_information()

        # 必要なインデックスが存在するか確認
        required_indexes = [
            'review_summary.overall_average_-1',
            'review_summary.total_reviews_-1',
            'review_summary.last_updated_-1',
            'review_summary.overall_average_-1_review_summary.total_reviews_-1'
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
            logger.info("\n✓ すべての必要なインデックスが存在します")
            logger.info("=" * 60)
            return True
        else:
            logger.error("\n✗ 一部のインデックスが不足しています")
            logger.info("=" * 60)
            return False

    except Exception as e:
        logger.exception(f"インデックス検証中にエラーが発生しました: {e}")
        return False

    finally:
        if db_service:
            await db_service.close()


async def main():
    """メイン処理"""
    # インデックスを作成
    create_success = await create_review_indexes()

    if not create_success:
        logger.error("インデックス作成に失敗しました")
        sys.exit(1)

    # インデックスを検証
    verify_success = await verify_indexes()

    if not verify_success:
        logger.error("インデックス検証に失敗しました")
        sys.exit(1)

    logger.info("\n✓ すべての処理が正常に完了しました")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
