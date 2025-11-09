"""
企業検索システムサービス
"""
import re
import math
from typing import Dict, List, Any, Optional


class CompanySearchService:
    """企業検索・フィルタリング機能を担当するサービス"""

    def __init__(self, db_service=None):
        """
        Args:
            db_service: データベースサービス
        """
        self.db = db_service

    async def search_companies(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        企業を検索・フィルタリング

        Args:
            search_params: 検索パラメータ

        Returns:
            検索結果
        """
        try:
            # パラメータバリデーション
            validation_errors = await self.validate_search_params(search_params)
            if validation_errors:
                return {
                    "success": False,
                    "error_code": "validation_error",
                    "errors": validation_errors
                }

            # 検索フィルタ構築
            search_filter = await self.build_search_filter(search_params)

            # ページネーション設定
            page = search_params.get("page", 1)
            per_page = min(search_params.get("per_page", 20), 100)
            skip = (page - 1) * per_page

            # ソート設定
            sort_order = await self.build_sort_order(search_params)

            # 総件数取得
            total_count = await self.db.count_documents("companies", search_filter)

            # 検索実行
            companies = await self.db.find_many(
                "companies",
                search_filter,
                skip=skip,
                limit=per_page,
                sort=sort_order
            )

            # ページネーション情報計算
            total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0

            return {
                "success": True,
                "companies": companies,
                "total_count": total_count,
                "current_page": page,
                "total_pages": total_pages,
                "per_page": per_page
            }

        except Exception as e:
            return {
                "success": False,
                "error_code": "database_error",
                "message": str(e)
            }

    async def build_search_filter(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        検索フィルタを構築

        Args:
            search_params: 検索パラメータ

        Returns:
            MongoDBフィルタ
        """
        search_filter = {
            # レビューサマリーが存在する企業のみ
            "review_summary": {"$exists": True}
        }

        # 企業名での部分一致検索
        if "name" in search_params and search_params["name"]:
            escaped_name = re.escape(search_params["name"])
            search_filter["name"] = {
                "$regex": escaped_name,
                "$options": "i"  # 大文字小文字を区別しない
            }

        # 所在地での検索
        if "location" in search_params and search_params["location"]:
            escaped_location = re.escape(search_params["location"])
            search_filter["location"] = {
                "$regex": escaped_location,
                "$options": "i"
            }

        # 評価点数範囲での絞り込み
        if "min_rating" in search_params or "max_rating" in search_params:
            rating_filter = {}

            if "min_rating" in search_params:
                rating_filter["$gte"] = search_params["min_rating"]

            if "max_rating" in search_params:
                rating_filter["$lte"] = search_params["max_rating"]

            if rating_filter:
                search_filter["review_summary.overall_average"] = rating_filter

        return search_filter

    async def build_sort_order(self, search_params: Dict[str, Any]) -> List[tuple]:
        """
        ソート順序を構築

        Args:
            search_params: 検索パラメータ

        Returns:
            ソート順序（MongoDBフォーマット）
        """
        sort_by = search_params.get("sort_by", "latest")

        # ソートフィールドとソート方向のマッピング
        sort_config_map = {
            "latest": ("review_summary.last_review_date", -1),        # 最新レビュー順（降順）
            "rating_high": ("review_summary.overall_average", -1),    # 評価順（高→低）
            "rating_low": ("review_summary.overall_average", 1),      # 評価順（低→高）
            "review_count": ("review_summary.total_reviews", -1),     # レビュー数順（降順）
            "name": ("name", 1)                                       # 企業名順（昇順）
        }

        # ソート設定を取得（デフォルトは最新レビュー順）
        sort_field, direction = sort_config_map.get(sort_by, sort_config_map["latest"])

        return [(sort_field, direction)]

    async def validate_search_params(self, search_params: Dict[str, Any]) -> List[str]:
        """
        検索パラメータのバリデーション

        Args:
            search_params: 検索パラメータ

        Returns:
            エラーメッセージリスト
        """
        errors = []

        # ページネーションパラメータの検証
        page = search_params.get("page", 1)
        if not isinstance(page, int) or page < 1:
            errors.append("Page must be a positive integer")

        per_page = search_params.get("per_page", 20)
        if not isinstance(per_page, int) or per_page < 1:
            errors.append("per_page must be a positive integer")

        # 評価範囲の検証
        min_rating = search_params.get("min_rating")
        max_rating = search_params.get("max_rating")

        if min_rating is not None:
            if not isinstance(min_rating, (int, float)) or min_rating < 0 or min_rating > 5:
                errors.append("Min rating must be between 0 and 5")

        if max_rating is not None:
            if not isinstance(max_rating, (int, float)) or max_rating < 0 or max_rating > 5:
                errors.append("Max rating must be between 0 and 5")

        if (min_rating is not None and max_rating is not None and
            min_rating > max_rating):
            errors.append("Min rating cannot be greater than max rating")

        return errors

    async def search_companies_with_reviews(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        レビュー情報付きで企業を検索

        Args:
            search_params: 検索パラメータ

        Returns:
            検索結果（レビュー情報含む）
        """
        # モック実装 - 実際の実装では検索結果を返す
        mock_companies = [
            {
                "id": "company1",
                "name": "テスト会社A",
                "location": "東京都",
                "overall_average": 3.2,
                "total_reviews": 15,
                "category_averages": {
                    "recommendation": 3.5,
                    "foreign_support": 2.8,
                    "company_culture": 3.1,
                    "employee_relations": 3.4,
                    "evaluation_system": 3.0,
                    "promotion_treatment": 2.9
                }
            }
        ]

        return {
            "companies": mock_companies,
            "pagination": {
                "page": search_params.get("page", 1),
                "limit": search_params.get("limit", 20),
                "total": len(mock_companies),
                "pages": 1
            }
        }