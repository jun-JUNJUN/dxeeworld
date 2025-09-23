"""
企業モデルのレビュー機能拡張テスト
"""
import pytest
from datetime import datetime
from src.models.company import Company, IndustryType, CompanySize
from src.models.review import ReviewSummary


class TestCompanyReviewExtension:
    """Company モデルのレビュー機能拡張テスト"""

    def test_company_with_review_summary(self):
        """レビューサマリー付きの企業モデルを作成できる"""
        review_summary = ReviewSummary(
            total_reviews=15,
            overall_average=3.2,
            category_averages={
                "recommendation": 3.5,
                "foreign_support": 2.8,
                "company_culture": 3.1,
                "employee_relations": 3.4,
                "evaluation_system": 3.0,
                "promotion_treatment": 2.9
            },
            last_updated=datetime(2024, 1, 1)
        )

        company = Company(
            id="company_123",
            name="株式会社サンプル",
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.MEDIUM,
            country="Japan",
            location="東京都",
            description="テスト企業",
            review_summary=review_summary
        )

        assert company.review_summary is not None
        assert company.review_summary.total_reviews == 15
        assert company.review_summary.overall_average == 3.2
        assert company.review_summary.category_averages["recommendation"] == 3.5

    def test_company_without_review_summary(self):
        """レビューサマリーなしの企業モデルを作成できる"""
        company = Company(
            id="company_456",
            name="株式会社テスト",
            industry=IndustryType.FINANCE,
            size=CompanySize.LARGE,
            country="Japan"
        )

        assert company.review_summary is None

    def test_company_from_dict_with_review_summary(self):
        """レビューサマリー付きの辞書からCompanyオブジェクトを作成できる"""
        data = {
            "_id": "company_789",
            "name": "株式会社データ",
            "industry": "technology",
            "size": "medium",
            "country": "Japan",
            "location": "大阪府",
            "review_summary": {
                "total_reviews": 8,
                "overall_average": 4.1,
                "category_averages": {
                    "recommendation": 4.2,
                    "foreign_support": 4.0,
                    "company_culture": 4.1,
                    "employee_relations": 4.3,
                    "evaluation_system": 3.9,
                    "promotion_treatment": 4.0
                },
                "last_updated": datetime(2024, 2, 1)
            }
        }

        company = Company.from_dict(data)

        assert company.id == "company_789"
        assert company.review_summary is not None
        assert company.review_summary.total_reviews == 8
        assert company.review_summary.overall_average == 4.1

    def test_company_from_dict_without_review_summary(self):
        """レビューサマリーなしの辞書からCompanyオブジェクトを作成できる"""
        data = {
            "_id": "company_999",
            "name": "株式会社ノーレビュー",
            "industry": "construction",
            "size": "small",
            "country": "Japan"
        }

        company = Company.from_dict(data)

        assert company.id == "company_999"
        assert company.review_summary is None

    def test_company_to_dict_with_review_summary(self):
        """レビューサマリー付きのCompanyオブジェクトを辞書に変換できる"""
        review_summary = ReviewSummary(
            total_reviews=5,
            overall_average=3.5,
            category_averages={"recommendation": 3.5},
            last_updated=datetime(2024, 1, 15)
        )

        company = Company(
            id="company_dict",
            name="辞書テスト会社",
            industry=IndustryType.HEALTHCARE,
            size=CompanySize.STARTUP,
            country="Japan",
            review_summary=review_summary
        )

        result = company.to_dict()

        assert "review_summary" in result
        assert result["review_summary"]["total_reviews"] == 5
        assert result["review_summary"]["overall_average"] == 3.5
        assert result["review_summary"]["category_averages"]["recommendation"] == 3.5

    def test_company_to_dict_without_review_summary(self):
        """レビューサマリーなしのCompanyオブジェクトを辞書に変換できる"""
        company = Company(
            id="company_no_review",
            name="レビューなし会社",
            industry=IndustryType.RETAIL,
            size=CompanySize.MEDIUM,
            country="Japan"
        )

        result = company.to_dict()

        assert result.get("review_summary") is None

    def test_company_update_review_summary(self):
        """企業のレビューサマリーを更新できる"""
        company = Company(
            id="company_update",
            name="更新テスト会社",
            industry=IndustryType.EDUCATION,
            size=CompanySize.LARGE,
            country="Japan"
        )

        # 初期状態ではレビューサマリーなし
        assert company.review_summary is None

        # レビューサマリーを追加
        new_summary = ReviewSummary(
            total_reviews=3,
            overall_average=4.0,
            category_averages={"recommendation": 4.0},
            last_updated=datetime.utcnow()
        )

        company.review_summary = new_summary

        assert company.review_summary is not None
        assert company.review_summary.total_reviews == 3
        assert company.review_summary.overall_average == 4.0

    def test_company_zero_reviews_summary(self):
        """レビューが0件の企業サマリーを作成できる"""
        zero_summary = ReviewSummary(
            total_reviews=0,
            overall_average=0.0,
            category_averages={
                "recommendation": 0.0,
                "foreign_support": 0.0,
                "company_culture": 0.0,
                "employee_relations": 0.0,
                "evaluation_system": 0.0,
                "promotion_treatment": 0.0
            },
            last_updated=datetime.utcnow()
        )

        company = Company(
            id="company_zero",
            name="レビュー0件会社",
            industry=IndustryType.MEDIA,
            size=CompanySize.SMALL,
            country="Japan",
            review_summary=zero_summary
        )

        assert company.review_summary.total_reviews == 0
        assert company.review_summary.overall_average == 0.0
        assert all(avg == 0.0 for avg in company.review_summary.category_averages.values())