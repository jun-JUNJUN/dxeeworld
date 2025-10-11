"""
UserService レビュー投稿履歴管理機能のテスト

Requirements: 1.7, 1.8
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from src.services.user_service import UserService
from src.utils.result import Result


class TestUserReviewHistory:
    """レビュー投稿履歴管理機能のテスト"""

    @pytest.fixture
    def service(self, mock_db_service):
        """テスト用UserServiceインスタンス"""
        return UserService(db_service=mock_db_service)

    @pytest.fixture
    def mock_db_service(self):
        """モックデータベースサービス"""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_last_review_posted_at_returns_datetime(self, service, mock_db_service):
        """最終レビュー投稿日時を取得 - 日時が存在する場合"""
        # Arrange
        user_id = "user123"
        expected_datetime = datetime(2024, 10, 1, 10, 0, 0)
        mock_db_service.find_one.return_value = {
            "_id": user_id,
            "last_review_posted_at": expected_datetime
        }

        # Act
        result = await service.get_last_review_posted_at(user_id)

        # Assert
        assert result == expected_datetime
        mock_db_service.find_one.assert_called_once_with(
            "users",
            {"_id": user_id}
        )

    @pytest.mark.asyncio
    async def test_get_last_review_posted_at_returns_none_when_no_history(self, service, mock_db_service):
        """最終レビュー投稿日時を取得 - 投稿履歴なし"""
        # Arrange
        user_id = "user123"
        mock_db_service.find_one.return_value = {
            "_id": user_id
            # last_review_posted_at フィールドなし
        }

        # Act
        result = await service.get_last_review_posted_at(user_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_review_posted_at_returns_none_when_user_not_found(self, service, mock_db_service):
        """最終レビュー投稿日時を取得 - ユーザーが見つからない"""
        # Arrange
        user_id = "nonexistent"
        mock_db_service.find_one.return_value = None

        # Act
        result = await service.get_last_review_posted_at(user_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_last_review_posted_at_success(self, service, mock_db_service):
        """最終レビュー投稿日時を更新 - 成功"""
        # Arrange
        user_id = "user123"
        review_datetime = datetime(2024, 10, 11, 15, 30, 0)
        mock_db_service.update_one.return_value = {"modified_count": 1}

        # Act
        result = await service.update_last_review_posted_at(user_id, review_datetime)

        # Assert
        assert result.is_success is True
        assert result.data is True
        mock_db_service.update_one.assert_called_once()
        call_args = mock_db_service.update_one.call_args
        assert call_args[0][0] == "users"
        assert call_args[0][1] == {"_id": user_id}
        assert call_args[0][2]["last_review_posted_at"] == review_datetime

    @pytest.mark.asyncio
    async def test_update_last_review_posted_at_uses_current_time_by_default(self, service, mock_db_service):
        """最終レビュー投稿日時を更新 - デフォルトで現在時刻を使用"""
        # Arrange
        user_id = "user123"
        mock_db_service.update_one.return_value = {"modified_count": 1}
        before_call = datetime.utcnow()

        # Act
        result = await service.update_last_review_posted_at(user_id)

        # Assert
        after_call = datetime.utcnow()
        assert result.is_success is True

        # 呼び出し引数を確認
        call_args = mock_db_service.update_one.call_args[0][2]
        updated_time = call_args["last_review_posted_at"]

        # 呼び出し時刻が前後1秒以内であることを確認
        assert before_call <= updated_time <= after_call

    @pytest.mark.asyncio
    async def test_check_review_access_within_one_year_true(self, service, mock_db_service):
        """1年以内のレビュー投稿履歴チェック - True"""
        # Arrange
        user_id = "user123"
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        mock_db_service.find_one.return_value = {
            "_id": user_id,
            "last_review_posted_at": six_months_ago
        }

        # Act
        result = await service.check_review_access_within_one_year(user_id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_review_access_within_one_year_false_more_than_one_year(self, service, mock_db_service):
        """1年以内のレビュー投稿履歴チェック - 1年以上前はFalse"""
        # Arrange
        user_id = "user123"
        thirteen_months_ago = datetime.utcnow() - timedelta(days=395)
        mock_db_service.find_one.return_value = {
            "_id": user_id,
            "last_review_posted_at": thirteen_months_ago
        }

        # Act
        result = await service.check_review_access_within_one_year(user_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_review_access_within_one_year_false_no_history(self, service, mock_db_service):
        """1年以内のレビュー投稿履歴チェック - 履歴なしはFalse"""
        # Arrange
        user_id = "user123"
        mock_db_service.find_one.return_value = {
            "_id": user_id
            # last_review_posted_at フィールドなし
        }

        # Act
        result = await service.check_review_access_within_one_year(user_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_review_access_within_one_year_false_user_not_found(self, service, mock_db_service):
        """1年以内のレビュー投稿履歴チェック - ユーザーが見つからない場合はFalse"""
        # Arrange
        user_id = "nonexistent"
        mock_db_service.find_one.return_value = None

        # Act
        result = await service.check_review_access_within_one_year(user_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_review_access_exactly_one_year_ago(self, service, mock_db_service):
        """1年以内のレビュー投稿履歴チェック - ちょうど1年前（境界値テスト）"""
        # Arrange
        user_id = "user123"
        # utcnow() を2回呼ぶと微妙な時間差が出るので、1秒プラスして境界内に確実に含める
        exactly_one_year_ago = datetime.utcnow() - timedelta(days=365) + timedelta(seconds=1)
        mock_db_service.find_one.return_value = {
            "_id": user_id,
            "last_review_posted_at": exactly_one_year_ago
        }

        # Act
        result = await service.check_review_access_within_one_year(user_id)

        # Assert
        assert result is True  # ちょうど365日前は「1年以内」とみなす

    @pytest.mark.asyncio
    async def test_check_review_access_one_day_over_one_year(self, service, mock_db_service):
        """1年以内のレビュー投稿履歴チェック - 1年+1日前（境界値テスト）"""
        # Arrange
        user_id = "user123"
        one_year_and_one_day_ago = datetime.utcnow() - timedelta(days=366)
        mock_db_service.find_one.return_value = {
            "_id": user_id,
            "last_review_posted_at": one_year_and_one_day_ago
        }

        # Act
        result = await service.check_review_access_within_one_year(user_id)

        # Assert
        assert result is False
