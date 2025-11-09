"""
レビュー集計サービス
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)


class ReviewAggregationService:
    """企業単位でレビューデータを集計するサービス"""

    def __init__(self, db_service=None):
        """
        Args:
            db_service: データベースサービス
        """
        self.db = db_service

    def calculate_category_averages(self, reviews: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        カテゴリ別評価平均を計算（None値を除外）

        Args:
            reviews: レビューのリスト

        Returns:
            カテゴリ別評価平均の辞書
        """
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment"
        ]

        category_averages = {}

        for category in categories:
            # 有効な評価値（None以外）を抽出
            valid_ratings = [
                review["ratings"][category]
                for review in reviews
                if review.get("ratings", {}).get(category) is not None
            ]

            # 平均計算
            if valid_ratings:
                category_averages[category] = sum(valid_ratings) / len(valid_ratings)
            else:
                category_averages[category] = 0.0

        return category_averages

    def calculate_overall_average(self, category_averages: Dict[str, float]) -> float:
        """
        総合評価平均を計算（全カテゴリの平均値の平均）

        Args:
            category_averages: カテゴリ別評価平均

        Returns:
            総合評価平均
        """
        averages = list(category_averages.values())

        if not averages:
            return 0.0

        return sum(averages) / len(averages)

    async def aggregate_company_reviews(self, company_id: str) -> Dict[str, Any]:
        """
        企業単位でレビューを集計し、Company.review_summary を更新

        Args:
            company_id: 企業ID

        Returns:
            集計結果
        """
        try:
            # ObjectIdに変換
            try:
                company_oid = ObjectId(company_id)
            except Exception as e:
                logger.error(f"Invalid company_id format: {company_id}, error: {e}")
                return {
                    "success": False,
                    "company_id": company_id,
                    "error": f"Invalid company_id format: {company_id}"
                }

            # 対象企業のすべてのアクティブなレビューを取得
            reviews = await self.db.find_many(
                "reviews",
                {"company_id": company_oid, "is_active": True},
                sort=[("created_at", -1)]
            )

            # レビュー総数
            total_reviews = len(reviews)

            # レビューが0件の場合
            if total_reviews == 0:
                return {
                    "success": True,
                    "company_id": company_id,
                    "total_reviews": 0,
                    "overall_average": 0.0,
                    "category_averages": {
                        "recommendation": 0.0,
                        "foreign_support": 0.0,
                        "company_culture": 0.0,
                        "employee_relations": 0.0,
                        "evaluation_system": 0.0,
                        "promotion_treatment": 0.0
                    },
                    "last_review_date": None
                }

            # カテゴリ別評価平均を計算
            category_averages = self.calculate_category_averages(reviews)

            # 総合評価平均を計算
            overall_average = self.calculate_overall_average(category_averages)

            # 最終レビュー投稿日時を取得（最新のレビュー）
            last_review_date = reviews[0]["created_at"] if reviews else None

            return {
                "success": True,
                "company_id": company_id,
                "total_reviews": total_reviews,
                "overall_average": overall_average,
                "category_averages": category_averages,
                "last_review_date": last_review_date
            }

        except Exception as e:
            logger.exception(f"Failed to aggregate reviews for company {company_id}: {e}")
            return {
                "success": False,
                "company_id": company_id,
                "error": str(e)
            }

    async def aggregate_and_update_company(self, company_id: str) -> Dict[str, Any]:
        """
        企業単位でレビューを集計し、Company.review_summary を更新

        Args:
            company_id: 企業ID

        Returns:
            集計結果と更新ステータス
        """
        try:
            # 集計処理を実行
            aggregation_result = await self.aggregate_company_reviews(company_id)

            if not aggregation_result["success"]:
                return aggregation_result

            # ObjectIdに変換
            try:
                company_oid = ObjectId(company_id)
            except Exception as e:
                logger.error(f"Invalid company_id format: {company_id}, error: {e}")
                return {
                    "success": False,
                    "company_id": company_id,
                    "error": f"Invalid company_id format: {company_id}"
                }

            # review_summary データを構築
            review_summary = {
                "total_reviews": aggregation_result["total_reviews"],
                "overall_average": aggregation_result["overall_average"],
                "category_averages": aggregation_result["category_averages"],
                "last_review_date": aggregation_result["last_review_date"],
                "last_updated": datetime.now()
            }

            # 企業レコードを更新
            update_result = await self.db.update_one(
                "companies",
                {"_id": company_oid},
                {"$set": {"review_summary": review_summary}}
            )

            logger.info(f"Updated review_summary for company {company_id}: {aggregation_result['total_reviews']} reviews")

            return {
                "success": True,
                "company_id": company_id,
                "total_reviews": aggregation_result["total_reviews"],
                "overall_average": aggregation_result["overall_average"],
                "category_averages": aggregation_result["category_averages"],
                "last_review_date": aggregation_result["last_review_date"],
                "updated": update_result > 0 if isinstance(update_result, int) else True
            }

        except Exception as e:
            logger.exception(f"Failed to update company review summary for {company_id}: {e}")
            return {
                "success": False,
                "company_id": company_id,
                "error": str(e)
            }
