"""
レビューオブジェクト匿名化機能のテスト
"""
import pytest
from datetime import datetime
from src.services.review_anonymization_service import ReviewAnonymizationService
from src.models.review import Review, EmploymentStatus, EmploymentPeriod


class TestReviewObjectAnonymization:
    """レビューオブジェクト匿名化機能のテストクラス"""

    @pytest.fixture
    def service(self):
        """匿名化サービスのインスタンスを提供"""
        return ReviewAnonymizationService()

    @pytest.fixture
    def sample_review(self):
        """テスト用のサンプルレビューを提供"""
        return Review(
            id="review123",
            company_id="company456",
            user_id="user789",
            employment_status=EmploymentStatus.CURRENT,
            employment_period=EmploymentPeriod(start_year=2020, end_year=None),
            ratings={
                "recommendation": 4,
                "foreign_support": 5,
                "company_culture": 3,
                "employee_relations": 4,
                "evaluation_system": None,
                "promotion_treatment": 4
            },
            comments={
                "recommendation": "Great company to work for!",
                "foreign_support": "Excellent support for foreigners",
                "company_culture": "Nice culture",
                "employee_relations": "Good relationships",
                "evaluation_system": None,
                "promotion_treatment": "Fair promotion system"
            },
            individual_average=4.0,
            answered_count=5,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
            is_active=True,
            language="en"
        )

    def test_anonymize_review_basic_structure(self, service, sample_review):
        """匿名化されたレビューが正しい辞書構造を持つことを確認"""
        result = service.anonymize_review(sample_review)

        # 基本的なキーが存在することを確認
        assert "id" in result
        assert "company_id" in result
        assert "anonymized_user" in result
        assert "employment_status" in result
        assert "employment_period" in result
        assert "ratings" in result
        assert "comments" in result
        assert "individual_average" in result
        assert "answered_count" in result
        assert "created_at" in result
        assert "is_active" in result

    def test_anonymize_review_user_anonymization(self, service, sample_review):
        """ユーザーIDが正しく匿名化されることを確認"""
        result = service.anonymize_review(sample_review)

        # user_idが含まれていないことを確認
        assert "user_id" not in result

        # anonymized_userが「ユーザー[A-Z]」形式であることを確認
        assert result["anonymized_user"].startswith("ユーザー")
        assert len(result["anonymized_user"]) == 5
        last_char = result["anonymized_user"][-1]
        assert last_char.isalpha() and last_char.isupper()

    def test_anonymize_review_preserves_other_data(self, service, sample_review):
        """匿名化以外のデータが正しく保持されることを確認"""
        result = service.anonymize_review(sample_review)

        # IDとcompany_idが保持されることを確認
        assert result["id"] == sample_review.id
        assert result["company_id"] == sample_review.company_id

        # 在籍状況が保持されることを確認
        assert result["employment_status"] == sample_review.employment_status.value

        # 評価スコアが保持されることを確認
        assert result["ratings"] == sample_review.ratings

        # コメントが保持されることを確認
        assert result["comments"] == sample_review.comments

        # 平均評価が保持されることを確認
        assert result["individual_average"] == sample_review.individual_average

        # 回答数が保持されることを確認
        assert result["answered_count"] == sample_review.answered_count

    def test_anonymize_review_employment_period_with_end_year(self, service):
        """終了年がある勤務期間が正しく処理されることを確認"""
        review = Review(
            id="review123",
            company_id="company456",
            user_id="user789",
            employment_status=EmploymentStatus.FORMER,
            employment_period=EmploymentPeriod(start_year=2018, end_year=2022),
            ratings={"recommendation": 4},
            comments={"recommendation": "Good"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

        result = service.anonymize_review(review)

        assert result["employment_period"]["start_year"] == 2018
        assert result["employment_period"]["end_year"] == 2022
        assert result["employment_period"]["display"] == "2018年〜2022年"

    def test_anonymize_review_employment_period_current(self, service):
        """現在勤務中の勤務期間が正しく処理されることを確認"""
        review = Review(
            id="review123",
            company_id="company456",
            user_id="user789",
            employment_status=EmploymentStatus.CURRENT,
            employment_period=EmploymentPeriod(start_year=2020, end_year=None),
            ratings={"recommendation": 5},
            comments={"recommendation": "Excellent"},
            individual_average=5.0,
            answered_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

        result = service.anonymize_review(review)

        assert result["employment_period"]["start_year"] == 2020
        assert result["employment_period"]["end_year"] is None
        assert result["employment_period"]["display"] == "2020年〜現在"

    def test_anonymize_review_without_employment_period(self, service):
        """勤務期間が未設定のレビューが正しく処理されることを確認"""
        review = Review(
            id="review123",
            company_id="company456",
            user_id="user789",
            employment_status=EmploymentStatus.CURRENT,
            employment_period=None,
            ratings={"recommendation": 3},
            comments={"recommendation": "OK"},
            individual_average=3.0,
            answered_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

        result = service.anonymize_review(review)

        assert result["employment_period"] is None

    def test_anonymize_review_with_preview_mode(self, service, sample_review):
        """プレビューモードでコメントがマスキングされることを確認"""
        result = service.anonymize_review(sample_review, preview_mode=True)

        # コメントが「***」でマスキングされることを確認
        for key, value in result["comments"].items():
            if sample_review.comments[key] is not None:
                assert result["comments"][key] == "***"
            else:
                assert result["comments"][key] is None

        # 評価スコアは保持されることを確認
        assert result["ratings"] == sample_review.ratings

    def test_anonymize_review_with_full_access_mode(self, service, sample_review):
        """フルアクセスモードでコメントが保持されることを確認"""
        result = service.anonymize_review(sample_review, preview_mode=False)

        # コメントが元のまま保持されることを確認
        assert result["comments"] == sample_review.comments

    def test_anonymize_review_consistency(self, service, sample_review):
        """同じレビューを複数回匿名化しても一貫した結果を得ることを確認"""
        result1 = service.anonymize_review(sample_review)
        result2 = service.anonymize_review(sample_review)

        # 匿名化ユーザー名が一致することを確認
        assert result1["anonymized_user"] == result2["anonymized_user"]

        # その他のデータも一致することを確認
        assert result1 == result2

    def test_anonymize_review_datetime_format(self, service, sample_review):
        """日時が適切な形式で返されることを確認"""
        result = service.anonymize_review(sample_review)

        # created_atとupdated_atがdatetimeオブジェクトであることを確認
        assert isinstance(result["created_at"], datetime)
        assert result["created_at"] == sample_review.created_at

    def test_anonymize_review_multilingual_comments(self, service):
        """多言語コメントが正しく処理されることを確認"""
        review = Review(
            id="review123",
            company_id="company456",
            user_id="user789",
            employment_status=EmploymentStatus.CURRENT,
            employment_period=EmploymentPeriod(start_year=2020, end_year=None),
            ratings={"recommendation": 4},
            comments={"recommendation": "Great company"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            language="en",
            comments_ja={"recommendation": "素晴らしい会社"},
            comments_zh={"recommendation": "很棒的公司"},
            comments_en={"recommendation": "Great company"}
        )

        result = service.anonymize_review(review)

        # 多言語コメントが含まれることを確認
        assert "language" in result
        assert result["language"] == "en"
        assert "comments_ja" in result
        assert result["comments_ja"]["recommendation"] == "素晴らしい会社"
        assert "comments_zh" in result
        assert result["comments_zh"]["recommendation"] == "很棒的公司"
        assert "comments_en" in result
        assert result["comments_en"]["recommendation"] == "Great company"

    def test_anonymize_review_preview_mode_multilingual(self, service):
        """プレビューモードで多言語コメントもマスキングされることを確認"""
        review = Review(
            id="review123",
            company_id="company456",
            user_id="user789",
            employment_status=EmploymentStatus.CURRENT,
            ratings={"recommendation": 4},
            comments={"recommendation": "Great"},
            individual_average=4.0,
            answered_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            language="en",
            comments_ja={"recommendation": "素晴らしい"},
            comments_zh={"recommendation": "很棒"},
            comments_en={"recommendation": "Great"}
        )

        result = service.anonymize_review(review, preview_mode=True)

        # 全ての言語のコメントがマスキングされることを確認
        assert result["comments"]["recommendation"] == "***"
        assert result["comments_ja"]["recommendation"] == "***"
        assert result["comments_zh"]["recommendation"] == "***"
        assert result["comments_en"]["recommendation"] == "***"
