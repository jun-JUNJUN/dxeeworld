"""
レビュー履歴管理モデル
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ReviewAction(Enum):
    """レビュー操作種別"""
    CREATE = "create"
    UPDATE = "update"


@dataclass
class ReviewHistory:
    """レビュー履歴データモデル"""
    id: str
    review_id: str
    user_id: str
    company_id: str
    action: ReviewAction
    previous_data: Optional[Dict[str, Any]]
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: dict) -> 'ReviewHistory':
        """辞書からReviewHistoryオブジェクトを作成"""
        return cls(
            id=str(data.get('_id', data.get('id'))),
            review_id=data['review_id'],
            user_id=data['user_id'],
            company_id=data['company_id'],
            action=ReviewAction(data['action']),
            previous_data=data.get('previous_data'),
            timestamp=data['timestamp']
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'review_id': self.review_id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'action': self.action.value,
            'previous_data': self.previous_data,
            'timestamp': self.timestamp
        }