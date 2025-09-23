"""
企業別平均点計算サービス
"""
from typing import Dict, List
from datetime import datetime
from src.models.review import ReviewSummary, ReviewCategory


class CompanyCalculationService:
    """企業レビューの集計・計算処理を担当するサービス"""

    def __init__(self, db_service):
        """
        Args:
            db_service: データベースサービス
        """
        self.db = db_service

    async def calculate_company_averages(self, company_id: str) -> ReviewSummary:
        """
        企業の全項目平均と項目別平均を計算

        Args:
            company_id: 企業ID

        Returns:
            ReviewSummary: 計算されたレビューサマリー
        """
        # 企業の全アクティブレビューを取得
        reviews = await self.db.find_many(
            "reviews",
            {"company_id": company_id, "is_active": True}
        )

        if not reviews:
            return ReviewSummary(
                total_reviews=0,
                overall_average=0.0,
                category_averages={category.value: 0.0 for category in ReviewCategory},
                last_updated=datetime.utcnow()
            )

        # 全項目平均の計算
        individual_averages = [review["individual_average"] for review in reviews]
        overall_average = round(sum(individual_averages) / len(individual_averages), 1)

        # 項目別平均の計算
        category_averages = {}
        for category in ReviewCategory:
            category_ratings = []
            for review in reviews:
                rating = review["ratings"].get(category.value)
                if rating is not None:
                    category_ratings.append(rating)

            if category_ratings:
                category_averages[category.value] = round(
                    sum(category_ratings) / len(category_ratings), 1
                )
            else:
                category_averages[category.value] = 0.0

        return ReviewSummary(
            total_reviews=len(reviews),
            overall_average=overall_average,
            category_averages=category_averages,
            last_updated=datetime.utcnow()
        )

    async def update_company_summary(self, company_id: str, summary: ReviewSummary) -> bool:
        """
        企業のレビューサマリーを更新

        Args:
            company_id: 企業ID
            summary: 更新するレビューサマリー

        Returns:
            bool: 更新成功フラグ
        """
        update_data = {
            "review_summary": summary.to_dict()
        }

        result = await self.db.update_one(
            "companies",
            {"_id": company_id},
            update_data
        )

        return result

    async def recalculate_company_averages(self, company_id: str) -> bool:
        """
        企業の平均点を再計算・更新

        Args:
            company_id: 企業ID

        Returns:
            bool: 処理成功フラグ
        """
        try:
            # 平均点を計算
            summary = await self.calculate_company_averages(company_id)

            # データベースを更新
            result = await self.update_company_summary(company_id, summary)

            return result

        except Exception:
            return False