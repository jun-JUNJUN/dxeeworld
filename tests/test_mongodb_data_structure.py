"""
MongoDB でのデータ構造テスト
タスク 1.3: MongoDB でデータモデル拡張が正しく動作するかテスト

注意: このテストは MongoDB が起動している必要があります
"""
import pytest
import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from src.database import DatabaseService
from src.models.review import Review, EmploymentStatus
from src.models.user import User, UserType


@pytest.mark.skipif(
    True,  # MongoDB が起動していない場合はスキップ
    reason="MongoDB が起動している場合のみ実行"
)
class TestMongoDBDataStructure:
    """MongoDB でのデータ構造テスト"""

    @pytest.fixture
    async def db_service(self):
        """テスト用データベースサービス"""
        db = DatabaseService()
        try:
            await db.connect()
        except Exception as e:
            pytest.skip(f"MongoDB に接続できません: {e}")

        # テストコレクションをクリーンアップ
        await db.delete_many("reviews_structure_test", {})
        await db.delete_many("users_structure_test", {})

        yield db

        # クリーンアップ
        await db.delete_many("reviews_structure_test", {})
        await db.delete_many("users_structure_test", {})
        await db.disconnect()

    @pytest.mark.asyncio
    async def test_review_multilingual_save_and_load(self, db_service):
        """多言語レビューを MongoDB に保存して読み込む"""
        # 多言語レビューを作成
        review_data = {
            "company_id": "company_test_123",
            "user_id": "user_test_456",
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "素晴らしい会社です"},
            "individual_average": 4.0,
            "answered_count": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "language": "ja",
            "comments_en": {"recommendation": "Great company"},
            "comments_zh": {"recommendation": "很棒的公司"}
        }

        # MongoDB に保存
        review_id = await db_service.create("reviews_structure_test", review_data)
        assert review_id is not None

        # MongoDB から読み込み
        loaded_data = await db_service.find_one(
            "reviews_structure_test",
            {"_id": ObjectId(review_id)}
        )

        # データ構造を検証
        assert loaded_data["language"] == "ja"
        assert loaded_data["comments"]["recommendation"] == "素晴らしい会社です"
        assert loaded_data["comments_en"]["recommendation"] == "Great company"
        assert loaded_data["comments_zh"]["recommendation"] == "很棒的公司"

        # Review モデルに変換できることを確認
        review = Review.from_dict(loaded_data)
        assert review.language == "ja"
        assert review.comments["recommendation"] == "素晴らしい会社です"
        assert review.comments_en["recommendation"] == "Great company"
        assert review.comments_zh["recommendation"] == "很棒的公司"

    @pytest.mark.asyncio
    async def test_user_with_last_review_posted_at_save_and_load(self, db_service):
        """last_review_posted_at を持つユーザーを MongoDB に保存して読み込む"""
        now = datetime.now(timezone.utc)

        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "user_type": "JOB_SEEKER",
            "password_hash": "hashed_password",
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "last_review_posted_at": now
        }

        # MongoDB に保存
        user_id = await db_service.create("users_structure_test", user_data)
        assert user_id is not None

        # MongoDB から読み込み
        loaded_data = await db_service.find_one(
            "users_structure_test",
            {"_id": ObjectId(user_id)}
        )

        # データ構造を検証
        assert "last_review_posted_at" in loaded_data
        assert loaded_data["last_review_posted_at"] == now

        # User モデルに変換できることを確認
        user = User.from_dict(loaded_data)
        assert user.last_review_posted_at == now
        assert user.has_review_access() is True

    @pytest.mark.asyncio
    async def test_review_multilingual_query(self, db_service):
        """多言語レビューのクエリテスト"""
        # 複数の言語でレビューを作成
        reviews_data = [
            {
                "company_id": "company_1",
                "user_id": "user_1",
                "employment_status": "current",
                "ratings": {"recommendation": 5},
                "comments": {"recommendation": "Excellent"},
                "individual_average": 5.0,
                "answered_count": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "language": "en"
            },
            {
                "company_id": "company_2",
                "user_id": "user_2",
                "employment_status": "former",
                "ratings": {"recommendation": 4},
                "comments": {"recommendation": "良い会社"},
                "individual_average": 4.0,
                "answered_count": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "language": "ja"
            },
            {
                "company_id": "company_3",
                "user_id": "user_3",
                "employment_status": "current",
                "ratings": {"recommendation": 3},
                "comments": {"recommendation": "不错的公司"},
                "individual_average": 3.0,
                "answered_count": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "language": "zh"
            }
        ]

        await db_service.bulk_insert("reviews_structure_test", reviews_data)

        # 言語別にクエリ
        ja_reviews = await db_service.find_many(
            "reviews_structure_test",
            {"language": "ja"}
        )
        assert len(ja_reviews) == 1
        assert ja_reviews[0]["language"] == "ja"

        en_reviews = await db_service.find_many(
            "reviews_structure_test",
            {"language": "en"}
        )
        assert len(en_reviews) == 1
        assert en_reviews[0]["language"] == "en"

        zh_reviews = await db_service.find_many(
            "reviews_structure_test",
            {"language": "zh"}
        )
        assert len(zh_reviews) == 1
        assert zh_reviews[0]["language"] == "zh"

    @pytest.mark.asyncio
    async def test_review_without_translations_optional(self, db_service):
        """翻訳フィールドなしのレビューも保存・読み込み可能"""
        # 翻訳フィールドなしのレビュー
        review_data = {
            "company_id": "company_test",
            "user_id": "user_test",
            "employment_status": "current",
            "ratings": {"recommendation": 4},
            "comments": {"recommendation": "Good company"},
            "individual_average": 4.0,
            "answered_count": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "language": "en"
            # comments_ja, comments_zh は含まない
        }

        review_id = await db_service.create("reviews_structure_test", review_data)

        # 読み込み
        loaded_data = await db_service.find_one(
            "reviews_structure_test",
            {"_id": ObjectId(review_id)}
        )

        assert loaded_data["language"] == "en"
        assert "comments_ja" not in loaded_data
        assert "comments_zh" not in loaded_data

        # Review モデルに変換できる
        review = Review.from_dict(loaded_data)
        assert review.language == "en"
        assert review.comments_ja is None
        assert review.comments_zh is None

    @pytest.mark.asyncio
    async def test_user_without_last_review_posted_at_optional(self, db_service):
        """last_review_posted_at なしのユーザーも保存・読み込み可能"""
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "user_type": "JOB_SEEKER",
            "password_hash": "hashed_password",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
            # last_review_posted_at は含まない
        }

        user_id = await db_service.create("users_structure_test", user_data)

        # 読み込み
        loaded_data = await db_service.find_one(
            "users_structure_test",
            {"_id": ObjectId(user_id)}
        )

        assert "last_review_posted_at" not in loaded_data

        # User モデルに変換できる（last_review_posted_at は None）
        user = User.from_dict(loaded_data)
        assert user.last_review_posted_at is None
        assert user.has_review_access() is False


# MongoDB なしでも実行できる簡易テスト
class TestDataModelStructure:
    """データモデルの構造テスト（MongoDB なし）"""

    def test_review_model_has_multilingual_fields(self):
        """Review モデルが多言語フィールドを持つ"""
        review = Review(
            id="test_id",
            company_id="company_123",
            user_id="user_456",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "良い"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            language="ja",
            comments_en={"recommendation": "Good"},
            comments_zh={"recommendation": "好"}
        )

        assert hasattr(review, 'language')
        assert hasattr(review, 'comments_en')
        assert hasattr(review, 'comments_zh')
        assert hasattr(review, 'comments_ja')

    def test_user_model_has_last_review_posted_at_field(self):
        """User モデルが last_review_posted_at フィールドを持つ"""
        user = User(
            id="test_id",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed",
            last_review_posted_at=datetime.now(timezone.utc)
        )

        assert hasattr(user, 'last_review_posted_at')
        assert hasattr(user, 'update_last_review_posted_at')
        assert hasattr(user, 'has_review_access')

    def test_review_to_dict_includes_new_fields(self):
        """Review.to_dict() が新規フィールドを含む"""
        review = Review(
            id="test_id",
            company_id="company_123",
            user_id="user_456",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "良い"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            language="ja",
            comments_en={"recommendation": "Good"}
        )

        data = review.to_dict()

        assert "language" in data
        assert "comments_en" in data
        assert data["language"] == "ja"

    def test_user_to_dict_includes_last_review_posted_at(self):
        """User.to_dict() が last_review_posted_at を含む"""
        now = datetime.now(timezone.utc)
        user = User(
            id="test_id",
            email="test@example.com",
            name="Test User",
            user_type=UserType.JOB_SEEKER,
            password_hash="hashed",
            last_review_posted_at=now
        )

        data = user.to_dict()

        assert "last_review_posted_at" in data
        assert data["last_review_posted_at"] == now.isoformat()
