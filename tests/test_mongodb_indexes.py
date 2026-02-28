"""
Test: MongoDB Index Creation (Task 6.2)

This module tests MongoDB index creation for review aggregation queries.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the ensure_indexes module for testing
from src.tools import ensure_indexes


class TestReviewIndexesModule:
    """Test the ensure_indexes module functions"""

    def test_index_definition_correctness(self):
        """Verify index specification matches design requirements"""
        # Design requirement: (company_id: 1, created_at: -1)
        # This is defined in ensure_indexes.REVIEW_INDEXES
        company_created_idx = ensure_indexes.REVIEW_INDEXES['company_created_idx']

        # Verify index key specification
        keys = company_created_idx['keys']
        assert keys == [('company_id', 1), ('created_at', -1)]

        # Verify company_id is ascending (1)
        assert keys[0] == ('company_id', 1)

        # Verify created_at is descending (-1)
        assert keys[1] == ('created_at', -1)

        # Verify background option is set
        assert company_created_idx['options']['background'] is True

        # Verify index name
        assert company_created_idx['options']['name'] == 'company_created_idx'

    def test_all_required_indexes_defined(self):
        """Verify all required indexes are defined"""
        required_indexes = [
            'company_created_idx',      # Main aggregation query optimization
            'user_created_idx',         # User review queries
            'active_company_idx'         # Active reviews filter
        ]

        for index_name in required_indexes:
            assert index_name in ensure_indexes.REVIEW_INDEXES
            assert 'keys' in ensure_indexes.REVIEW_INDEXES[index_name]
            assert 'options' in ensure_indexes.REVIEW_INDEXES[index_name]

    def test_index_names_unique(self):
        """Verify all index names are unique"""
        index_names = [
            idx['options']['name']
            for idx in ensure_indexes.REVIEW_INDEXES.values()
        ]

        # All names should be unique
        assert len(index_names) == len(set(index_names))


class TestMongoDBIndexesIntegration:
    """Test MongoDB index creation integration"""

    @pytest.mark.asyncio
    async def test_create_review_indexes_success(self):
        """Verify indexes can be created on collection"""
        # Mock database and collection
        mock_db = AsyncMock()
        mock_collection = AsyncMock()

        # Mock list_indexes to return no existing indexes
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_collection.list_indexes = AsyncMock(return_value=mock_cursor)
        mock_db.reviews = mock_collection

        # Call create_review_indexes
        created = await ensure_indexes.create_review_indexes(mock_db)

        # Verify create_index was called for each index
        assert mock_collection.create_index.call_count == len(ensure_indexes.REVIEW_INDEXES)

        # Verify all indexes were marked as created
        assert len(created) == len(ensure_indexes.REVIEW_INDEXES)

    @pytest.mark.asyncio
    async def test_create_review_indexes_skip_existing(self):
        """Verify existing indexes are not recreated"""
        # Mock database and collection
        mock_db = AsyncMock()
        mock_collection = AsyncMock()

        # Mock list_indexes to return ALL existing indexes (not just one)
        mock_cursor = AsyncMock()
        existing_index_list = [
            {'name': '_id_'},
            {'name': 'company_created_idx'},
            {'name': 'user_created_idx'},
            {'name': 'active_company_idx'}
        ]
        mock_cursor.to_list = AsyncMock(return_value=existing_index_list)
        mock_collection.list_indexes = AsyncMock(return_value=mock_cursor)
        mock_db.reviews = mock_collection

        # Call create_review_indexes
        created = await ensure_indexes.create_review_indexes(mock_db)

        # Verify create_index was NOT called for existing index
        # (Should only create indexes that don't exist)
        assert len(created) == 0

    @pytest.mark.asyncio
    async def test_list_existing_indexes(self):
        """Verify we can list existing indexes"""
        # Mock database and collection
        mock_db = AsyncMock()
        mock_collection = AsyncMock()

        # Mock list_indexes response
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'name': '_id_', 'key': {'_id': 1}},
            {'name': 'company_created_idx', 'key': [('company_id', 1), ('created_at', -1)]}
        ])
        mock_collection.list_indexes = AsyncMock(return_value=mock_cursor)
        mock_db.reviews = mock_collection

        # Call list_existing_indexes
        indexes = await ensure_indexes.list_existing_indexes(mock_db)

        # Verify indexes returned
        assert len(indexes) == 2
        assert indexes[0]['name'] == '_id_'
        assert indexes[1]['name'] == 'company_created_idx'

    @pytest.mark.asyncio
    async def test_drop_index_if_exists(self):
        """Verify we can drop existing index"""
        # Mock database and collection
        mock_db = AsyncMock()
        mock_collection = AsyncMock()

        # Mock index exists
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'name': '_id_'},
            {'name': 'company_created_idx'}
        ])
        mock_collection.list_indexes = AsyncMock(return_value=mock_cursor)
        mock_collection.drop_index = AsyncMock(return_value=None)
        mock_db.reviews = mock_collection

        # Call drop_index_if_exists
        result = await ensure_indexes.drop_index_if_exists(mock_db, 'company_created_idx')

        # Verify drop was called
        assert result is True
        mock_collection.drop_index.assert_called_once_with('company_created_idx')

    @pytest.mark.asyncio
    async def test_drop_index_if_not_exists(self):
        """Verify dropping non-existent index returns False"""
        # Mock database and collection
        mock_db = AsyncMock()
        mock_collection = AsyncMock()

        # Mock index does NOT exist
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'name': '_id_'}
        ])
        mock_collection.list_indexes = AsyncMock(return_value=mock_cursor)
        mock_db.reviews = mock_collection

        # Call drop_index_if_exists
        result = await ensure_indexes.drop_index_if_exists(mock_db, 'company_created_idx')

        # Verify drop was NOT called
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_indexes_all_present(self):
        """Verify index verification succeeds when all indexes exist"""
        # Mock database connection
        with patch('src.tools.ensure_indexes.get_database_connection') as mock_get_config:
            mock_get_config.return_value = {'uri': 'mongodb://test', 'db_name': 'test'}

            # Mock MongoDB client
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client.close = MagicMock()

            # Mock database
            mock_db = AsyncMock()
            mock_db.reviews = AsyncMock()

            # Mock list_indexes to return all required indexes
            mock_cursor = AsyncMock()
            existing_indexes = [
                {'name': '_id_'},
                {'name': 'company_created_idx'},
                {'name': 'user_created_idx'},
                {'name': 'active_company_idx'}
            ]
            mock_cursor.to_list = AsyncMock(return_value=existing_indexes)
            mock_db.reviews.list_indexes = AsyncMock(return_value=mock_cursor)

            with patch('src.tools.ensure_indexes.AsyncIOMotorClient', return_value=mock_client):
                mock_client.__getitem__ = MagicMock(return_value=mock_db)

                # Call verify_indexes
                all_present, missing = await ensure_indexes.verify_indexes()

                # Verify all indexes present
                assert all_present is True
                assert missing == []

    @pytest.mark.asyncio
    async def test_verify_indexes_missing(self):
        """Verify index verification detects missing indexes"""
        # Mock database connection
        with patch('src.tools.ensure_indexes.get_database_connection') as mock_get_config:
            mock_get_config.return_value = {'uri': 'mongodb://test', 'db_name': 'test'}

            # Mock MongoDB client
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client.close = MagicMock()

            # Mock database
            mock_db = AsyncMock()
            mock_db.reviews = AsyncMock()

            # Mock list_indexes to return only some indexes (missing company_created_idx)
            mock_cursor = AsyncMock()
            existing_indexes = [
                {'name': '_id_'},
                {'name': 'user_created_idx'},
                {'name': 'active_company_idx'}
            ]
            mock_cursor.to_list = AsyncMock(return_value=existing_indexes)
            mock_db.reviews.list_indexes = AsyncMock(return_value=mock_cursor)

            with patch('src.tools.ensure_indexes.AsyncIOMotorClient', return_value=mock_client):
                mock_client.__getitem__ = MagicMock(return_value=mock_db)

                # Call verify_indexes
                all_present, missing = await ensure_indexes.verify_indexes()

                # Verify missing index detected
                assert all_present is False
                assert 'company_created_idx' in missing

    @pytest.mark.asyncio
    async def test_ensure_all_indexes_workflow(self):
        """Verify complete index creation workflow"""
        # Mock database connection
        with patch('src.tools.ensure_indexes.get_database_connection') as mock_get_config:
            mock_get_config.return_value = {'uri': 'mongodb://test', 'db_name': 'test'}

            # Mock MongoDB client
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client.close = MagicMock()

            # Mock database and collection
            mock_db = AsyncMock()
            mock_collection = AsyncMock()

            # Mock no existing indexes
            mock_cursor = AsyncMock()
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_collection.list_indexes = AsyncMock(return_value=mock_cursor)
            mock_db.reviews = mock_collection

            with patch('src.tools.ensure_indexes.AsyncIOMotorClient', return_value=mock_client):
                mock_client.__getitem__ = MagicMock(return_value=mock_db)

                # Call ensure_all_indexes
                result = await ensure_indexes.ensure_all_indexes()

                # Verify workflow completed successfully
                assert result is True

                # Verify create_index was called
                assert mock_collection.create_index.call_count == len(ensure_indexes.REVIEW_INDEXES)

                # Verify connection closed
                mock_client.close.assert_called_once()
