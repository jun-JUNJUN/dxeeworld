"""
ユーザーモデル
"""
from enum import Enum
from typing import Optional
from datetime import datetime


class UserType(Enum):
    """ユーザータイプ"""
    JOB_SEEKER = "JOB_SEEKER"
    RECRUITER = "RECRUITER"


class User:
    """ユーザーエンティティ"""
    
    def __init__(self, id: str, email: str, name: str, user_type: UserType, 
                 password_hash: str, company_id: Optional[str] = None, 
                 position: Optional[str] = None, 
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 is_active: bool = True):
        self.id = id
        self.email = email
        self.name = name
        self.user_type = user_type
        self.password_hash = password_hash
        self.company_id = company_id
        self.position = position
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.is_active = is_active
    
    def to_dict(self) -> dict:
        """辞書形式に変換（パスワードハッシュは除外）"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'user_type': self.user_type.value,
            'company_id': self.company_id,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """辞書からユーザーインスタンスを作成"""
        return cls(
            id=str(data['_id']),
            email=data['email'],
            name=data['name'],
            user_type=UserType(data['user_type']),
            password_hash=data['password_hash'],
            company_id=data.get('company_id'),
            position=data.get('position'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True)
        )