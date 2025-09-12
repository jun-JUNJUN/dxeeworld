"""
テストファースト: MongoDB接続機能のテスト
"""
import pytest
import pytest_asyncio
from src.database import DatabaseService
from src.config import get_database_connection


class TestMongoDBConnection:
    """MongoDB接続とデータベース基盤のテスト"""

    @pytest_asyncio.async
    async def test_database_connection_can_be_established(self):
        """データベース接続が確立できることを確認"""
        db_service = DatabaseService()
        connection = await db_service.connect()
        assert connection is not None

    @pytest_asyncio.async
    async def test_database_health_check(self):
        """データベース接続の健全性チェックができることを確認"""
        db_service = DatabaseService()
        is_healthy = await db_service.health_check()
        assert isinstance(is_healthy, bool)

    @pytest_asyncio.async
    async def test_database_error_handling(self):
        """データベースエラーが適切に処理されることを確認"""
        db_service = DatabaseService()
        # 無効な接続情報でテスト
        with pytest.raises(Exception):
            await db_service.connect_with_invalid_config()

    def test_get_database_connection_config(self):
        """データベース接続設定が取得できることを確認"""
        config = get_database_connection()
        assert config is not None
        assert 'host' in config or 'uri' in config