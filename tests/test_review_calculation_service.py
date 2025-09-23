"""
レビュー計算ロジックサービスのテスト
"""
import pytest
from datetime import datetime
from src.services.review_calculation_service import ReviewCalculationService
from src.models.review import Review, ReviewCategory, EmploymentStatus


class TestReviewCalculationService:
    """ReviewCalculationServiceのテスト"""

    def setup_method(self):
        """各テスト前の準備"""
        self.calc_service = ReviewCalculationService()

    def test_calculate_individual_average_all_answered(self):
        """全項目に回答した場合の個別平均点計算"""
        ratings = {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": 5,
            "employee_relations": 2,
            "evaluation_system": 4,
            "promotion_treatment": 3
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        # (4+3+5+2+4+3)/6 = 3.5
        assert average == 3.5
        assert count == 6

    def test_calculate_individual_average_partial_answers(self):
        """一部項目のみ回答した場合の個別平均点計算"""
        ratings = {
            "recommendation": 4,
            "foreign_support": None,  # 回答しない
            "company_culture": 2,
            "employee_relations": None,  # 回答しない
            "evaluation_system": 5,
            "promotion_treatment": None  # 回答しない
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        # (4+2+5)/3 = 3.67 → 3.7 (小数第1位まで四捨五入)
        assert average == 3.7
        assert count == 3

    def test_calculate_individual_average_no_answers(self):
        """全項目未回答の場合の個別平均点計算"""
        ratings = {
            "recommendation": None,
            "foreign_support": None,
            "company_culture": None,
            "employee_relations": None,
            "evaluation_system": None,
            "promotion_treatment": None
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        assert average == 0.0
        assert count == 0

    def test_calculate_individual_average_single_answer(self):
        """1項目のみ回答した場合の個別平均点計算"""
        ratings = {
            "recommendation": 5,
            "foreign_support": None,
            "company_culture": None,
            "employee_relations": None,
            "evaluation_system": None,
            "promotion_treatment": None
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        assert average == 5.0
        assert count == 1

    def test_calculate_individual_average_edge_values(self):
        """境界値（最低・最高評価）での個別平均点計算"""
        ratings = {
            "recommendation": 1,  # 最低評価
            "foreign_support": 5,  # 最高評価
            "company_culture": None,
            "employee_relations": None,
            "evaluation_system": None,
            "promotion_treatment": None
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        # (1+5)/2 = 3.0
        assert average == 3.0
        assert count == 2

    def test_calculate_individual_average_rounding_up(self):
        """四捨五入（切り上げ）のテスト"""
        ratings = {
            "recommendation": 3,
            "foreign_support": 4,
            "company_culture": None,
            "employee_relations": None,
            "evaluation_system": None,
            "promotion_treatment": None
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        # (3+4)/2 = 3.5 (そのまま)
        assert average == 3.5
        assert count == 2

    def test_calculate_individual_average_rounding_down(self):
        """四捨五入（切り捨て）のテスト"""
        ratings = {
            "recommendation": 2,
            "foreign_support": 2,
            "company_culture": 3,
            "employee_relations": None,
            "evaluation_system": None,
            "promotion_treatment": None
        }

        average, count = self.calc_service.calculate_individual_average(ratings)

        # (2+2+3)/3 = 2.33... → 2.3
        assert average == 2.3
        assert count == 3

    def test_validate_rating_values_valid(self):
        """有効な評価値のバリデーション"""
        ratings = {
            "recommendation": 1,
            "foreign_support": 3,
            "company_culture": 5,
            "employee_relations": None
        }

        errors = self.calc_service.validate_rating_values(ratings)
        assert len(errors) == 0

    def test_validate_rating_values_invalid_range(self):
        """無効な範囲の評価値のバリデーション"""
        ratings = {
            "recommendation": 0,  # 範囲外（下限）
            "foreign_support": 6,  # 範囲外（上限）
            "company_culture": 3,  # 正常
            "employee_relations": None  # 正常（未回答）
        }

        errors = self.calc_service.validate_rating_values(ratings)
        assert len(errors) == 2
        assert "recommendation" in str(errors)
        assert "foreign_support" in str(errors)

    def test_validate_rating_values_invalid_type(self):
        """無効な型の評価値のバリデーション"""
        ratings = {
            "recommendation": "4",  # 文字列
            "foreign_support": 3.5,  # 小数
            "company_culture": True,  # 真偽値
            "employee_relations": None  # 正常（未回答）
        }

        errors = self.calc_service.validate_rating_values(ratings)
        assert len(errors) == 3

    def test_validate_required_categories(self):
        """必須カテゴリーの存在確認"""
        ratings = {
            "recommendation": 4,
            "foreign_support": 3,
            # company_culture が存在しない
            "employee_relations": 5,
            "evaluation_system": 2,
            "promotion_treatment": 4
        }

        errors = self.calc_service.validate_required_categories(ratings)
        assert len(errors) == 1
        assert "company_culture" in str(errors)

    def test_validate_required_categories_all_present(self):
        """全必須カテゴリーが存在する場合"""
        ratings = {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": None,  # 未回答でもキーは存在
            "employee_relations": 5,
            "evaluation_system": 2,
            "promotion_treatment": 4
        }

        errors = self.calc_service.validate_required_categories(ratings)
        assert len(errors) == 0