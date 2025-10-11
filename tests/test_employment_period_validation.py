"""
雇用期間バリデーションのユニットテスト

TDD RED フェーズ: 雇用期間バリデーションの期待される動作を定義
"""

import pytest
from src.services.review_submission_service import ReviewSubmissionService
from datetime import datetime


class TestEmploymentPeriodValidation:
    """雇用期間バリデーションのテストクラス"""

    def test_validate_current_employee(self):
        """
        test_validate_current_employee(): 現従業員は終了年なしで有効
        Requirements: 6.1, 6.2, 7.7
        """
        review_data = {
            "employment_status": "current",
            "employment_period": {
                "start_year": 2020,
                "end_year": None,  # 現従業員なので終了年なし
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        # バリデーションメソッドを呼び出し
        errors = ReviewSubmissionService.validate_employment_period(review_data)

        # エラーなしを期待
        assert len(errors) == 0

    def test_validate_current_employee_with_end_year_present(self):
        """
        現従業員で終了年が「present」の場合も有効
        Requirements: 6.1
        """
        review_data = {
            "employment_status": "current",
            "employment_period": {
                "start_year": 2020,
                "end_year": "present",  # 「現在」を示す特別な値
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) == 0

    def test_validate_former_employee_valid(self):
        """
        test_validate_former_employee_valid(): 元従業員は開始年 <= 終了年で有効
        Requirements: 7.6
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": 2018,
                "end_year": 2022,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) == 0

    def test_validate_former_employee_same_year(self):
        """
        元従業員で開始年と終了年が同じ場合（1年未満の勤務）も有効
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": 2022,
                "end_year": 2022,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) == 0

    def test_validate_former_employee_invalid(self):
        """
        test_validate_former_employee_invalid(): 開始年 > 終了年でバリデーションエラー
        Requirements: 7.6
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": 2023,
                "end_year": 2020,  # 開始年 > 終了年
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) > 0
        assert any("開始年は終了年より前" in err for err in errors)

    def test_validate_missing_end_year_for_former(self):
        """
        test_validate_missing_end_year_for_former(): 元従業員で終了年なしはエラー
        Requirements: 7.2, 7.3
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": 2020,
                "end_year": None,  # 元従業員なのに終了年がない
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) > 0
        assert any("雇用終了年を入力してください" in err for err in errors)

    def test_validate_missing_start_year(self):
        """
        開始年が未入力の場合はエラー
        Requirements: 7.1
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": None,  # 開始年がない
                "end_year": 2022,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) > 0
        assert any("雇用開始年を入力してください" in err for err in errors)

    def test_validate_missing_start_year_current_employee(self):
        """
        現従業員でも開始年は必須
        Requirements: 7.7
        """
        review_data = {
            "employment_status": "current",
            "employment_period": {
                "start_year": None,  # 開始年がない
                "end_year": None,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) > 0
        assert any("雇用開始年を入力してください" in err for err in errors)

    def test_validate_both_missing_for_former(self):
        """
        元従業員で開始年と終了年の両方が未入力の場合は両方エラー
        Requirements: 7.3
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": None,
                "end_year": None,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) >= 2
        assert any("雇用開始年を入力してください" in err for err in errors)
        assert any("雇用終了年を入力してください" in err for err in errors)

    def test_validate_future_year(self):
        """
        未来の年は無効（現在年より後）
        """
        current_year = datetime.now().year
        review_data = {
            "employment_status": "current",
            "employment_period": {
                "start_year": current_year + 5,  # 未来の年
                "end_year": None,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) > 0
        assert any("未来の年は入力できません" in err for err in errors)

    def test_validate_year_too_old(self):
        """
        1970年より前の年は無効
        """
        review_data = {
            "employment_status": "former",
            "employment_period": {
                "start_year": 1969,  # 1970年より前
                "end_year": 2000,
            },
            "ratings": {"recommendation": 4},
            "comments": {},
            "company_id": "test_company_id",
            "user_id": "test_user_id",
        }

        errors = ReviewSubmissionService.validate_employment_period(review_data)

        assert len(errors) > 0
        assert any("1970年以降の年を入力してください" in err for err in errors)
