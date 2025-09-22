"""
レビューデータモデル
"""
from dataclasses import dataclass
from typing import Optional, Dict
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

    @classmethod
    def from_dict(cls, data: dict) -> 'Review':
        """辞書からReviewオブジェクトを作成"""
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
            is_active=data.get('is_active', True)
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'company_id': self.company_id,
            'user_id': self.user_id,
            'employment_status': self.employment_status.value,
            'ratings': self.ratings,
            'comments': self.comments,
            'individual_average': self.individual_average,
            'answered_count': self.answered_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }

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