"""
レビューモデルの多言語対応フィールドのテスト
タスク 1.1: Review モデルの多言語フィールド追加
"""
import pytest
from datetime import datetime
from src.models.review import Review, EmploymentStatus


class TestReviewMultilingualFields:
    """レビューモデルの多言語フィールドのテスト"""

    def test_review_with_language_field_japanese(self):
        """日本語でレビューを作成し、languageフィールドが正しく設定される"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "素晴らしい会社です"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="ja"
        )

        assert review.language == "ja"
        assert review.comments["recommendation"] == "素晴らしい会社です"

    def test_review_with_language_field_english(self):
        """英語でレビューを作成し、languageフィールドが正しく設定される"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 5},
            comments={"recommendation": "Great company"},
            individual_average=5.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="en"
        )

        assert review.language == "en"
        assert review.comments["recommendation"] == "Great company"

    def test_review_with_language_field_chinese(self):
        """中国語でレビューを作成し、languageフィールドが正しく設定される"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "很棒的公司"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="zh"
        )

        assert review.language == "zh"
        assert review.comments["recommendation"] == "很棒的公司"

    def test_review_with_translated_comments_ja_to_en_zh(self):
        """日本語レビューに英語と中国語の翻訳が含まれる"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "素晴らしい会社です"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="ja",
            comments_en={"recommendation": "Great company"},
            comments_zh={"recommendation": "很棒的公司"}
        )

        assert review.language == "ja"
        assert review.comments["recommendation"] == "素晴らしい会社です"
        assert review.comments_en["recommendation"] == "Great company"
        assert review.comments_zh["recommendation"] == "很棒的公司"

    def test_review_with_translated_comments_en_to_ja_zh(self):
        """英語レビューに日本語と中国語の翻訳が含まれる"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 5},
            comments={"recommendation": "Excellent workplace"},
            individual_average=5.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="en",
            comments_ja={"recommendation": "素晴らしい職場"},
            comments_zh={"recommendation": "优秀的工作场所"}
        )

        assert review.language == "en"
        assert review.comments["recommendation"] == "Excellent workplace"
        assert review.comments_ja["recommendation"] == "素晴らしい職場"
        assert review.comments_zh["recommendation"] == "优秀的工作场所"

    def test_review_with_translated_comments_zh_to_en_ja(self):
        """中国語レビューに英語と日本語の翻訳が含まれる"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "非常好的公司"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="zh",
            comments_en={"recommendation": "Very good company"},
            comments_ja={"recommendation": "とても良い会社"}
        )

        assert review.language == "zh"
        assert review.comments["recommendation"] == "非常好的公司"
        assert review.comments_en["recommendation"] == "Very good company"
        assert review.comments_ja["recommendation"] == "とても良い会社"

    def test_review_to_dict_includes_language_and_translations(self):
        """to_dict()が言語フィールドと翻訳フィールドを含む"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "素晴らしい会社です"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="ja",
            comments_en={"recommendation": "Great company"},
            comments_zh={"recommendation": "很棒的公司"}
        )

        result = review.to_dict()

        assert result["language"] == "ja"
        assert result["comments"]["recommendation"] == "素晴らしい会社です"
        assert result["comments_en"]["recommendation"] == "Great company"
        assert result["comments_zh"]["recommendation"] == "很棒的公司"

    def test_review_from_dict_includes_language_and_translations(self):
        """from_dict()が言語フィールドと翻訳フィールドを正しく読み込む"""
        data = {
            "_id": "review_123",
            "company_id": "company_456",
            "user_id": "user_789",
            "employment_status": "current",
            "ratings": {"recommendation": 5},
            "comments": {"recommendation": "Excellent workplace"},
            "individual_average": 5.0,
            "answered_count": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "language": "en",
            "comments_ja": {"recommendation": "素晴らしい職場"},
            "comments_zh": {"recommendation": "优秀的工作场所"}
        }

        review = Review.from_dict(data)

        assert review.language == "en"
        assert review.comments["recommendation"] == "Excellent workplace"
        assert review.comments_ja["recommendation"] == "素晴らしい職場"
        assert review.comments_zh["recommendation"] == "优秀的工作场所"

    def test_review_language_validation_valid_codes(self):
        """有効な言語コード（en, ja, zh）でレビューを作成できる"""
        for lang_code in ["en", "ja", "zh"]:
            review = Review(
                id=f"review_{lang_code}",
                company_id="company_456",
                user_id="user_789",
                employment_status=EmploymentStatus.CURRENT,
                ratings={"recommendation": 4},
                comments={"recommendation": "Test comment"},
                individual_average=4.0,
                answered_count=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                language=lang_code
            )
            assert review.language == lang_code

    def test_review_language_validation_invalid_code(self):
        """無効な言語コードでレビュー作成時にエラーが発生する"""
        with pytest.raises(ValueError, match="言語コードは 'en', 'ja', 'zh' のいずれかである必要があります"):
            Review(
                id="review_123",
                company_id="company_456",
                user_id="user_789",
                employment_status=EmploymentStatus.CURRENT,
                ratings={"recommendation": 4},
                comments={"recommendation": "Test comment"},
                individual_average=4.0,
                answered_count=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                language="fr"  # 無効な言語コード
            )

    def test_review_optional_translation_fields(self):
        """翻訳フィールドはオプショナルで、Noneでも有効"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "素晴らしい会社です"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="ja"
            # comments_en と comments_zh は指定しない
        )

        assert review.language == "ja"
        assert not hasattr(review, "comments_en") or review.comments_en is None
        assert not hasattr(review, "comments_zh") or review.comments_zh is None

    def test_review_to_dict_excludes_none_translation_fields(self):
        """to_dict()はNoneの翻訳フィールドを含めない"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "Test"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            language="en"
        )

        result = review.to_dict()

        assert result["language"] == "en"
        # Noneの翻訳フィールドはdict に含めない
        assert "comments_ja" not in result or result["comments_ja"] is None
        assert "comments_zh" not in result or result["comments_zh"] is None
