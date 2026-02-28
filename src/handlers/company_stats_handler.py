"""
企業統計情報ハンドラー（Task 8.4）

GET /companies/:id/stats

8カテゴリー集計データ・NPS・業界ベンチマークを JSON で返す。
"""
import json
import logging

from .base_handler import BaseHandler
from ..services.review_aggregation_service import ReviewAggregationService
from ..database import get_db_service

logger = logging.getLogger(__name__)


def _json_response(handler, data: dict, status: int = 200):
    """JSON レスポンスを書き出すユーティリティ"""
    handler.set_status(status)
    handler.set_header("Content-Type", "application/json; charset=utf-8")
    handler.write(json.dumps(data, ensure_ascii=False))


class CompanyStatsHandler(BaseHandler):
    """企業統計情報エンドポイント（GET /companies/:id/stats）"""

    def initialize(self):
        db_service = get_db_service()
        self.aggregation_service = ReviewAggregationService(db_service)

    async def get(self, company_id: str):
        """
        企業の集計統計データを返す

        Response JSON:
        {
          "overall_rating": 4.2,
          "nps_score": 75,
          "review_count": 125,
          "category_scores": {
            "compensation": 4.0,
            "work_life_balance": 4.5,
            "culture": 3.8,
            "career_development": 4.2,
            "management": 3.9,
            "performance_system": 3.5,
            "work_environment": 4.1,
            "business_product": 4.3
          },
          "industry_averages": { ... },
          "last_updated": "2026-02-17T08:00:00+00:00"
        }
        """
        try:
            if not company_id or not company_id.strip():
                self.set_status(400)
                _json_response(self, {"error": "Invalid company_id"}, 400)
                return

            # 企業集計データを取得
            stats = await self.aggregation_service.get_company_aggregations(company_id)

            if not stats.get("success"):
                _json_response(self, {"error": stats.get("error", "Aggregation failed")}, 500)
                return

            # 業界ベンチマークを取得
            benchmarks = await self.aggregation_service.get_industry_benchmarks()
            industry_averages = benchmarks.get("benchmarks", {})

            response = {
                "overall_rating": stats.get("overall_rating", 0.0),
                "nps_score": stats.get("nps_score", 0),
                "review_count": stats.get("review_count", 0),
                "category_scores": stats.get("category_scores", {}),
                "industry_averages": industry_averages,
                "last_updated": stats.get("last_updated", ""),
            }

            _json_response(self, response)

        except Exception as e:
            logger.exception("CompanyStatsHandler error for company %s: %s", company_id, e)
            _json_response(self, {"error": "Internal server error"}, 500)
