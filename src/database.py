"""
データベースアクセス基盤
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable
import motor.motor_asyncio
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, OperationFailure
from pymongo import UpdateOne
from .config import get_database_connection

logger = logging.getLogger(__name__)


class DatabaseService:
    """MongoDB接続とデータベース操作を管理するサービス"""
    
    def __init__(self):
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db = None
        self.config = get_database_connection()
    
    async def connect(self):
        """データベースに接続"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.config['uri'],
                serverSelectionTimeoutMS=5000,  # 5秒のタイムアウト
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            self.db = self.client[self.config['db_name']]
            
            # 接続テスト
            await self.client.admin.command('ping')
            logger.info("データベース接続が確立されました")
            return self.client
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
    
    async def health_check(self) -> bool:
        """データベース接続の健全性をチェック"""
        try:
            if not self.client:
                await self.connect()
            
            # ping コマンドでヘルスチェック
            result = await self.client.admin.command('ping')
            return result.get('ok', 0) == 1
            
        except Exception as e:
            logger.error(f"データベースヘルスチェックエラー: {e}")
            return False
    
    async def connect_with_invalid_config(self):
        """テスト用: 無効な設定での接続（例外発生用）"""
        invalid_client = motor.motor_asyncio.AsyncIOMotorClient(
            "mongodb://invalid-host:99999",
            serverSelectionTimeoutMS=100
        )
        await invalid_client.admin.command('ping')
    
    async def find_one(self, collection: str, filter_dict: dict):
        """単一ドキュメントを検索"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            result = await collection_obj.find_one(filter_dict)
            return result
            
        except Exception as e:
            logger.error(f"find_one エラー: {e}")
            return None
    
    async def create(self, collection: str, document: dict):
        """ドキュメントを作成"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            result = await collection_obj.insert_one(document)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"create エラー: {e}")
            raise
    
    async def delete_one(self, collection: str, filter_dict: dict):
        """単一ドキュメントを削除"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            result = await collection_obj.delete_one(filter_dict)
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"delete_one エラー: {e}")
            return False
    
    async def find_many(self, collection: str, filter_dict: dict = None, limit: int = None, sort: list = None):
        """複数ドキュメントを検索"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            cursor = collection_obj.find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            results = await cursor.to_list(length=limit)
            return results
            
        except Exception as e:
            logger.error(f"find_many エラー: {e}")
            return []
    
    async def update_one(self, collection: str, filter_dict: dict, update_dict: dict):
        """単一ドキュメントを更新"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            result = await collection_obj.update_one(filter_dict, {'$set': update_dict})
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"update_one エラー: {e}")
            return False
    
    async def count_documents(self, collection: str, filter_dict: dict = None):
        """ドキュメント数をカウント"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            count = await collection_obj.count_documents(filter_dict or {})
            return count
            
        except Exception as e:
            logger.error(f"count_documents エラー: {e}")
            return 0
    
    async def aggregate(self, collection: str, pipeline: list):
        """集約クエリを実行"""
        try:
            if not self.client:
                await self.connect()
            
            collection_obj = self.db[collection]
            cursor = collection_obj.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            return results
            
        except Exception as e:
            logger.error(f"aggregate エラー: {e}")
            return []
    
    async def close(self):
        """データベース接続を閉じる"""
        if self.client:
            self.client.close()
            logger.info("データベース接続が閉じられました")

    async def connect_with_retry(self, max_retries: int = 3, retry_delay: float = 1.0):
        """リトライ機能付きデータベース接続"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await self.connect()
            except (ServerSelectionTimeoutError, ConnectionFailure) as e:
                last_exception = e
                logger.warning(f"接続失敗 (試行 {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数バックオフ

        raise last_exception

    async def find_one_with_retry(self, collection: str, filter_dict: dict, max_retries: int = 2):
        """リトライ機能付き単一ドキュメント検索"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                if not self.client:
                    await self.connect()

                collection_obj = self.db[collection]
                result = await collection_obj.find_one(filter_dict)
                return result

            except OperationFailure as e:
                last_exception = e
                logger.warning(f"操作失敗 (試行 {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)

        logger.error(f"find_one_with_retry 最終エラー: {last_exception}")
        return None

    async def bulk_insert(self, collection: str, documents: List[dict]) -> List[str]:
        """複数ドキュメントの一括挿入"""
        try:
            if not self.client:
                await self.connect()

            collection_obj = self.db[collection]
            result = await collection_obj.insert_many(documents)
            return [str(oid) for oid in result.inserted_ids]

        except Exception as e:
            logger.error(f"bulk_insert エラー: {e}")
            raise

    async def bulk_update(self, collection: str, updates: List[dict]) -> int:
        """複数ドキュメントの一括更新"""
        try:
            if not self.client:
                await self.connect()

            collection_obj = self.db[collection]

            # UpdateOneオペレーションのリストを作成
            operations = []
            for update in updates:
                operations.append(
                    UpdateOne(
                        filter=update["filter"],
                        update=update["update"],
                        upsert=update.get("upsert", False)
                    )
                )

            result = await collection_obj.bulk_write(operations)
            return result.modified_count

        except Exception as e:
            logger.error(f"bulk_update エラー: {e}")
            return 0

    async def find_paginated(self, collection: str, filter_dict: dict = None,
                           page: int = 1, page_size: int = 10,
                           sort: List = None) -> Dict[str, Any]:
        """ページネーション付き検索"""
        try:
            if not self.client:
                await self.connect()

            collection_obj = self.db[collection]

            # スキップ数計算
            skip = (page - 1) * page_size

            # クエリ構築
            cursor = collection_obj.find(filter_dict or {})

            if sort:
                cursor = cursor.sort(sort)

            cursor = cursor.skip(skip).limit(page_size)

            # 結果取得
            items = await cursor.to_list(length=page_size)

            # 総件数取得
            total_count = await collection_obj.count_documents(filter_dict or {})

            return {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }

        except Exception as e:
            logger.error(f"find_paginated エラー: {e}")
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total_count": 0,
                "total_pages": 0
            }

    async def with_transaction(self, operation: Callable) -> Any:
        """トランザクション付き操作実行"""
        if not self.client:
            await self.connect()

        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    result = await operation(session)
                    await session.commit_transaction()
                    return result
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"トランザクションエラー: {e}")
                    raise

    async def create_index(self, collection: str, index_spec: List, **options) -> str:
        """インデックス作成"""
        try:
            if not self.client:
                await self.connect()

            collection_obj = self.db[collection]
            result = await collection_obj.create_index(index_spec, **options)
            logger.info(f"インデックス作成完了: {result}")
            return result

        except Exception as e:
            logger.error(f"create_index エラー: {e}")
            raise

    async def list_indexes(self, collection: str) -> List[dict]:
        """インデックス一覧取得"""
        try:
            if not self.client:
                await self.connect()

            collection_obj = self.db[collection]
            cursor = collection_obj.list_indexes()
            indexes = await cursor.to_list(length=None)
            return indexes

        except Exception as e:
            logger.error(f"list_indexes エラー: {e}")
            return []