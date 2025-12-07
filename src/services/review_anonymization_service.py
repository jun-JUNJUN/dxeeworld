"""
レビュー匿名化サービス

ユーザーIDを匿名化表示（例：「ユーザーA」）に変換するサービス
"""
import hashlib
from typing import Optional, Dict, Any
from datetime import timezone
from zoneinfo import ZoneInfo
from src.models.review import Review


class ReviewAnonymizationService:
    """ユーザーIDを匿名化するサービス"""

    def __init__(self, salt: str = ""):
        """
        Args:
            salt: ハッシュ値のカスタマイズ用のソルト（オプション）
        """
        self.salt = salt

    def anonymize_user_id(self, user_id: str) -> str:
        """
        ユーザーIDを匿名化表示に変換

        Args:
            user_id: ユーザーID

        Returns:
            匿名化表示（例：「ユーザーA」）
        """
        hash_value = self._hash_user_id(user_id)
        letter = self._hash_to_letter(hash_value)
        return f"ユーザー{letter}"

    def anonymize_review(self, review: Review, preview_mode: bool = False) -> Dict[str, Any]:
        """
        レビューオブジェクトを匿名化

        Args:
            review: レビューオブジェクト
            preview_mode: プレビューモード（Trueの場合はコメントをマスキング）

        Returns:
            匿名化されたレビューデータ（辞書形式）
        """
        # ユーザーIDを匿名化
        anonymized_user = self.anonymize_user_id(review.user_id)

        # 勤務期間の処理
        employment_period_dict = None
        if review.employment_period is not None:
            employment_period_dict = {
                "start_year": review.employment_period.start_year,
                "end_year": review.employment_period.end_year,
                "display": review.employment_period.get_display_string()
            }

        # コメントの処理（プレビューモードの場合はマスキング）
        def mask_comments(comments: Optional[Dict[str, Optional[str]]]) -> Optional[Dict[str, Optional[str]]]:
            """コメントをマスキングする（プレビューモード用）"""
            if comments is None:
                return None
            return {
                key: "***" if value is not None else None
                for key, value in comments.items()
            }

        comments = mask_comments(review.comments) if preview_mode else review.comments
        comments_ja = mask_comments(review.comments_ja) if preview_mode and review.comments_ja else review.comments_ja
        comments_zh = mask_comments(review.comments_zh) if preview_mode and review.comments_zh else review.comments_zh
        comments_en = mask_comments(review.comments_en) if preview_mode and review.comments_en else review.comments_en

        # タイムゾーン変換: UTC → JST (Good Pattern - Timezone-Aware Datetime)
        jst = ZoneInfo("Asia/Tokyo")
        created_at_jst = review.created_at.astimezone(jst) if review.created_at else None
        updated_at_jst = review.updated_at.astimezone(jst) if review.updated_at else None

        # 匿名化されたレビューデータを構築
        anonymized_review = {
            "id": review.id,
            "company_id": review.company_id,
            "anonymized_user": anonymized_user,
            "employment_status": review.employment_status.value,
            "employment_period": employment_period_dict,
            "ratings": review.ratings,
            "comments": comments,
            "individual_average": review.individual_average,
            "answered_count": review.answered_count,
            "created_at": review.created_at,  # 元のUTC時刻（互換性のため保持）
            "created_at_jst": created_at_jst,  # JST変換済み
            "updated_at": review.updated_at,  # 元のUTC時刻（互換性のため保持）
            "updated_at_jst": updated_at_jst,  # JST変換済み
            "is_active": review.is_active,
            "language": review.language,
            "comments_ja": comments_ja,
            "comments_zh": comments_zh,
            "comments_en": comments_en
        }

        return anonymized_review

    def _hash_user_id(self, user_id: str) -> str:
        """
        ユーザーIDからSHA-256ハッシュ値を生成

        Args:
            user_id: ユーザーID

        Returns:
            64文字の16進数文字列
        """
        salted_user_id = user_id + self.salt
        hash_object = hashlib.sha256(salted_user_id.encode('utf-8'))
        return hash_object.hexdigest()

    def _hash_to_letter(self, hash_value: str) -> str:
        """
        ハッシュ値をA-Zの1文字に変換

        アルゴリズム:
        1. ハッシュ値の最初の8文字を取得
        2. 16進数を10進数に変換
        3. 26で割った余りを計算
        4. 余りをA-Zのアルファベットに変換

        Args:
            hash_value: 16進数文字列のハッシュ値

        Returns:
            A-Zの1文字
        """
        # 最初の8文字を取得
        first_8_chars = hash_value[:8]

        # 16進数を10進数に変換
        decimal_value = int(first_8_chars, 16)

        # 26で割った余りを計算
        remainder = decimal_value % 26

        # A-Zのアルファベットに変換
        letter = chr(ord('A') + remainder)

        return letter
