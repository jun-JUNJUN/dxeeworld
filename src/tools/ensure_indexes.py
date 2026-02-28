"""
MongoDB インデックス作成スクリプト

reviews コレクションのインデックスを作成・管理するスクリプト
用途：デプロイ時のインデックス初期化、またはデータベース構造の更新時
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient

from src.config import get_database_connection
from src.models.review import Review

logger = logging.getLogger(__name__)


# インデックス定義（Design Requirement 11.12）
REVIEW_INDEXES = {
    # 集約クエリのパフォーマンス最適化用インデックス
    # company_id 昇順 (1) + created_at 降順 (-1)
    'company_created_idx': {
        'keys': [('company_id', 1), ('created_at', -1)],
        'options': {
            'name': 'company_created_idx',
            'background': True  # バックグラウンド作成で他操作への影響を軽減
        }
    },
    # user_id インデックス（ユーザーのレビュー検索用）
    'user_created_idx': {
        'keys': [('user_id', 1), ('created_at', -1)],
        'options': {
            'name': 'user_created_idx',
            'background': True
        }
    },
    # is_active インデックス（有効レビューのみを取得）
    'active_company_idx': {
        'keys': [('is_active', 1), ('company_id', 1), ('created_at', -1)],
        'options': {
            'name': 'active_company_idx',
            'background': True
        }
    }
}


async def create_review_indexes(db):
    """
    reviews コレクションにインデックスを作成

    Args:
        db: Motor データベースインスタンス

    Returns:
        list: 作成されたインデックス名のリスト
    """
    collection = db.reviews
    created_indexes = []

    for index_name, index_config in REVIEW_INDEXES.items():
        try:
            # 既存のインデックスを確認
            existing_indexes = await collection.list_indexes()
            existing_index_names = [idx.get('name') for idx in await existing_indexes.to_list(length=None)]

            if index_config['options']['name'] not in existing_index_names:
                # インデックス作成
                await collection.create_index(
                    index_config['keys'],
                    **index_config['options']
                )
                created_indexes.append(index_name)
                logger.info(f"インデックス作成成功: {index_name}")
            else:
                logger.info(f"インデックス既存: {index_name}")

        except Exception as e:
            logger.error(f"インデックス作成失敗 ({index_name}): {e}")

    return created_indexes


async def list_existing_indexes(db):
    """
    既存のインデックス一覧を取得

    Args:
        db: Motor データベースインスタンス

    Returns:
        list: 既存インデックスの情報リスト
    """
    try:
        collection = db.reviews
        indexes_cursor = await collection.list_indexes()
        indexes = await indexes_cursor.to_list(length=None)
        return indexes
    except Exception as e:
        logger.error(f"インデックス一覧取得失敗: {e}")
        return []


async def drop_index_if_exists(db, index_name):
    """
    インデックスを削除（存在する場合のみ）

    Args:
        db: Motor データベースインスタンス
        index_name: 削除するインデックス名

    Returns:
        bool: 削除成功した場合はTrue
    """
    try:
        collection = db.reviews
        existing_indexes = await list_existing_indexes(db)
        existing_index_names = [idx.get('name') for idx in existing_indexes]

        if index_name in existing_index_names:
            await collection.drop_index(index_name)
            logger.info(f"インデックス削除成功: {index_name}")
            return True
        else:
            logger.warning(f"インデックス存在せず: {index_name}")
            return False

    except Exception as e:
        logger.error(f"インデックス削除失敗 ({index_name}): {e}")
        return False


async def ensure_all_indexes():
    """
    すべての必要なインデックスを作成

    メインエントリーポイント
    """
    logger.info("インデックス作成を開始...")

    try:
        # データベース接続
        config = get_database_connection()
        client = AsyncIOMotorClient(config['uri'])
        db = client[config['db_name']]

        # 接続テスト
        await client.admin.command('ping')
        logger.info("データベース接続成功")

        # インデックス作成
        created = await create_review_indexes(db)

        # 作成されたインデックス数をログ
        if created:
            logger.info(f"インデックス作成完了: {len(created)}個の新規インデックス")
        else:
            logger.info("すべてのインデックス既存 - 作成不要")

        # 接続切断
        client.close()
        logger.info("データベース接続切断")

        return True

    except Exception as e:
        logger.error(f"インデックス作成失敗: {e}")
        return False


async def verify_indexes():
    """
    必要なインデックスがすべて存在することを検証

    Returns:
        tuple: (all_present: bool, missing_indexes: list)
    """
    logger.info("インデックス検証を開始...")

    try:
        config = get_database_connection()
        client = AsyncIOMotorClient(config['uri'])
        db = client[config['db_name']]

        # 既存インデックス取得
        existing_indexes = await list_existing_indexes(db)
        existing_index_names = {idx.get('name') for idx in existing_indexes}

        # 必要なインデックス名取得
        required_index_names = {
            idx_config['options']['name']
            for idx_config in REVIEW_INDEXES.values()
        }

        # 欠落インデックス検出
        missing_indexes = required_index_names - existing_index_names
        all_present = len(missing_indexes) == 0

        if all_present:
            logger.info("すべてのインデックス存在検証成功")
        else:
            logger.warning(f"インデックス欠落検出: {missing_indexes}")

        client.close()
        return all_present, list(missing_indexes)

    except Exception as e:
        logger.error(f"インデックス検証失敗: {e}")
        return False, []


async def main():
    """メイン関数: コマンドライン実行用"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'create':
            success = await ensure_all_indexes()
            sys.exit(0 if success else 1)

        elif command == 'verify':
            all_present, missing = await verify_indexes()
            if all_present:
                print("✅ すべてのインデックスが存在します")
                sys.exit(0)
            else:
                print(f"❌ 欠落インデックス: {missing}")
                sys.exit(1)

        elif command == 'list':
            try:
                config = get_database_connection()
                client = AsyncIOMotorClient(config['uri'])
                db = client[config['db_name']]
                indexes = await list_existing_indexes(db)
                client.close()

                print("既存インデックス一覧:")
                for idx in indexes:
                    print(f"  - {idx.get('name')}: {idx.get('key')}")

                sys.exit(0)
            except Exception as e:
                print(f"エラー: {e}")
                sys.exit(1)

        else:
            print(f"不明なコマンド: {command}")
            print("使用方法: python ensure_indexes.py [create|verify|list]")
            sys.exit(1)
    else:
        print("使用方法: python ensure_indexes.py [create|verify|list]")
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
