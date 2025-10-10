"""
データモデル拡張のマイグレーションスクリプトのテスト
タスク 1.3: 既存データのマイグレーションスクリプト作成
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from src.database import DatabaseService


class TestMultilingualMigration:
    """多言語対応マイグレーションのテスト"""

    @pytest.fixture
    async def db_service(self):
        """テスト用データベースサービス"""
        db = DatabaseService()
        await db.connect()

        # クリーンアップ
        await db.delete_many("reviews_test", {})
        await db.delete_many("users_test", {})

        yield db

        # クリーンアップ
        await db.delete_many("reviews_test", {})
        await db.delete_many("users_test", {})
        await db.disconnect()

    @pytest.mark.asyncio
    async def test_migrate_reviews_adds_language_field(self, db_service):
        """既存のレビューに language フィールドを追加する"""
        # 既存のレビューデータを作成（language フィールドなし）
        old_review = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "良い会社です"},
            "individual_average": 4.0,
            "answered_count": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }

        review_id = await db_service.create("reviews_test", old_review)

        # マイグレーション実行（全ての language フィールドがない reviews に "ja" を設定）
        result = await db_service.update_many(
            "reviews_test",
            {"language": {"$exists": False}},
            {"$set": {"language": "ja"}}
        )

        assert result.modified_count == 1

        # マイグレーション後のデータ確認
        migrated_review = await db_service.find_one(
            "reviews_test",
            {"_id": ObjectId(review_id)}
        )

        assert migrated_review["language"] == "ja"
        assert migrated_review["comments"]["recommendation"] == "良い会社です"

    @pytest.mark.asyncio
    async def test_migrate_multiple_reviews(self, db_service):
        """複数の既存レビューに language フィールドを一括追加する"""
        # 3つの既存レビューを作成
        reviews = [
            {
                "company_id": f"company_{i}",
                "user_id": f"user_{i}",
                "employment_status": "current",
                "ratings": {"recommendation": i + 1},
                "comments": {"recommendation": f"コメント{i}"},
                "individual_average": float(i + 1),
                "answered_count": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            for i in range(3)
        ]

        await db_service.bulk_insert("reviews_test", reviews)

        # マイグレーション実行
        result = await db_service.update_many(
            "reviews_test",
            {"language": {"$exists": False}},
            {"$set": {"language": "ja"}}
        )

        assert result.modified_count == 3

        # 全てのレビューが "ja" になっていることを確認
        all_reviews = await db_service.find_many("reviews_test", {})
        for review in all_reviews:
            assert review["language"] == "ja"

    @pytest.mark.asyncio
    async def test_migrate_users_adds_last_review_posted_at(self, db_service):
        """既存のユーザーに last_review_posted_at フィールドを追加する"""
        # ユーザーを作成（last_review_posted_at なし）
        old_user = {
            "email": "test@example.com",
            "name": "Test User",
            "user_type": "JOB_SEEKER",
            "password_hash": "hashed_password",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }

        user_id = await db_service.create("users_test", old_user)

        # そのユーザーのレビューを作成
        review_time = datetime.now(timezone.utc) - timedelta(days=30)
        review = {
            "company_id": "company_123",
            "user_id": user_id,
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "良い"},
            "individual_average": 4.0,
            "answered_count": 1,
            "created_at": review_time,
            "updated_at": review_time,
            "is_active": True,
            "language": "ja"
        }

        await db_service.create("reviews_test", review)

        # マイグレーション実行
        # 各ユーザーの最新レビュー投稿日時を取得し、last_review_posted_at を設定
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": 1},
            {"$project": {"user_id": 1, "created_at": 1}}
        ]

        latest_reviews = await db_service.aggregate("reviews_test", pipeline)

        if latest_reviews:
            latest_review = latest_reviews[0]
            await db_service.update_one(
                "users_test",
                {"_id": ObjectId(user_id)},
                {"$set": {"last_review_posted_at": latest_review["created_at"]}}
            )

        # マイグレーション後のユーザー確認
        migrated_user = await db_service.find_one(
            "users_test",
            {"_id": ObjectId(user_id)}
        )

        assert "last_review_posted_at" in migrated_user
        assert migrated_user["last_review_posted_at"] == review_time

    @pytest.mark.asyncio
    async def test_migrate_users_without_reviews(self, db_service):
        """レビュー投稿履歴がないユーザーは last_review_posted_at が None になる"""
        # レビュー投稿履歴がないユーザーを作成
        user_without_reviews = {
            "email": "noreviews@example.com",
            "name": "No Reviews User",
            "user_type": "JOB_SEEKER",
            "password_hash": "hashed_password",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }

        user_id = await db_service.create("users_test", user_without_reviews)

        # マイグレーション実行（レビューがないので last_review_posted_at は None）
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": 1},
            {"$project": {"user_id": 1, "created_at": 1}}
        ]

        latest_reviews = await db_service.aggregate("reviews_test", pipeline)

        # レビューがない場合は None を設定
        if not latest_reviews:
            await db_service.update_one(
                "users_test",
                {"_id": ObjectId(user_id)},
                {"$set": {"last_review_posted_at": None}}
            )

        migrated_user = await db_service.find_one(
            "users_test",
            {"_id": ObjectId(user_id)}
        )

        assert "last_review_posted_at" in migrated_user
        assert migrated_user["last_review_posted_at"] is None

    @pytest.mark.asyncio
    async def test_migration_is_idempotent_for_reviews(self, db_service):
        """レビューマイグレーションは冪等性がある（複数回実行しても安全）"""
        # language フィールドありのレビューを作成
        review_with_language = {
            "company_id": "company_123",
            "user_id": "user_456",
            "employment_status": "current",
            "ratings": {"recommendation": 5},
            "comments": {"recommendation": "Excellent"},
            "individual_average": 5.0,
            "answered_count": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "language": "en"  # すでに language フィールドがある
        }

        review_id = await db_service.create("reviews_test", review_with_language)

        # マイグレーションを実行（language フィールドがあるので更新されないはず）
        result = await db_service.update_many(
            "reviews_test",
            {"language": {"$exists": False}},
            {"$set": {"language": "ja"}}
        )

        assert result.modified_count == 0  # 既に language があるので更新なし

        # データが変更されていないことを確認
        review = await db_service.find_one(
            "reviews_test",
            {"_id": ObjectId(review_id)}
        )

        assert review["language"] == "en"  # 元の値が保持されている

    @pytest.mark.asyncio
    async def test_migration_validation_check(self, db_service):
        """マイグレーション後のデータ整合性検証"""
        # マイグレーション前データ作成
        reviews_before = [
            {
                "company_id": "company_1",
                "user_id": "user_1",
                "employment_status": "current",
                "ratings": {"recommendation": 4},
                "comments": {"recommendation": "良い"},
                "individual_average": 4.0,
                "answered_count": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            },
            {
                "company_id": "company_2",
                "user_id": "user_2",
                "employment_status": "former",
                "ratings": {"recommendation": 3},
                "comments": {"recommendation": "普通"},
                "individual_average": 3.0,
                "answered_count": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "language": "ja"  # 既に language がある
            }
        ]

        await db_service.bulk_insert("reviews_test", reviews_before)

        # マイグレーション前の件数確認
        total_before = await db_service.count_documents("reviews_test", {})
        assert total_before == 2

        # マイグレーション実行
        result = await db_service.update_many(
            "reviews_test",
            {"language": {"$exists": False}},
            {"$set": {"language": "ja"}}
        )

        # マイグレーション後の検証
        total_after = await db_service.count_documents("reviews_test", {})
        assert total_after == 2  # 件数は変わらない

        # 全てのレビューに language フィールドがあることを確認
        reviews_without_language = await db_service.count_documents(
            "reviews_test",
            {"language": {"$exists": False}}
        )
        assert reviews_without_language == 0  # language がないレビューはゼロ

        # 全てのレビューの language が有効な値であることを確認
        all_reviews = await db_service.find_many("reviews_test", {})
        for review in all_reviews:
            assert review["language"] in ["en", "ja", "zh"]
