"""
企業データモデル
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum

# レビュー関連の型をインポート
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .review import ReviewSummary


class IndustryType(Enum):
    """業界種別"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    CONSULTING = "consulting"
    MEDIA = "media"
    REAL_ESTATE = "real_estate"
    CONSTRUCTION = "construction"
    OTHER = "other"


class CompanySize(Enum):
    """企業規模"""
    STARTUP = "startup"          # 1-10名
    SMALL = "small"              # 11-50名
    MEDIUM = "medium"            # 51-200名
    LARGE = "large"              # 201-1000名
    ENTERPRISE = "enterprise"    # 1000名以上


@dataclass
class Company:
    """企業データモデル"""
    id: str
    name: str
    industry: IndustryType
    size: CompanySize
    country: str  # 国名は必須フィールド
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    name_original: Optional[str] = None
    source_files: Optional[List[str]] = None
    foreign_company_data: Optional[dict] = None
    construction_data: Optional[dict] = None
    review_summary: Optional['ReviewSummary'] = None  # レビューサマリー追加

    @classmethod
    def from_dict(cls, data: dict) -> 'Company':
        """辞書からCompanyオブジェクトを作成"""
        # レビューサマリーの処理
        review_summary = None
        if 'review_summary' in data and data['review_summary'] is not None:
            from .review import ReviewSummary
            review_summary = ReviewSummary.from_dict(data['review_summary'])

        return cls(
            id=str(data.get('_id', data.get('id'))),
            name=data['name'],
            industry=IndustryType(data['industry']),
            size=CompanySize(data['size']),
            country=data['country'],  # 必須フィールド
            description=data.get('description'),
            website=data.get('website'),
            location=data.get('location'),
            founded_year=data.get('founded_year'),
            employee_count=data.get('employee_count'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True),
            name_original=data.get('name_original'),
            source_files=data.get('source_files', []),
            foreign_company_data=data.get('foreign_company_data', {}),
            construction_data=data.get('construction_data', {}),
            review_summary=review_summary
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        result = {
            'name': self.name,
            'industry': self.industry.value,
            'size': self.size.value,
            'country': self.country,
            'description': self.description,
            'website': self.website,
            'location': self.location,
            'founded_year': self.founded_year,
            'employee_count': self.employee_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active,
            'name_original': self.name_original,
            'source_files': self.source_files or [],
            'foreign_company_data': self.foreign_company_data or {},
            'construction_data': self.construction_data or {}
        }

        # レビューサマリーがある場合のみ追加
        if self.review_summary is not None:
            result['review_summary'] = self.review_summary.to_dict()

        return result