"""
レビュー集計サービス
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId

logger = logging.getLogger(__name__)

# 新8カテゴリーの定義: (出力キー, フィールドリスト)
_NEW_CATEGORIES: List[tuple] = [
    ("compensation",       ["comp_salary", "comp_bonus", "comp_benefits", "comp_equity"]),
    ("work_life_balance",  ["wlb_hours", "wlb_vacation", "wlb_flexibility", "wlb_overall"]),
    ("culture",            ["culture_atmosphere", "culture_diversity", "culture_ethics", "culture_communication"]),
    ("career_development", ["career_growth", "career_training", "career_path", "career_mentorship"]),
    ("management",         ["mgmt_vision", "mgmt_decision", "mgmt_structure", "mgmt_manager"]),
    ("performance_system", ["perf_fairness", "perf_feedback", "perf_promotion", "perf_linkage"]),
    ("work_environment",   ["env_office", "env_relationships", "env_stress", "env_health"]),
    ("business_product",   ["biz_future", "biz_pride", "biz_social_impact", "biz_financial"]),
]


class ReviewAggregationService:
    """企業単位でレビューデータを集計するサービス"""

    def __init__(self, db_service=None):
        """
        Args:
            db_service: データベースサービス
        """
        self.db = db_service
        self._cache: Dict[str, Any] = {}

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
            # company_idは文字列として保存されているため、文字列で検索
            reviews = await self.db.find_many(
                "reviews",
                {"company_id": company_id, "is_active": True},
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

    def calculate_new_category_averages(self, reviews: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        新8カテゴリーの平均評価を計算（None値を除外）

        Args:
            reviews: レビューのリスト（新スキーマフィールドを含む）

        Returns:
            8カテゴリーの平均評価辞書
        """
        result: Dict[str, float] = {}
        for category_key, fields in _NEW_CATEGORIES:
            all_values: List[float] = []
            for review in reviews:
                for field in fields:
                    val = review.get(field)
                    if val is not None:
                        all_values.append(float(val))
            result[category_key] = sum(all_values) / len(all_values) if all_values else 0.0
        return result

    def calculate_new_overall_average(self, category_averages: Dict[str, float]) -> float:
        """
        新8カテゴリーの平均から総合評価を計算

        Args:
            category_averages: カテゴリー別平均の辞書

        Returns:
            総合評価平均（0.0〜5.0）
        """
        values = [v for v in category_averages.values() if v > 0.0]
        return sum(values) / len(values) if values else 0.0

    def calculate_nps(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        NPS（Net Promoter Score）を計算

        Promoters: overall_nps 9-10
        Passives:  overall_nps 7-8
        Detractors: overall_nps 0-6

        NPS = (Promoters - Detractors) / Total * 100

        Args:
            reviews: レビューのリスト

        Returns:
            NPS計算結果辞書
        """
        promoters = 0
        passives = 0
        detractors = 0

        for review in reviews:
            nps = review.get("overall_nps")
            if nps is None:
                continue
            nps = int(nps)
            if nps >= 9:
                promoters += 1
            elif nps >= 7:
                passives += 1
            else:
                detractors += 1

        total = promoters + passives + detractors

        if total == 0:
            nps_score = 0
        else:
            nps_score = round((promoters - detractors) / total * 100)

        return {
            "nps_score": nps_score,
            "promoters_count": promoters,
            "passives_count": passives,
            "detractors_count": detractors,
            "total_count": total,
        }

    async def get_company_aggregations(self, company_id: str) -> Dict[str, Any]:
        """
        企業の新8カテゴリー集計データを取得

        Args:
            company_id: 企業ID

        Returns:
            集計結果辞書
        """
        try:
            reviews = await self.db.find_many(
                "reviews",
                {"company_id": company_id, "is_active": True},
                sort=[("created_at", -1)]
            )

            if not reviews:
                return {
                    "success": True,
                    "company_id": company_id,
                    "overall_rating": 0.0,
                    "nps_score": 0,
                    "review_count": 0,
                    "category_scores": {key: 0.0 for key, _ in _NEW_CATEGORIES},
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }

            category_scores = self.calculate_new_category_averages(reviews)
            overall_rating = self.calculate_new_overall_average(category_scores)
            nps_result = self.calculate_nps(reviews)
            last_review = reviews[0].get("created_at")

            return {
                "success": True,
                "company_id": company_id,
                "overall_rating": round(overall_rating, 2),
                "nps_score": nps_result["nps_score"],
                "review_count": len(reviews),
                "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
                "last_updated": last_review.isoformat() if hasattr(last_review, "isoformat") else str(last_review),
            }

        except Exception as e:
            logger.exception("Failed to get company aggregations for %s: %s", company_id, e)
            return {
                "success": False,
                "company_id": company_id,
                "error": str(e),
            }

    async def get_industry_benchmarks(self) -> Dict[str, Any]:
        """
        全企業を対象とした業界ベンチマーク（8カテゴリー平均）を計算

        Returns:
            業界ベンチマーク辞書
        """
        try:
            reviews = await self.db.find_many(
                "reviews",
                {"is_active": True},
            )

            benchmarks = self.calculate_new_category_averages(reviews)

            return {
                "success": True,
                "benchmarks": {k: round(v, 2) for k, v in benchmarks.items()},
                "review_count": len(reviews),
            }

        except Exception as e:
            logger.exception("Failed to get industry benchmarks: %s", e)
            return {
                "success": False,
                "benchmarks": {key: 0.0 for key, _ in _NEW_CATEGORIES},
                "error": str(e),
            }

    async def invalidate_cache(self, company_id: str) -> None:
        """
        特定企業のキャッシュを無効化

        Args:
            company_id: 企業ID
        """
        self._cache.pop(company_id, None)

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
                "last_review_date": aggregation_result["last_review_date"]
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
