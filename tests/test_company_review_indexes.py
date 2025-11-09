"""
レビュー一覧ページ用のMongoDBインデックステスト
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.company_service import CompanyService


class TestCompanyReviewIndexes:
    """レビュー集計データ用のインデックステスト"""

    @pytest.fixture
    def company_service(self):
        """テスト用のCompanyServiceインスタンスを作成"""
        mock_db = MagicMock()
        mock_db.create_index = AsyncMock(return_value="index_name")
        service = CompanyService(mock_db)
        return service

    @pytest.mark.asyncio
    async def test_create_review_summary_indexes(self, company_service):
        """レビュー集計データ用のインデックスが作成されることを確認"""
        # 実行
        result = await company_service.create_review_summary_indexes()

        # 検証
        assert result is True
        assert company_service.db_service.create_index.call_count >= 4

        # 各インデックスが作成されていることを確認
        calls = company_service.db_service.create_index.call_args_list

        # review_summary.overall_average の降順インデックス
        assert any(
            call[0][0] == 'companies' and
            call[0][1] == [('review_summary.overall_average', -1)]
            for call in calls
        ), "overall_average降順インデックスが作成されていません"

        # review_summary.total_reviews の降順インデックス
        assert any(
            call[0][0] == 'companies' and
            call[0][1] == [('review_summary.total_reviews', -1)]
            for call in calls
        ), "total_reviews降順インデックスが作成されていません"

        # review_summary.last_updated の降順インデックス
        assert any(
            call[0][0] == 'companies' and
            call[0][1] == [('review_summary.last_updated', -1)]
            for call in calls
        ), "last_updated降順インデックスが作成されていません"

        # 複合インデックス（overall_average + total_reviews）
        assert any(
            call[0][0] == 'companies' and
            call[0][1] == [('review_summary.overall_average', -1), ('review_summary.total_reviews', -1)]
            for call in calls
        ), "複合インデックス（overall_average + total_reviews）が作成されていません"

    @pytest.mark.asyncio
    async def test_create_review_summary_indexes_handles_errors(self, company_service):
        """インデックス作成エラー時に適切にハンドリングされることを確認"""
        # エラーを発生させる
        company_service.db_service.create_index = AsyncMock(
            side_effect=Exception("MongoDB connection error")
        )

        # 実行
        result = await company_service.create_review_summary_indexes()

        # 検証
        assert result is False

    @pytest.mark.asyncio
    async def test_create_review_summary_indexes_is_idempotent(self, company_service):
        """インデックス作成が冪等であることを確認（複数回実行しても問題ない）"""
        # 1回目の実行
        result1 = await company_service.create_review_summary_indexes()
        assert result1 is True

        # 2回目の実行
        result2 = await company_service.create_review_summary_indexes()
        assert result2 is True

        # 両方成功することを確認
        assert company_service.db_service.create_index.call_count >= 8  # 4インデックス × 2回
