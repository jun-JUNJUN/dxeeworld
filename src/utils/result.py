"""
Result型による操作結果の型安全な表現
"""
from typing import TypeVar, Generic, Optional

T = TypeVar('T')
E = TypeVar('E')


class Result(Generic[T, E]):
    """操作結果を表現するクラス"""
    
    def __init__(self, data: Optional[T] = None, error: Optional[E] = None, is_success: bool = True):
        self.data = data
        self.error = error
        self.is_success = is_success
    
    @classmethod
    def success(cls, data: T) -> 'Result[T, E]':
        """成功結果を作成"""
        return cls(data=data, is_success=True)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """失敗結果を作成"""
        return cls(error=error, is_success=False)