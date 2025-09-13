"""
データベースサービスの拡張機能テスト
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, OperationFailure
from src.database import DatabaseService


class TestDatabaseServiceRetry:
    """リトライロジックのテスト"""

    @pytest.mark.asyncio
    async def test_connect_retry_on_failure(self):
        """接続失敗時のリトライ機能"""
        db_service = DatabaseService()

        # 最初の2回は失敗、3回目で成功するモック
        with patch.object(db_service, 'client') as mock_client:
            mock_client.admin.command = AsyncMock(
                side_effect=[
                    ConnectionFailure("Connection failed"),
                    ServerSelectionTimeoutError("Timeout"),
                    {"ok": 1}  # 3回目で成功
                ]
            )

            # リトライロジックでconnectを呼び出す
            result = await db_service.connect_with_retry(max_retries=3)
            assert result is not None
            assert mock_client.admin.command.call_count <= 3

    @pytest.mark.asyncio
    async def test_connect_retry_exceeds_max_attempts(self):
        """最大リトライ回数を超えた場合のエラー"""
        db_service = DatabaseService()

        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client_class:
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.admin.command = AsyncMock(
                side_effect=ConnectionFailure("Connection failed")
            )

            # 最大リトライ数を超えて失敗
            with pytest.raises(ConnectionFailure):
                await db_service.connect_with_retry(max_retries=2)

    @pytest.mark.asyncio
    async def test_operation_retry_on_temporary_failure(self):
        """一時的な操作エラー時のリトライ"""
        db_service = DatabaseService()
        db_service.client = Mock()
        db_service.db = Mock()

        # 最初は失敗、2回目で成功
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(
            side_effect=[
                OperationFailure("Temporary failure"),
                {"_id": "123", "name": "Test"}
            ]
        )
        db_service.db.__getitem__ = Mock(return_value=mock_collection)

        result = await db_service.find_one_with_retry("test_collection", {"_id": "123"})
        assert result is not None
        assert result["name"] == "Test"


class TestDatabaseServiceBulkOperations:
    """バルク操作のテスト"""

    @pytest.mark.asyncio
    async def test_bulk_insert(self):
        """複数ドキュメントの一括挿入"""
        db_service = DatabaseService()
        db_service.client = Mock()
        db_service.db = Mock()

        mock_collection = AsyncMock()
        mock_collection.insert_many = AsyncMock(
            return_value=Mock(inserted_ids=["id1", "id2", "id3"])
        )
        db_service.db.__getitem__ = Mock(return_value=mock_collection)

        documents = [
            {"name": "Doc1"},
            {"name": "Doc2"},
            {"name": "Doc3"}
        ]

        result = await db_service.bulk_insert("test_collection", documents)
        assert len(result) == 3
        mock_collection.insert_many.assert_called_once_with(documents)

    @pytest.mark.asyncio
    async def test_bulk_update(self):
        """複数ドキュメントの一括更新"""
        db_service = DatabaseService()
        db_service.client = Mock()
        db_service.db = Mock()

        mock_collection = AsyncMock()
        mock_collection.bulk_write = AsyncMock(
            return_value=Mock(modified_count=2)
        )
        db_service.db.__getitem__ = Mock(return_value=mock_collection)

        updates = [
            {"filter": {"_id": "1"}, "update": {"$set": {"status": "active"}}},
            {"filter": {"_id": "2"}, "update": {"$set": {"status": "inactive"}}}
        ]

        result = await db_service.bulk_update("test_collection", updates)
        assert result == 2


class TestDatabaseServicePagination:
    """ページネーション機能のテスト"""

    @pytest.mark.asyncio
    async def test_find_with_pagination(self):
        """ページネーション付き検索"""
        db_service = DatabaseService()
        db_service.client = Mock()
        db_service.db = Mock()

        # 10件のダミーデータ
        dummy_data = [{"id": i, "name": f"Item{i}"} for i in range(10)]

        mock_collection = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=dummy_data[:5])

        mock_collection.find = Mock(return_value=mock_cursor)
        db_service.db.__getitem__ = Mock(return_value=mock_collection)

        result = await db_service.find_paginated(
            "test_collection",
            filter_dict={},
            page=1,
            page_size=5,
            sort=[("created_at", -1)]
        )

        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 5
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(5)


class TestDatabaseServiceTransactions:
    """トランザクション機能のテスト"""

    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """トランザクションの正常コミット"""
        db_service = DatabaseService()
        db_service.client = Mock()

        mock_session = AsyncMock()
        mock_session.start_transaction = AsyncMock()
        mock_session.commit_transaction = AsyncMock()
        mock_session.abort_transaction = AsyncMock()

        db_service.client.start_session = AsyncMock(return_value=mock_session)

        async def transaction_operations(session):
            # トランザクション内の操作
            return True

        result = await db_service.with_transaction(transaction_operations)
        assert result is True
        mock_session.start_transaction.assert_called_once()
        mock_session.commit_transaction.assert_called_once()
        mock_session.abort_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        """エラー時のトランザクションロールバック"""
        db_service = DatabaseService()
        db_service.client = Mock()

        mock_session = AsyncMock()
        mock_session.start_transaction = AsyncMock()
        mock_session.commit_transaction = AsyncMock()
        mock_session.abort_transaction = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        db_service.client.start_session = AsyncMock(return_value=mock_session)

        async def failing_transaction(session):
            raise ValueError("Transaction failed")

        with pytest.raises(ValueError):
            await db_service.with_transaction(failing_transaction)

        mock_session.abort_transaction.assert_called_once()


class TestDatabaseServiceIndexing:
    """インデックス管理のテスト"""

    @pytest.mark.asyncio
    async def test_create_index(self):
        """インデックス作成"""
        db_service = DatabaseService()
        db_service.client = Mock()
        db_service.db = Mock()

        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock(return_value="index_name")
        db_service.db.__getitem__ = Mock(return_value=mock_collection)

        result = await db_service.create_index(
            "test_collection",
            [("field1", 1), ("field2", -1)],
            unique=True
        )

        assert result == "index_name"
        mock_collection.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_indexes(self):
        """インデックス一覧取得"""
        db_service = DatabaseService()
        db_service.client = Mock()
        db_service.db = Mock()

        mock_collection = Mock()
        mock_collection.list_indexes = Mock(return_value=AsyncMock())
        mock_collection.list_indexes().to_list = AsyncMock(
            return_value=[
                {"name": "_id_", "key": {"_id": 1}},
                {"name": "email_1", "key": {"email": 1}, "unique": True}
            ]
        )
        db_service.db.__getitem__ = Mock(return_value=mock_collection)

        indexes = await db_service.list_indexes("test_collection")
        assert len(indexes) == 2
        assert indexes[1]["unique"] is True