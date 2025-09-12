"""
データベースアクセス基盤
"""
import logging
from typing import Optional
import motor.motor_asyncio
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
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