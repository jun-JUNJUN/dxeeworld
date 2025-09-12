"""
求人情報データモデル
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobType(Enum):
    """雇用形態"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class ExperienceLevel(Enum):
    """経験レベル"""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class SalaryType(Enum):
    """給与タイプ"""
    HOURLY = "hourly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


@dataclass
class SalaryRange:
    """給与範囲"""
    min_amount: Optional[int]
    max_amount: Optional[int]
    currency: str = "JPY"
    salary_type: SalaryType = SalaryType.ANNUAL

    def to_dict(self) -> dict:
        return {
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'currency': self.currency,
            'salary_type': self.salary_type.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SalaryRange':
        return cls(
            min_amount=data.get('min_amount'),
            max_amount=data.get('max_amount'),
            currency=data.get('currency', 'JPY'),
            salary_type=SalaryType(data.get('salary_type', SalaryType.ANNUAL.value))
        )


@dataclass
class JobRequirements:
    """求人要件"""
    required_skills: List[str]
    preferred_skills: List[str]
    experience_years: Optional[int]
    education_level: Optional[str]
    languages: List[str]

    def to_dict(self) -> dict:
        return {
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'experience_years': self.experience_years,
            'education_level': self.education_level,
            'languages': self.languages
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JobRequirements':
        return cls(
            required_skills=data.get('required_skills', []),
            preferred_skills=data.get('preferred_skills', []),
            experience_years=data.get('experience_years'),
            education_level=data.get('education_level'),
            languages=data.get('languages', [])
        )


@dataclass
class Job:
    """求人情報データモデル"""
    id: str
    title: str
    company_id: str
    company_name: str
    description: str
    job_type: JobType
    experience_level: ExperienceLevel
    location: str
    remote_work: bool
    salary_range: Optional[SalaryRange]
    requirements: JobRequirements
    benefits: List[str]
    posted_by: str  # ユーザーID
    posted_at: datetime
    expires_at: Optional[datetime]
    is_active: bool = True
    view_count: int = 0
    application_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Job':
        """辞書からJobオブジェクトを作成"""
        salary_data = data.get('salary_range')
        salary_range = SalaryRange.from_dict(salary_data) if salary_data else None
        
        requirements_data = data.get('requirements', {})
        requirements = JobRequirements.from_dict(requirements_data)
        
        return cls(
            id=str(data.get('_id', data.get('id'))),
            title=data['title'],
            company_id=data['company_id'],
            company_name=data['company_name'],
            description=data['description'],
            job_type=JobType(data['job_type']),
            experience_level=ExperienceLevel(data['experience_level']),
            location=data['location'],
            remote_work=data.get('remote_work', False),
            salary_range=salary_range,
            requirements=requirements,
            benefits=data.get('benefits', []),
            posted_by=data['posted_by'],
            posted_at=data['posted_at'],
            expires_at=data.get('expires_at'),
            is_active=data.get('is_active', True),
            view_count=data.get('view_count', 0),
            application_count=data.get('application_count', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'title': self.title,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'description': self.description,
            'job_type': self.job_type.value,
            'experience_level': self.experience_level.value,
            'location': self.location,
            'remote_work': self.remote_work,
            'salary_range': self.salary_range.to_dict() if self.salary_range else None,
            'requirements': self.requirements.to_dict(),
            'benefits': self.benefits,
            'posted_by': self.posted_by,
            'posted_at': self.posted_at,
            'expires_at': self.expires_at,
            'is_active': self.is_active,
            'view_count': self.view_count,
            'application_count': self.application_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def is_expired(self) -> bool:
        """求人が期限切れかどうかを確認"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def increment_view_count(self):
        """閲覧数を増加"""
        self.view_count += 1

    def increment_application_count(self):
        """応募数を増加"""
        self.application_count += 1