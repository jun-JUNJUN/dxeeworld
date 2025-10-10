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
    """レビューデータモデル"""
    id: str
    company_id: str
    user_id: str
    employment_status: EmploymentStatus
    ratings: Dict[str, Optional[int]]  # 1-5 or None
    comments: Dict[str, Optional[str]]
    individual_average: float
    answered_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    employment_period: Optional[EmploymentPeriod] = None  # 新規追加: 勤務期間
    language: str = "ja"  # 新規追加: レビュー言語 (en, ja, zh)
    comments_ja: Optional[Dict[str, Optional[str]]] = None  # 新規追加: 日本語翻訳
    comments_zh: Optional[Dict[str, Optional[str]]] = None  # 新規追加: 中国語翻訳
    comments_en: Optional[Dict[str, Optional[str]]] = None  # 新規追加: 英語翻訳

    def __post_init__(self):
        """データ検証"""
        # 言語コードの検証
        valid_languages = ["en", "ja", "zh"]
        if self.language not in valid_languages:
            raise ValueError(f"言語コードは 'en', 'ja', 'zh' のいずれかである必要があります")

    @classmethod
    def from_dict(cls, data: dict) -> 'Review':
        """辞書からReviewオブジェクトを作成"""
        # 勤務期間データの処理
        employment_period = None
        if 'employment_period' in data and data['employment_period']:
            employment_period = EmploymentPeriod.from_dict(data['employment_period'])

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
            comments_en=data.get('comments_en')
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
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
    last_updated: datetime

    @classmethod
    def from_dict(cls, data: dict) -> 'ReviewSummary':
        """辞書からReviewSummaryオブジェクトを作成"""
        return cls(
            total_reviews=data['total_reviews'],
            overall_average=data['overall_average'],
            category_averages=data['category_averages'],
            last_updated=data['last_updated']
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'total_reviews': self.total_reviews,
            'overall_average': self.overall_average,
            'category_averages': self.category_averages,
            'last_updated': self.last_updated
        }