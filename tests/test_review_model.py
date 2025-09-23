"""
レビューデータモデルのテスト
"""
import pytest
from datetime import datetime
from src.models.review import Review, ReviewCategory, EmploymentStatus, ReviewSummary


class TestReview:
    """Reviewモデルのテスト"""

    def test_review_creation_with_all_fields(self):
        """全フィールドを指定してレビューを作成できる"""
        ratings = {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": None,
            "employee_relations": 5,
            "evaluation_system": 2,
            "promotion_treatment": 4
        }

        comments = {
            "recommendation": "良い会社です",
            "foreign_support": "",
            "company_culture": None,
            "employee_relations": "同僚との関係は良好",
            "evaluation_system": None,
            "promotion_treatment": "昇進機会あり"
        }

        created_at = datetime.utcnow()

        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.FORMER,
            ratings=ratings,
            comments=comments,
            individual_average=3.6,
            answered_count=4,
            created_at=created_at,
            updated_at=created_at
        )

        assert review.id == "review_123"
        assert review.company_id == "company_456"
        assert review.user_id == "user_789"
        assert review.employment_status == EmploymentStatus.FORMER
        assert review.ratings == ratings
        assert review.comments == comments
        assert review.individual_average == 3.6
        assert review.answered_count == 4
        assert review.is_active is True

    def test_review_from_dict(self):
        """辞書からReviewオブジェクトを作成できる"""
        data = {
            "_id": "review_123",
            "company_id": "company_456",
            "user_id": "user_789",
            "employment_status": "current",
            "ratings": {
                "recommendation": 5,
                "foreign_support": 4,
                "company_culture": 3,
                "employee_relations": 4,
                "evaluation_system": 3,
                "promotion_treatment": 4
            },
            "comments": {
                "recommendation": "素晴らしい会社",
                "foreign_support": "サポート充実",
                "company_culture": "良い風土",
                "employee_relations": "良好",
                "evaluation_system": "公平",
                "promotion_treatment": "適切"
            },
            "individual_average": 3.8,
            "answered_count": 6,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
            "is_active": True
        }

        review = Review.from_dict(data)

        assert review.id == "review_123"
        assert review.employment_status == EmploymentStatus.CURRENT
        assert review.ratings["recommendation"] == 5
        assert review.comments["recommendation"] == "素晴らしい会社"

    def test_review_to_dict(self):
        """Reviewオブジェクトを辞書に変換できる"""
        review = Review(
            id="review_123",
            company_id="company_456",
            user_id="user_789",
            employment_status=EmploymentStatus.FORMER,
            ratings={"recommendation": 4},
            comments={"recommendation": "良い"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1)
        )

        result = review.to_dict()

        assert result["company_id"] == "company_456"
        assert result["employment_status"] == "former"
        assert result["ratings"]["recommendation"] == 4
        assert result["individual_average"] == 4.0

    def test_calculate_individual_average(self):
        """個別レビュー平均点を正しく計算できる"""
        ratings = {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": None,  # 回答しない
            "employee_relations": 5,
            "evaluation_system": 2,
            "promotion_treatment": None  # 回答しない
        }

        average, count = Review.calculate_individual_average(ratings)

        # (4+3+5+2)/4 = 3.5
        assert average == 3.5
        assert count == 4

    def test_calculate_individual_average_no_answers(self):
        """全て回答しない場合の平均点計算"""
        ratings = {
            "recommendation": None,
            "foreign_support": None,
            "company_culture": None,
            "employee_relations": None,
            "evaluation_system": None,
            "promotion_treatment": None
        }

        average, count = Review.calculate_individual_average(ratings)

        assert average == 0.0
        assert count == 0

    def test_review_category_enum(self):
        """ReviewCategoryEnumが正しく定義されている"""
        assert ReviewCategory.RECOMMENDATION.value == "recommendation"
        assert ReviewCategory.FOREIGN_SUPPORT.value == "foreign_support"
        assert ReviewCategory.COMPANY_CULTURE.value == "company_culture"
        assert ReviewCategory.EMPLOYEE_RELATIONS.value == "employee_relations"
        assert ReviewCategory.EVALUATION_SYSTEM.value == "evaluation_system"
        assert ReviewCategory.PROMOTION_TREATMENT.value == "promotion_treatment"

    def test_employment_status_enum(self):
        """EmploymentStatusEnumが正しく定義されている"""
        assert EmploymentStatus.CURRENT.value == "current"
        assert EmploymentStatus.FORMER.value == "former"


class TestReviewSummary:
    """ReviewSummaryモデルのテスト"""

    def test_review_summary_creation(self):
        """ReviewSummaryを作成できる"""
        category_averages = {
            "recommendation": 3.5,
            "foreign_support": 2.8,
            "company_culture": 3.1,
            "employee_relations": 3.4,
            "evaluation_system": 3.0,
            "promotion_treatment": 2.9
        }

        summary = ReviewSummary(
            total_reviews=15,
            overall_average=3.2,
            category_averages=category_averages,
            last_updated=datetime(2024, 1, 1)
        )

        assert summary.total_reviews == 15
        assert summary.overall_average == 3.2
        assert summary.category_averages["recommendation"] == 3.5
        assert summary.last_updated == datetime(2024, 1, 1)

    def test_review_summary_from_dict(self):
        """辞書からReviewSummaryオブジェクトを作成できる"""
        data = {
            "total_reviews": 10,
            "overall_average": 4.0,
            "category_averages": {
                "recommendation": 4.2,
                "foreign_support": 3.8
            },
            "last_updated": datetime(2024, 2, 1)
        }

        summary = ReviewSummary.from_dict(data)

        assert summary.total_reviews == 10
        assert summary.overall_average == 4.0
        assert summary.category_averages["recommendation"] == 4.2

    def test_review_summary_to_dict(self):
        """ReviewSummaryオブジェクトを辞書に変換できる"""
        summary = ReviewSummary(
            total_reviews=5,
            overall_average=3.0,
            category_averages={"recommendation": 3.0},
            last_updated=datetime(2024, 1, 1)
        )

        result = summary.to_dict()

        assert result["total_reviews"] == 5
        assert result["overall_average"] == 3.0
        assert result["category_averages"]["recommendation"] == 3.0
        assert result["last_updated"] == datetime(2024, 1, 1)