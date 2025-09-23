"""
レビュー履歴管理システムのテスト
"""
import pytest
from datetime import datetime
from src.models.review_history import ReviewHistory, ReviewAction


class TestReviewHistory:
    """ReviewHistoryモデルのテスト"""

    def test_review_history_creation(self):
        """レビュー履歴を作成できる"""
        previous_data = {
            "ratings": {"recommendation": 3},
            "comments": {"recommendation": "普通"}
        }

        history = ReviewHistory(
            id="history_123",
            review_id="review_456",
            user_id="user_789",
            company_id="company_012",
            action=ReviewAction.UPDATE,
            previous_data=previous_data,
            timestamp=datetime(2024, 1, 1)
        )

        assert history.id == "history_123"
        assert history.review_id == "review_456"
        assert history.user_id == "user_789"
        assert history.company_id == "company_012"
        assert history.action == ReviewAction.UPDATE
        assert history.previous_data == previous_data
        assert history.timestamp == datetime(2024, 1, 1)

    def test_review_history_from_dict(self):
        """辞書からReviewHistoryオブジェクトを作成できる"""
        data = {
            "_id": "history_789",
            "review_id": "review_123",
            "user_id": "user_456",
            "company_id": "company_789",
            "action": "create",
            "previous_data": {
                "ratings": {"recommendation": 4},
                "comments": {"recommendation": "良い"}
            },
            "timestamp": datetime(2024, 2, 1)
        }

        history = ReviewHistory.from_dict(data)

        assert history.id == "history_789"
        assert history.action == ReviewAction.CREATE
        assert history.previous_data["ratings"]["recommendation"] == 4

    def test_review_history_to_dict(self):
        """ReviewHistoryオブジェクトを辞書に変換できる"""
        history = ReviewHistory(
            id="history_convert",
            review_id="review_convert",
            user_id="user_convert",
            company_id="company_convert",
            action=ReviewAction.CREATE,
            previous_data={"test": "data"},
            timestamp=datetime(2024, 1, 15)
        )

        result = history.to_dict()

        assert result["review_id"] == "review_convert"
        assert result["action"] == "create"
        assert result["previous_data"]["test"] == "data"
        assert result["timestamp"] == datetime(2024, 1, 15)

    def test_review_action_enum(self):
        """ReviewActionEnumが正しく定義されている"""
        assert ReviewAction.CREATE.value == "create"
        assert ReviewAction.UPDATE.value == "update"

    def test_review_history_with_empty_previous_data(self):
        """previous_dataが空の場合のレビュー履歴"""
        history = ReviewHistory(
            id="history_empty",
            review_id="review_empty",
            user_id="user_empty",
            company_id="company_empty",
            action=ReviewAction.CREATE,
            previous_data={},
            timestamp=datetime.utcnow()
        )

        assert history.previous_data == {}
        assert history.action == ReviewAction.CREATE

    def test_review_history_with_none_previous_data(self):
        """previous_dataがNoneの場合のレビュー履歴"""
        history = ReviewHistory(
            id="history_none",
            review_id="review_none",
            user_id="user_none",
            company_id="company_none",
            action=ReviewAction.CREATE,
            previous_data=None,
            timestamp=datetime.utcnow()
        )

        assert history.previous_data is None
        assert history.action == ReviewAction.CREATE

    def test_review_history_from_dict_with_none_previous_data(self):
        """previous_dataがNoneの辞書からオブジェクトを作成できる"""
        data = {
            "_id": "history_none_dict",
            "review_id": "review_none_dict",
            "user_id": "user_none_dict",
            "company_id": "company_none_dict",
            "action": "create",
            "previous_data": None,
            "timestamp": datetime(2024, 3, 1)
        }

        history = ReviewHistory.from_dict(data)

        assert history.previous_data is None
        assert history.action == ReviewAction.CREATE

    def test_review_history_to_dict_with_none_previous_data(self):
        """previous_dataがNoneのオブジェクトを辞書に変換できる"""
        history = ReviewHistory(
            id="history_none_to_dict",
            review_id="review_none_to_dict",
            user_id="user_none_to_dict",
            company_id="company_none_to_dict",
            action=ReviewAction.UPDATE,
            previous_data=None,
            timestamp=datetime(2024, 1, 20)
        )

        result = history.to_dict()

        assert result["previous_data"] is None
        assert result["action"] == "update"