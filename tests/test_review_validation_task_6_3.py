"""
Test: Review Validation (Task 6.3)

レビューバリデーションの包括的テスト:
- 各レーティングフィールドの1～5範囲チェック
- コメント欄の最大文字数チェック（カテゴリーコメント500文字、総合コメント1000文字）
- overall_nps の0～10範囲チェック
- employment_status、tenure、job_category の enum値チェック

Requirements: 11.1～11.12
"""
import pytest
from datetime import datetime
from src.models.review import Review, EmploymentStatus, TenureEnum, JobCategory


def make_base_review(**kwargs):
    """テスト用のベースレビューデータを作成するヘルパー"""
    base = {
        'id': 'test-id',
        'company_id': 'test-company',
        'user_id': 'test-user',
        'employment_status': 'current',
        'ratings': {},
        'comments': {},
        'individual_average': 0.0,
        'answered_count': 0,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'is_active': True,
    }
    base.update(kwargs)
    return base


class TestRatingFieldValidation:
    """各レーティングフィールドの1～5範囲チェック"""

    # --- 有効な値（1〜5）のテスト ---

    @pytest.mark.parametrize("field,value", [
        ('comp_salary', 1),
        ('comp_salary', 3),
        ('comp_salary', 5),
        ('comp_bonus', 1),
        ('comp_benefits', 5),
        ('wlb_hours', 1),
        ('wlb_vacation', 5),
        ('wlb_flexibility', 3),
        ('wlb_overall', 4),
        ('culture_atmosphere', 2),
        ('culture_diversity', 5),
        ('culture_ethics', 1),
        ('culture_communication', 3),
        ('career_growth', 4),
        ('career_training', 2),
        ('career_path', 5),
        ('career_mentorship', 1),
        ('mgmt_vision', 3),
        ('mgmt_decision', 4),
        ('mgmt_structure', 2),
        ('mgmt_manager', 5),
        ('perf_fairness', 1),
        ('perf_feedback', 3),
        ('perf_promotion', 5),
        ('perf_linkage', 4),
        ('env_office', 2),
        ('env_relationships', 5),
        ('env_stress', 1),
        ('env_health', 3),
        ('biz_future', 4),
        ('biz_pride', 5),
        ('biz_social_impact', 2),
        ('biz_financial', 3),
        ('overall_satisfaction', 1),
        ('overall_satisfaction', 5),
    ])
    def test_valid_rating_values(self, field, value):
        """有効な1〜5の評価値を受け入れること"""
        data = make_base_review(**{field: value})
        review = Review(**data)
        assert getattr(review, field) == value

    # --- 無効な値（範囲外）のテスト ---

    @pytest.mark.parametrize("field", [
        'comp_salary', 'comp_bonus', 'comp_benefits',
        'wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall',
        'culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication',
        'career_growth', 'career_training', 'career_path', 'career_mentorship',
        'mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager',
        'perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage',
        'env_office', 'env_relationships', 'env_stress', 'env_health',
        'biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial',
        'overall_satisfaction',
    ])
    def test_rating_below_minimum_raises_error(self, field):
        """評価値が1未満の場合はValueErrorが発生すること"""
        data = make_base_review(**{field: 0})
        with pytest.raises(ValueError, match=f"{field}"):
            Review(**data)

    @pytest.mark.parametrize("field", [
        'comp_salary', 'comp_bonus', 'comp_benefits',
        'wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall',
        'culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication',
        'career_growth', 'career_training', 'career_path', 'career_mentorship',
        'mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager',
        'perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage',
        'env_office', 'env_relationships', 'env_stress', 'env_health',
        'biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial',
        'overall_satisfaction',
    ])
    def test_rating_above_maximum_raises_error(self, field):
        """評価値が5超の場合はValueErrorが発生すること"""
        data = make_base_review(**{field: 6})
        with pytest.raises(ValueError, match=f"{field}"):
            Review(**data)

    def test_rating_negative_value_raises_error(self):
        """負の評価値はValueErrorが発生すること"""
        data = make_base_review(comp_salary=-1)
        with pytest.raises(ValueError):
            Review(**data)

    def test_none_rating_is_valid(self):
        """Noneの評価値は有効（省略可能）であること"""
        data = make_base_review(comp_salary=None)
        review = Review(**data)
        assert review.comp_salary is None

    def test_all_rating_fields_none_is_valid(self):
        """全レーティングフィールドがNoneでも有効であること"""
        data = make_base_review()
        review = Review(**data)
        # Verify all new rating fields default to None
        assert review.comp_salary is None
        assert review.overall_satisfaction is None


class TestNPSFieldValidation:
    """overall_nps の0～10範囲チェック"""

    @pytest.mark.parametrize("nps_value", [0, 1, 5, 9, 10])
    def test_valid_nps_values(self, nps_value):
        """有効な0〜10のNPS値を受け入れること"""
        data = make_base_review(overall_nps=nps_value)
        review = Review(**data)
        assert review.overall_nps == nps_value

    def test_nps_below_minimum_raises_error(self):
        """NPS値が0未満の場合はValueErrorが発生すること"""
        data = make_base_review(overall_nps=-1)
        with pytest.raises(ValueError, match="overall_nps"):
            Review(**data)

    def test_nps_above_maximum_raises_error(self):
        """NPS値が10超の場合はValueErrorが発生すること"""
        data = make_base_review(overall_nps=11)
        with pytest.raises(ValueError, match="overall_nps"):
            Review(**data)

    def test_nps_none_is_valid(self):
        """NPS値がNoneは有効（省略可能）であること"""
        data = make_base_review(overall_nps=None)
        review = Review(**data)
        assert review.overall_nps is None

    def test_nps_boundary_values(self):
        """NPS境界値（0と10）を正しく受け入れること"""
        data_min = make_base_review(overall_nps=0)
        review_min = Review(**data_min)
        assert review_min.overall_nps == 0

        data_max = make_base_review(overall_nps=10)
        review_max = Review(**data_max)
        assert review_max.overall_nps == 10


class TestCommentLengthValidation:
    """コメント欄の最大文字数チェック"""

    # --- カテゴリーコメント（最大500文字）のテスト ---

    @pytest.mark.parametrize("field", [
        'comp_comment', 'wlb_comment', 'culture_comment', 'career_comment',
        'mgmt_comment', 'perf_comment', 'env_comment', 'biz_comment',
    ])
    def test_category_comment_at_max_length_is_valid(self, field):
        """カテゴリーコメントが500文字は有効であること"""
        comment = "あ" * 500
        data = make_base_review(**{field: comment})
        review = Review(**data)
        assert getattr(review, field) == comment

    @pytest.mark.parametrize("field", [
        'comp_comment', 'wlb_comment', 'culture_comment', 'career_comment',
        'mgmt_comment', 'perf_comment', 'env_comment', 'biz_comment',
    ])
    def test_category_comment_exceeding_max_length_raises_error(self, field):
        """カテゴリーコメントが501文字超はValueErrorが発生すること"""
        comment = "あ" * 501
        data = make_base_review(**{field: comment})
        with pytest.raises(ValueError, match=f"{field}"):
            Review(**data)

    @pytest.mark.parametrize("field", [
        'comp_comment', 'wlb_comment', 'culture_comment', 'career_comment',
        'mgmt_comment', 'perf_comment', 'env_comment', 'biz_comment',
    ])
    def test_category_comment_empty_string_is_valid(self, field):
        """カテゴリーコメントが空文字列は有効であること"""
        data = make_base_review(**{field: ""})
        review = Review(**data)
        assert getattr(review, field) == ""

    @pytest.mark.parametrize("field", [
        'comp_comment', 'wlb_comment', 'culture_comment', 'career_comment',
        'mgmt_comment', 'perf_comment', 'env_comment', 'biz_comment',
    ])
    def test_category_comment_none_is_valid(self, field):
        """カテゴリーコメントがNoneは有効（省略可能）であること"""
        data = make_base_review(**{field: None})
        review = Review(**data)
        assert getattr(review, field) is None

    # --- 総合コメント（最大1000文字）のテスト ---

    def test_overall_comment_at_max_length_is_valid(self):
        """総合コメントが1000文字は有効であること"""
        comment = "あ" * 1000
        data = make_base_review(overall_comment=comment)
        review = Review(**data)
        assert review.overall_comment == comment

    def test_overall_comment_exceeding_max_length_raises_error(self):
        """総合コメントが1001文字超はValueErrorが発生すること"""
        comment = "あ" * 1001
        data = make_base_review(overall_comment=comment)
        with pytest.raises(ValueError, match="overall_comment"):
            Review(**data)

    def test_overall_comment_none_is_valid(self):
        """総合コメントがNoneは有効（省略可能）であること"""
        data = make_base_review(overall_comment=None)
        review = Review(**data)
        assert review.overall_comment is None

    def test_overall_comment_longer_limit_than_category_comment(self):
        """総合コメントはカテゴリーコメント（500文字）より長い1000文字を受け入れること"""
        comment_700 = "あ" * 700
        # カテゴリーコメントは700文字でエラー
        data_cat = make_base_review(comp_comment=comment_700)
        with pytest.raises(ValueError):
            Review(**data_cat)

        # 総合コメントは700文字でOK
        data_overall = make_base_review(overall_comment=comment_700)
        review = Review(**data_overall)
        assert len(review.overall_comment) == 700


class TestEnumFieldValidation:
    """employment_status、tenure、job_category の enum値チェック"""

    # --- tenure のテスト ---

    @pytest.mark.parametrize("tenure_value", [
        "6m_under", "6m_1y", "1y_3y", "3y_5y", "5y_over"
    ])
    def test_valid_tenure_values(self, tenure_value):
        """有効なtenure enum値を受け入れること"""
        data = make_base_review(tenure=tenure_value)
        review = Review(**data)
        assert review.tenure == tenure_value

    def test_invalid_tenure_raises_error(self):
        """無効なtenure値はValueErrorが発生すること"""
        data = make_base_review(tenure="invalid_tenure")
        with pytest.raises(ValueError, match="tenure"):
            Review(**data)

    def test_tenure_none_is_valid(self):
        """tenureがNoneは有効（省略可能）であること"""
        data = make_base_review(tenure=None)
        review = Review(**data)
        assert review.tenure is None

    def test_tenure_enum_values_match_expected(self):
        """TenureEnumの値がすべて正しい文字列に対応すること"""
        expected_values = {"6m_under", "6m_1y", "1y_3y", "3y_5y", "5y_over"}
        actual_values = {t.value for t in TenureEnum}
        assert actual_values == expected_values

    # --- job_category のテスト ---

    @pytest.mark.parametrize("category_value", [
        "engineer", "designer", "pm", "marketing", "sales", "corporate", "other"
    ])
    def test_valid_job_category_values(self, category_value):
        """有効なjob_category enum値を受け入れること"""
        data = make_base_review(job_category=category_value)
        review = Review(**data)
        assert review.job_category == category_value

    def test_invalid_job_category_raises_error(self):
        """無効なjob_category値はValueErrorが発生すること"""
        data = make_base_review(job_category="invalid_category")
        with pytest.raises(ValueError, match="job_category"):
            Review(**data)

    def test_job_category_none_is_valid(self):
        """job_categoryがNoneは有効（省略可能）であること"""
        data = make_base_review(job_category=None)
        review = Review(**data)
        assert review.job_category is None

    def test_job_category_enum_values_match_expected(self):
        """JobCategoryのEnum値がすべて正しい文字列に対応すること"""
        expected_values = {"engineer", "designer", "pm", "marketing", "sales", "corporate", "other"}
        actual_values = {c.value for c in JobCategory}
        assert actual_values == expected_values

    # --- employment_status のテスト ---

    @pytest.mark.parametrize("status", ["current", "former"])
    def test_valid_employment_status_string_values(self, status):
        """有効なemployment_status文字列値を受け入れること（直接構築時は文字列のまま保持）"""
        data = make_base_review(employment_status=status)
        review = Review(**data)
        # Direct constructor keeps the value as-is; from_dict converts to Enum
        assert review.employment_status == status

    @pytest.mark.parametrize("status", [EmploymentStatus.CURRENT, EmploymentStatus.FORMER])
    def test_valid_employment_status_enum_values(self, status):
        """有効なemployment_status enum値を受け入れること"""
        data = make_base_review(employment_status=status)
        review = Review(**data)
        assert review.employment_status == status


class TestComplexValidationScenarios:
    """複合バリデーションシナリオのテスト"""

    def test_multiple_invalid_fields_first_error_raised(self):
        """複数の無効フィールドがある場合、最初のエラーが発生すること"""
        data = make_base_review(
            comp_salary=6,   # invalid
            wlb_hours=0,     # invalid
        )
        with pytest.raises(ValueError):
            Review(**data)

    def test_valid_complete_new_schema_review(self):
        """完全な新8カテゴリースキーマのレビューが有効であること"""
        data = make_base_review(
            comp_salary=4, comp_bonus=3, comp_benefits=4, comp_equity="yes",
            comp_comment="給与は良い",
            wlb_hours=4, wlb_vacation=5, wlb_flexibility=4, wlb_overall=4,
            wlb_comment="バランス良好",
            culture_atmosphere=4, culture_diversity=3, culture_ethics=5,
            culture_communication=4, culture_comment="良い文化",
            career_growth=4, career_training=3, career_path=4,
            career_mentorship=4, career_comment="成長機会あり",
            mgmt_vision=5, mgmt_decision=4, mgmt_structure=3,
            mgmt_manager=4, mgmt_comment="良い経営",
            perf_fairness=4, perf_feedback=4, perf_promotion=3,
            perf_linkage=4, perf_comment="公平な評価",
            env_office=4, env_relationships=5, env_stress=3,
            env_health=4, env_comment="快適な環境",
            biz_future=5, biz_pride=5, biz_social_impact=4,
            biz_financial=4, biz_comment="将来性あり",
            overall_satisfaction=5,
            overall_nps=9,
            tenure="3y_5y",
            job_category="engineer",
            overall_comment="総合的に素晴らしい職場"
        )
        review = Review(**data)
        assert review.comp_salary == 4
        assert review.overall_nps == 9
        assert review.tenure == "3y_5y"
        assert review.job_category == "engineer"

    def test_rating_non_integer_type_raises_error(self):
        """レーティングフィールドに整数以外の型はValueErrorが発生すること"""
        data = make_base_review(comp_salary=3.5)  # float not int
        with pytest.raises(ValueError):
            Review(**data)

    def test_rating_string_value_raises_error(self):
        """レーティングフィールドに文字列はValueErrorが発生すること"""
        data = make_base_review(comp_salary="5")  # string "5" not int 5
        with pytest.raises(ValueError):
            Review(**data)

    def test_comment_non_string_type_raises_error(self):
        """コメントフィールドに文字列以外はValueErrorが発生すること"""
        data = make_base_review(comp_comment=12345)  # int not string
        with pytest.raises(ValueError):
            Review(**data)

    def test_nps_non_integer_type_raises_error(self):
        """overall_npsに整数以外の型はValueErrorが発生すること"""
        data = make_base_review(overall_nps=7.5)  # float not int
        with pytest.raises(ValueError):
            Review(**data)

    def test_backward_compatible_review_passes_validation(self):
        """後方互換性のある旧スキーマレビューがバリデーションを通過すること"""
        data = {
            'id': 'legacy-id',
            'company_id': 'company-1',
            'user_id': 'user-1',
            'employment_status': EmploymentStatus.CURRENT,
            'ratings': {
                'recommendation': 5,
                'foreign_support': 4,
                'company_culture': 5,
                'employee_relations': 4,
                'evaluation_system': 4,
                'promotion_treatment': 4
            },
            'comments': {'recommendation': 'おすすめ'},
            'individual_average': 4.3,
            'answered_count': 6,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'is_active': True,
        }
        review = Review(**data)
        assert review.id == 'legacy-id'
        # No new fields set
        assert review.comp_salary is None
        assert review.overall_nps is None
