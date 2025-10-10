"""
ユーザーモデル
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime


class UserType(Enum):
    """ユーザータイプ"""
    JOB_SEEKER = "JOB_SEEKER"
    RECRUITER = "RECRUITER"


class SkillLevel(Enum):
    """スキルレベル"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UserProfile:
    """ユーザープロファイル"""
    
    def __init__(self, 
                 bio: Optional[str] = None,
                 skills: Optional[List[str]] = None,
                 experience_years: Optional[int] = None,
                 education: Optional[str] = None,
                 location: Optional[str] = None,
                 linkedin_url: Optional[str] = None,
                 github_url: Optional[str] = None,
                 portfolio_url: Optional[str] = None):
        self.bio = bio
        self.skills = skills or []
        self.experience_years = experience_years
        self.education = education
        self.location = location
        self.linkedin_url = linkedin_url
        self.github_url = github_url
        self.portfolio_url = portfolio_url
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'bio': self.bio,
            'skills': self.skills,
            'experience_years': self.experience_years,
            'education': self.education,
            'location': self.location,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'portfolio_url': self.portfolio_url
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """辞書からプロファイルインスタンスを作成"""
        return cls(
            bio=data.get('bio'),
            skills=data.get('skills', []),
            experience_years=data.get('experience_years'),
            education=data.get('education'),
            location=data.get('location'),
            linkedin_url=data.get('linkedin_url'),
            github_url=data.get('github_url'),
            portfolio_url=data.get('portfolio_url')
        )


class User:
    """ユーザーエンティティ"""

    def __init__(self, id: str, email: str, name: str, user_type: UserType,
                 password_hash: str, company_id: Optional[str] = None,
                 position: Optional[str] = None,
                 profile: Optional[UserProfile] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 is_active: bool = True,
                 last_review_posted_at: Optional[datetime] = None):
        self.id = id
        self.email = email
        self.name = name
        self.user_type = user_type
        self.password_hash = password_hash
        self.company_id = company_id
        self.position = position
        self.profile = profile or UserProfile()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.is_active = is_active
        self.last_review_posted_at = last_review_posted_at
    
    def to_dict(self) -> dict:
        """辞書形式に変換（パスワードハッシュは除外）"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'user_type': self.user_type.value,
            'company_id': self.company_id,
            'position': self.position,
            'profile': self.profile.to_dict() if self.profile else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'last_review_posted_at': self.last_review_posted_at.isoformat() if self.last_review_posted_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """辞書からユーザーインスタンスを作成"""
        profile_data = data.get('profile')
        profile = UserProfile.from_dict(profile_data) if profile_data else UserProfile()

        return cls(
            id=str(data['_id']),
            email=data['email'],
            name=data['name'],
            user_type=UserType(data['user_type']),
            password_hash=data['password_hash'],
            company_id=data.get('company_id'),
            position=data.get('position'),
            profile=profile,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True),
            last_review_posted_at=data.get('last_review_posted_at')
        )
    
    def update_profile(self, profile_data: dict):
        """プロファイル情報を更新"""
        if self.profile is None:
            self.profile = UserProfile()

        for key, value in profile_data.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)

        self.updated_at = datetime.utcnow()

    def update_last_review_posted_at(self, posted_at: datetime):
        """最終レビュー投稿日時を更新"""
        self.last_review_posted_at = posted_at
        self.updated_at = datetime.utcnow()

    def has_review_access(self) -> bool:
        """
        レビュー一覧へのアクセス権限を持つかチェック

        Returns:
            bool: 1年以内にレビューを投稿している場合True
        """
        if self.last_review_posted_at is None:
            return False

        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        one_year_ago = now - timedelta(days=365)

        # last_review_posted_atがnaiveな場合、UTCとみなす
        if self.last_review_posted_at.tzinfo is None:
            last_posted = self.last_review_posted_at.replace(tzinfo=timezone.utc)
        else:
            last_posted = self.last_review_posted_at

        return last_posted > one_year_ago