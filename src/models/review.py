"""
レビューデータモデル
"""
from dataclasses import dataclass
from typing import Optional, Dict, Union
from datetime import datetime
from enum import Enum


class EmploymentStatus(Enum):
    """在職状況"""
    CURRENT = "current"
    FORMER = "former"


class TenureEnum(Enum):
    """在籍期間カテゴリー"""
    SIX_MONTHS_UNDER = "6m_under"
    SIX_MONTHS_ONE_YEAR = "6m_1y"
    ONE_YEAR_THREE_YEARS = "1y_3y"
    THREE_YEARS_FIVE_YEARS = "3y_5y"
    FIVE_YEARS_OVER = "5y_over"


class JobCategory(Enum):
    """職種カテゴリー"""
    ENGINEER = "engineer"
    DESIGNER = "designer"
    PRODUCT_MANAGER = "pm"
    MARKETING = "marketing"
    SALES = "sales"
    CORPORATE = "corporate"
    OTHER = "other"


class ReviewCategory(Enum):
    """レビュー評価カテゴリー"""
    RECOMMENDATION = "recommendation"
    FOREIGN_SUPPORT = "foreign_support"
    COMPANY_CULTURE = "company_culture"
    EMPLOYEE_RELATIONS = "employee_relations"
    EVALUATION_SYSTEM = "evaluation_system"
    PROMOTION_TREATMENT = "promotion_treatment"


@dataclass
class EmploymentPeriod:
    """勤務期間データ"""
    start_year: int
    end_year: Optional[int]  # None = 現在勤務中

    def __post_init__(self):
        """データ検証"""
        current_year = datetime.now().year

        # 開始年のバリデーション
        if not isinstance(self.start_year, int) or self.start_year < 1970 or self.start_year > current_year:
            raise ValueError(f"開始年は1970年から{current_year}年の間で指定してください")

        # 終了年のバリデーション
        if self.end_year is not None:
            if not isinstance(self.end_year, int) or self.end_year < 1970 or self.end_year > current_year:
                raise ValueError(f"終了年は1970年から{current_year}年の間で指定してください")
            if self.end_year < self.start_year:
                raise ValueError("終了年は開始年以降の年を指定してください")

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'start_year': self.start_year,
            'end_year': self.end_year
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EmploymentPeriod':
        """辞書からEmploymentPeriodオブジェクトを作成"""
        return cls(
            start_year=data['start_year'],
            end_year=data.get('end_year')
        )

    def get_display_string(self) -> str:
        """表示用文字列を取得"""
        if self.end_year is None:
            return f"{self.start_year}年〜現在"
        else:
            return f"{self.start_year}年〜{self.end_year}年"


@dataclass
class Review:
    """レビューデータモデル

    支援レガシースキーマ（6カテゴリー）と新規8カテゴリースキーマの両方をサポート
    後方互換性のためにレガシーフィールドを保持
    """

    # Core fields (always required)
    id: str
    company_id: str
    user_id: str
    employment_status: EmploymentStatus
    ratings: Dict[str, Optional[int]]  # Legacy 6-category ratings (backward compatibility)
    comments: Dict[str, Optional[str]]  # Legacy comments (backward compatibility)
    individual_average: float
    answered_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    # Existing multilingual and period fields
    employment_period: Optional[EmploymentPeriod] = None
    language: str = "ja"  # en, ja, zh
    comments_ja: Optional[Dict[str, Optional[str]]] = None
    comments_zh: Optional[Dict[str, Optional[str]]] = None
    comments_en: Optional[Dict[str, Optional[str]]] = None

    # ===== NEW 8-CATEGORY FIELDS (MECE principle) =====

    # Category 1: 待遇・報酬 (Compensation & Benefits)
    comp_salary: Optional[int] = None  # 1-5, 給与水準
    comp_bonus: Optional[int] = None  # 1-5, 賞与・インセンティブ
    comp_benefits: Optional[int] = None  # 1-5, 福利厚生
    comp_equity: Optional[str] = None  # yes/no/maybe text, ストックオプション
    comp_comment: Optional[str] = None  # max 500 chars

    # Category 2: ワークライフバランス (Work-Life Balance)
    wlb_hours: Optional[int] = None  # 1-5, 労働時間
    wlb_vacation: Optional[int] = None  # 1-5, 休暇取得
    wlb_flexibility: Optional[int] = None  # 1-5, 柔軟な働き方
    wlb_overall: Optional[int] = None  # 1-5, 総合評価
    wlb_comment: Optional[str] = None  # max 500 chars

    # Category 3: 企業文化・風土 (Company Culture)
    culture_atmosphere: Optional[int] = None  # 1-5, 社風・雰囲気
    culture_diversity: Optional[int] = None  # 1-5, 多様性・インクルージョン
    culture_ethics: Optional[int] = None  # 1-5, 倫理・コンプライアンス
    culture_communication: Optional[int] = None  # 1-5, 社内コミュニケーション
    culture_comment: Optional[str] = None  # max 500 chars

    # Category 4: キャリア・成長 (Career Development)
    career_growth: Optional[int] = None  # 1-5, 成長機会
    career_training: Optional[int] = None  # 1-5, 研修・教育制度
    career_path: Optional[int] = None  # 1-5, キャリアパス
    career_mentorship: Optional[int] = None  # 1-5, メンター制度
    career_comment: Optional[str] = None  # max 500 chars

    # Category 5: マネジメント・組織 (Management & Organization)
    mgmt_vision: Optional[int] = None  # 1-5, 経営陣のビジョン
    mgmt_decision: Optional[int] = None  # 1-5, 意思決定プロセス
    mgmt_structure: Optional[int] = None  # 1-5, 組織体制
    mgmt_manager: Optional[int] = None  # 1-5, 直属上司の評価
    mgmt_comment: Optional[str] = None  # max 500 chars

    # Category 6: 評価・処遇制度 (Performance & Promotion)
    perf_fairness: Optional[int] = None  # 1-5, 評価制度の公平性
    perf_feedback: Optional[int] = None  # 1-5, 評価とフィードバック
    perf_promotion: Optional[int] = None  # 1-5, 昇進・昇格
    perf_linkage: Optional[int] = None  # 1-5, 報酬と評価の連動性
    perf_comment: Optional[str] = None  # max 500 chars

    # Category 7: 職場環境 (Work Environment)
    env_office: Optional[int] = None  # 1-5, オフィス環境
    env_relationships: Optional[int] = None  # 1-5, 人間関係
    env_stress: Optional[int] = None  # 1-5, ストレスレベル (inverted scoring)
    env_health: Optional[int] = None  # 1-5, 健康管理・安全衛生
    env_comment: Optional[str] = None  # max 500 chars

    # Category 8: 事業・製品 (Business & Product)
    biz_future: Optional[int] = None  # 1-5, 事業の将来性
    biz_pride: Optional[int] = None  # 1-5, 製品・サービスへの誇り
    biz_social_impact: Optional[int] = None  # 1-5, 社会貢献度
    biz_financial: Optional[int] = None  # 1-5, 財務健全性
    biz_comment: Optional[str] = None  # max 500 chars

    # Overall Assessment (総合評価)
    overall_satisfaction: Optional[int] = None  # 1-5, 総合満足度 (required for new schema)
    overall_nps: Optional[int] = None  # 0-10, 推薦意向 NPS (required for new schema)
    tenure: Optional[str] = None  # Enum value: "6m_under", "6m_1y", "1y_3y", "3y_5y", "5y_over"
    job_category: Optional[str] = None  # Enum value: "engineer", "designer", "pm", "marketing", "sales", "corporate", "other"
    overall_comment: Optional[str] = None  # max 1000 chars

    def __post_init__(self):
        """データ検証"""
        # 言語コードの検証
        valid_languages = ["en", "ja", "zh"]
        if self.language not in valid_languages:
            raise ValueError(f"言語コードは 'en', 'ja', 'zh' のいずれかである必要があります")

        # 新規8カテゴリーフィールドのバリデーション
        self._validate_extended_schema()

    def _validate_extended_schema(self):
        """新しい8カテゴリースキーマのバリデーション

        各レーティングフィールドの1-5範囲チェック
        overall_nps の0-10範囲チェック
        tenure、job_category の enum値チェック
        """
        self._validate_rating_fields()
        self._validate_nps_field()
        self._validate_enum_fields()
        self._validate_comment_lengths()

    def _validate_rating_fields(self):
        """すべてのレーティングフィールドを検証（1-5範囲）"""
        # レーティングフィールド（1-5範囲チェック）
        rating_fields = [
            # Category 1: Compensation & Benefits (4 fields)
            'comp_salary', 'comp_bonus', 'comp_benefits',
            # Category 2: Work-Life Balance (4 fields)
            'wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall',
            # Category 3: Company Culture (4 fields)
            'culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication',
            # Category 4: Career Development (4 fields)
            'career_growth', 'career_training', 'career_path', 'career_mentorship',
            # Category 5: Management (4 fields)
            'mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager',
            # Category 6: Performance & Promotion (4 fields)
            'perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage',
            # Category 7: Work Environment (4 fields)
            'env_office', 'env_relationships', 'env_stress', 'env_health',
            # Category 8: Business & Product (4 fields)
            'biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial',
            # Overall Assessment (1 field)
            'overall_satisfaction'
        ]

        for field in rating_fields:
            value = getattr(self, field, None)
            if value is not None:
                if not isinstance(value, int):
                    raise ValueError(f"{field} は整数である必要があります")
                if value < 1 or value > 5:
                    raise ValueError(f"{field} は1から5の間である必要があります（現在: {value}）")

    def _validate_nps_field(self):
        """NPSフィールドを検証（0-10範囲）"""
        if self.overall_nps is not None:
            if not isinstance(self.overall_nps, int):
                raise ValueError("overall_nps は整数である必要があります")
            if self.overall_nps < 0 or self.overall_nps > 10:
                raise ValueError(f"overall_nps は0から10の間である必要があります（現在: {self.overall_nps}）")

    def _validate_enum_fields(self):
        """tenureとjob_categoryのenum値を検証"""
        # tenure enumチェック
        if self.tenure is not None:
            valid_tenures = [t.value for t in TenureEnum]
            if self.tenure not in valid_tenures:
                raise ValueError(f"tenure は {valid_tenures} のいずれかである必要があります（現在: {self.tenure}）")

        # job_category enumチェック
        if self.job_category is not None:
            valid_categories = [c.value for c in JobCategory]
            if self.job_category not in valid_categories:
                raise ValueError(f"job_category は {valid_categories} のいずれかである必要があります（現在: {self.job_category}）")

    def _validate_comment_lengths(self):
        """各コメント欄の最大文字数を検証"""
        comment_fields_with_max = [
            # Category comments (max 500 chars each)
            ('comp_comment', 500),
            ('wlb_comment', 500),
            ('culture_comment', 500),
            ('career_comment', 500),
            ('mgmt_comment', 500),
            ('perf_comment', 500),
            ('env_comment', 500),
            ('biz_comment', 500),
            # Overall comment (max 1000 chars)
            ('overall_comment', 1000)
        ]

        for field, max_length in comment_fields_with_max:
            value = getattr(self, field, None)
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(f"{field} は文字列である必要があります")
                if len(value) > max_length:
                    raise ValueError(f"{field} は最大{max_length}文字までです（現在: {len(value)}文字）")

    @classmethod
    def from_dict(cls, data: dict) -> 'Review':
        """辞書からReviewオブジェクトを作成

        レガシー6カテゴリースキーマと新規8カテゴリースキーマの両方をサポート
        """
        # 勤務期間データの処理
        employment_period = None
        if 'employment_period' in data and data['employment_period']:
            employment_period = EmploymentPeriod.from_dict(data['employment_period'])

        # 新規8カテゴリーフィールドを辞書から安全に取得
        extended_fields = {
            # Compensation (4 ratings + comment)
            'comp_salary': data.get('comp_salary'),
            'comp_bonus': data.get('comp_bonus'),
            'comp_benefits': data.get('comp_benefits'),
            'comp_equity': data.get('comp_equity'),
            'comp_comment': data.get('comp_comment'),
            # Work-Life Balance (4 ratings + comment)
            'wlb_hours': data.get('wlb_hours'),
            'wlb_vacation': data.get('wlb_vacation'),
            'wlb_flexibility': data.get('wlb_flexibility'),
            'wlb_overall': data.get('wlb_overall'),
            'wlb_comment': data.get('wlb_comment'),
            # Company Culture (4 ratings + comment)
            'culture_atmosphere': data.get('culture_atmosphere'),
            'culture_diversity': data.get('culture_diversity'),
            'culture_ethics': data.get('culture_ethics'),
            'culture_communication': data.get('culture_communication'),
            'culture_comment': data.get('culture_comment'),
            # Career Development (4 ratings + comment)
            'career_growth': data.get('career_growth'),
            'career_training': data.get('career_training'),
            'career_path': data.get('career_path'),
            'career_mentorship': data.get('career_mentorship'),
            'career_comment': data.get('career_comment'),
            # Management (4 ratings + comment)
            'mgmt_vision': data.get('mgmt_vision'),
            'mgmt_decision': data.get('mgmt_decision'),
            'mgmt_structure': data.get('mgmt_structure'),
            'mgmt_manager': data.get('mgmt_manager'),
            'mgmt_comment': data.get('mgmt_comment'),
            # Performance System (4 ratings + comment)
            'perf_fairness': data.get('perf_fairness'),
            'perf_feedback': data.get('perf_feedback'),
            'perf_promotion': data.get('perf_promotion'),
            'perf_linkage': data.get('perf_linkage'),
            'perf_comment': data.get('perf_comment'),
            # Work Environment (4 ratings + comment)
            'env_office': data.get('env_office'),
            'env_relationships': data.get('env_relationships'),
            'env_stress': data.get('env_stress'),
            'env_health': data.get('env_health'),
            'env_comment': data.get('env_comment'),
            # Business & Product (4 ratings + comment)
            'biz_future': data.get('biz_future'),
            'biz_pride': data.get('biz_pride'),
            'biz_social_impact': data.get('biz_social_impact'),
            'biz_financial': data.get('biz_financial'),
            'biz_comment': data.get('biz_comment'),
            # Overall Assessment
            'overall_satisfaction': data.get('overall_satisfaction'),
            'overall_nps': data.get('overall_nps'),
            'tenure': data.get('tenure'),
            'job_category': data.get('job_category'),
            'overall_comment': data.get('overall_comment')
        }

        return cls(
            id=str(data.get('_id', data.get('id'))),
            company_id=data['company_id'],
            user_id=data['user_id'],
            employment_status=EmploymentStatus(data['employment_status']),
            ratings=data['ratings'],
            comments=data['comments'],
            individual_average=data['individual_average'],
            answered_count=data['answered_count'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            is_active=data.get('is_active', True),
            employment_period=employment_period,
            language=data.get('language', 'ja'),
            comments_ja=data.get('comments_ja'),
            comments_zh=data.get('comments_zh'),
            comments_en=data.get('comments_en'),
            # Extended fields
            **extended_fields
        )

    def to_dict(self) -> dict:
        """辞書形式に変換

        レガシー6カテゴリーフィールドと新規8カテゴリーフィールドの両方を返す
        """
        result = {
            'company_id': self.company_id,
            'user_id': self.user_id,
            'employment_status': self.employment_status.value,
            'ratings': self.ratings,
            'comments': self.comments,
            'individual_average': self.individual_average,
            'answered_count': self.answered_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active,
            'language': self.language
        }

        # 勤務期間データがある場合は追加
        if self.employment_period:
            result['employment_period'] = self.employment_period.to_dict()

        # 翻訳データがある場合は追加（Noneでないもののみ）
        if self.comments_ja is not None:
            result['comments_ja'] = self.comments_ja
        if self.comments_zh is not None:
            result['comments_zh'] = self.comments_zh
        if self.comments_en is not None:
            result['comments_en'] = self.comments_en

        # 新規8カテゴリーフィールド（Noneでないもののみ追加）
        extended_fields = {
            'comp_salary', 'comp_bonus', 'comp_benefits', 'comp_equity', 'comp_comment',
            'wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall', 'wlb_comment',
            'culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication', 'culture_comment',
            'career_growth', 'career_training', 'career_path', 'career_mentorship', 'career_comment',
            'mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager', 'mgmt_comment',
            'perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage', 'perf_comment',
            'env_office', 'env_relationships', 'env_stress', 'env_health', 'env_comment',
            'biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial', 'biz_comment',
            'overall_satisfaction', 'overall_nps', 'tenure', 'job_category', 'overall_comment'
        }

        for field in extended_fields:
            value = getattr(self, field, None)
            if value is not None:
                result[field] = value

        return result

    @staticmethod
    def calculate_individual_average(ratings: Dict[str, Optional[int]]) -> tuple[float, int]:
        """
        個別レビューの平均点を計算

        Args:
            ratings: 各項目の評価（1-5 or None）

        Returns:
            tuple: (平均点, 回答項目数)
        """
        valid_ratings = [score for score in ratings.values() if score is not None]

        if not valid_ratings:
            return 0.0, 0

        average = sum(valid_ratings) / len(valid_ratings)
        return round(average, 1), len(valid_ratings)

    def set_employment_period(self, start_year: int, end_year: Optional[Union[int, str]] = None) -> None:
        """
        勤務期間を設定

        Args:
            start_year: 開始年
            end_year: 終了年（None または 'current' で現在勤務を表す）
        """
        # 'current' の場合は None に変換
        if end_year == 'current':
            end_year = None
        elif isinstance(end_year, str):
            end_year = int(end_year)

        self.employment_period = EmploymentPeriod(start_year=start_year, end_year=end_year)

    def get_employment_period_display(self) -> str:
        """勤務期間の表示用文字列を取得"""
        if self.employment_period:
            return self.employment_period.get_display_string()
        return "勤務期間未設定"

    def validate_employment_period(self) -> bool:
        """勤務期間データの妥当性を検証"""
        if not self.employment_period:
            return True  # 勤務期間が設定されていない場合は妥当

        try:
            # EmploymentPeriodクラスの__post_init__でバリデーションが実行される
            EmploymentPeriod(
                start_year=self.employment_period.start_year,
                end_year=self.employment_period.end_year
            )
            return True
        except ValueError:
            return False


@dataclass
class ReviewSummary:
    """企業レビューサマリー"""
    total_reviews: int
    overall_average: float
    category_averages: Dict[str, float]
    last_review_date: datetime  # 最新レビューの投稿日時

    @classmethod
    def from_dict(cls, data: dict) -> 'ReviewSummary':
        """辞書からReviewSummaryオブジェクトを作成"""
        return cls(
            total_reviews=data['total_reviews'],
            overall_average=data['overall_average'],
            category_averages=data['category_averages'],
            last_review_date=data['last_review_date']
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'total_reviews': self.total_reviews,
            'overall_average': self.overall_average,
            'category_averages': self.category_averages,
            'last_review_date': self.last_review_date
        }