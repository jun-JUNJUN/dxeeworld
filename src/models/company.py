"""
企業データモデル
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


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
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'Company':
        """辞書からCompanyオブジェクトを作成"""
        return cls(
            id=str(data.get('_id', data.get('id'))),
            name=data['name'],
            industry=IndustryType(data['industry']),
            size=CompanySize(data['size']),
            description=data.get('description'),
            website=data.get('website'),
            location=data.get('location'),
            founded_year=data.get('founded_year'),
            employee_count=data.get('employee_count'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True)
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'industry': self.industry.value,
            'size': self.size.value,
            'description': self.description,
            'website': self.website,
            'location': self.location,
            'founded_year': self.founded_year,
            'employee_count': self.employee_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }