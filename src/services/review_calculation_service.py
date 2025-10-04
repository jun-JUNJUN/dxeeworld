"""
レビュー計算ロジックサービス
"""
from typing import Dict, Optional, List, Tuple
from src.models.review import ReviewCategory


class ReviewCalculationService:
    """レビューの計算処理を担当するサービス"""

    def calculate_individual_average(self, ratings: Dict[str, Optional[int]]) -> Tuple[float, int]:
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

    def validate_rating_values(self, ratings: Dict[str, Optional[int]]) -> List[str]:
        """
        評価値のバリデーション

        Args:
            ratings: 評価データ

        Returns:
            エラーメッセージのリスト
        """
        errors = []

        for category, rating in ratings.items():
            if rating is not None:
                # 型チェック（boolはintのサブクラスなので明示的に除外）
                if not isinstance(rating, int) or isinstance(rating, bool):
                    errors.append(f"Invalid type for {category}: expected int, got {type(rating).__name__}")
                    continue

                # 範囲チェック（1-5）
                if rating < 1 or rating > 5:
                    errors.append(f"Invalid rating for {category}: {rating} (must be 1-5)")

        return errors

    def validate_required_categories(self, ratings: Dict[str, Optional[int]]) -> List[str]:
        """
        必須カテゴリーの存在確認

        Args:
            ratings: 評価データ

        Returns:
            エラーメッセージのリスト
        """
        errors = []
        required_categories = {category.value for category in ReviewCategory}

        for category in required_categories:
            if category not in ratings:
                errors.append(f"Missing required category: {category}")

        return errors

    async def recalculate_company_averages(self, company_id: str) -> bool:
        """
        企業の平均評価を再計算（現在はモック実装）

        Args:
            company_id: 企業ID

        Returns:
            成功したかどうか
        """
        # TODO: 実際の実装では以下を行う:
        # 1. 企業の全アクティブレビューを取得
        # 2. カテゴリー別平均点を計算
        # 3. 全体平均点を計算
        # 4. 企業のreview_summaryを更新

        # モック実装として成功を返す
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Mock: Recalculating company averages for {company_id}")
        return True