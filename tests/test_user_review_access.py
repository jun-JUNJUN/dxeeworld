"""
ユーザーモデルのレビューアクセス権限関連フィールドのテスト
タスク 1.2: User モデルにレビュー投稿日時フィールド追加
"""
import pytest
from datetime import datetime, timedelta, timezone
from src.models.user import User, UserType, UserProfile


class TestUserReviewAccessFields:
    """ユーザーモデルのレビューアクセス権限フィールドのテスト"""

    def test_user_with_last_review_posted_at_field(self):
        """last_review_posted_atフィールドを持つユーザーを作成できる"""
        now = datetime.now(timezone.utc)
        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password",
            last_review_posted_at=now
        )

        assert user.last_review_posted_at == now

    def test_user_without_last_review_posted_at_field(self):
        """last_review_posted_atフィールドなしでユーザーを作成できる（オプショナル）"""
        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password"
        )

        assert user.last_review_posted_at is None

    def test_user_to_dict_includes_last_review_posted_at(self):
        """to_dict()がlast_review_posted_atフィールドを含む"""
        now = datetime.now(timezone.utc)
        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password",
            last_review_posted_at=now
        )

        result = user.to_dict()

        assert "last_review_posted_at" in result
        assert result["last_review_posted_at"] == now.isoformat()

    def test_user_to_dict_without_last_review_posted_at(self):
        """to_dict()でlast_review_posted_atがNoneの場合、Noneが含まれる"""
        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password"
        )

        result = user.to_dict()

        assert "last_review_posted_at" in result
        assert result["last_review_posted_at"] is None

    def test_user_from_dict_includes_last_review_posted_at(self):
        """from_dict()がlast_review_posted_atフィールドを正しく読み込む"""
        now = datetime.now(timezone.utc)
        data = {
            "_id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "user_type": "JOB_SEEKER",
            "password_hash": "hashed_password",
            "last_review_posted_at": now
        }

        user = User.from_dict(data)

        assert user.last_review_posted_at == now

    def test_user_from_dict_without_last_review_posted_at(self):
        """from_dict()でlast_review_posted_atがない場合、Noneが設定される"""
        data = {
            "_id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "user_type": "JOB_SEEKER",
            "password_hash": "hashed_password"
        }

        user = User.from_dict(data)

        assert user.last_review_posted_at is None

    def test_user_update_last_review_posted_at(self):
        """last_review_posted_atを更新できる"""
        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password"
        )

        assert user.last_review_posted_at is None

        now = datetime.now(timezone.utc)
        user.update_last_review_posted_at(now)

        assert user.last_review_posted_at == now

    def test_has_review_access_within_one_year(self):
        """1年以内にレビューを投稿したユーザーはアクセス権限がある"""
        now = datetime.now(timezone.utc)
        six_months_ago = now - timedelta(days=180)

        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password",
            last_review_posted_at=six_months_ago
        )

        assert user.has_review_access() is True

    def test_has_review_access_over_one_year(self):
        """1年以上前にレビューを投稿したユーザーはアクセス権限がない"""
        now = datetime.now(timezone.utc)
        fourteen_months_ago = now - timedelta(days=420)

        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password",
            last_review_posted_at=fourteen_months_ago
        )

        assert user.has_review_access() is False

    def test_has_review_access_no_review_history(self):
        """レビュー投稿履歴がないユーザーはアクセス権限がない"""
        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password"
        )

        assert user.has_review_access() is False

    def test_has_review_access_exactly_one_year_ago(self):
        """ちょうど1年前にレビューを投稿したユーザーはアクセス権限がない（境界値）"""
        now = datetime.now(timezone.utc)
        exactly_one_year_ago = now - timedelta(days=365)

        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password",
            last_review_posted_at=exactly_one_year_ago
        )

        # 境界値：365日前はアクセス不可
        assert user.has_review_access() is False

    def test_has_review_access_just_under_one_year_ago(self):
        """1年未満（364日前）にレビューを投稿したユーザーはアクセス権限がある（境界値）"""
        now = datetime.now(timezone.utc)
        just_under_one_year = now - timedelta(days=364)

        user = User(
            id="user_123",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed_password",
            last_review_posted_at=just_under_one_year
        )

        assert user.has_review_access() is True
