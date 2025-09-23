"""
検索結果表示・ソート機能サービス
"""
from typing import Dict, List, Any


class SearchResultService:
    """検索結果の表示・ソート・ページネーション機能を担当するサービス"""

    def __init__(self, search_service):
        """
        Args:
            search_service: 企業検索サービス
        """
        self.search_service = search_service

    async def get_sorted_search_results(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ソート済み検索結果を取得

        Args:
            search_params: 検索・ソートパラメータ

        Returns:
            ソート済み検索結果
        """
        try:
            # ソートパラメータを正規化
            normalized_params = await self.validate_and_normalize_sort_params(search_params)

            # 検索実行
            search_result = await self.search_service.search_companies(normalized_params)

            if not search_result["success"]:
                return search_result

            # 結果をフォーマット
            formatted_companies = await self.format_search_results(search_result["companies"])

            return {
                "success": True,
                "companies": formatted_companies,
                "total_count": search_result["total_count"],
                "current_page": search_result.get("current_page", 1),
                "total_pages": search_result.get("total_pages", 1),
                "per_page": search_result.get("per_page", 20),
                "sort_by": normalized_params["sort_by"],
                "sort_direction": normalized_params["sort_direction"]
            }

        except Exception as e:
            return {
                "success": False,
                "error_code": "result_processing_error",
                "message": str(e)
            }

    async def get_paginated_results(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ページネーション付き検索結果を取得

        Args:
            search_params: 検索パラメータ

        Returns:
            ページネーション情報付き検索結果
        """
        result = await self.get_sorted_search_results(search_params)

        if result["success"]:
            # ページネーション情報を追加
            current_page = result["current_page"]
            total_pages = result["total_pages"]

            result["has_previous"] = current_page > 1
            result["has_next"] = current_page < total_pages

            # ページナビゲーション情報
            result["page_info"] = {
                "current": current_page,
                "total": total_pages,
                "has_prev": result["has_previous"],
                "has_next": result["has_next"],
                "prev_page": current_page - 1 if result["has_previous"] else None,
                "next_page": current_page + 1 if result["has_next"] else None
            }

        return result

    async def format_search_results(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        検索結果を表示用にフォーマット

        Args:
            companies: 生の企業データリスト

        Returns:
            フォーマット済み企業データリスト
        """
        formatted_companies = []

        for company in companies:
            formatted_company = {
                "id": str(company["_id"]),
                "name": company["name"],
                "location": company.get("location", ""),
                "overall_average": 0.0,
                "total_reviews": 0,
                "category_averages": {},
                "last_updated": None,
                "display_summary": ""
            }

            # レビューサマリー情報の処理
            review_summary = company.get("review_summary")
            if review_summary:
                formatted_company["overall_average"] = review_summary.get("overall_average", 0.0)
                formatted_company["total_reviews"] = review_summary.get("total_reviews", 0)
                formatted_company["category_averages"] = review_summary.get("category_averages", {})
                formatted_company["last_updated"] = review_summary.get("last_updated")

            # 表示用サマリーを生成
            formatted_company["display_summary"] = await self.build_display_summary(company)

            formatted_companies.append(formatted_company)

        return formatted_companies

    async def build_display_summary(self, company_data: Dict[str, Any]) -> str:
        """
        企業の表示用サマリーを構築

        Args:
            company_data: 企業データ

        Returns:
            表示用サマリー文字列
        """
        review_summary = company_data.get("review_summary")

        if not review_summary:
            return "レビューなし - まだ評価が投稿されていません"

        overall_avg = review_summary.get("overall_average", 0.0)
        total_reviews = review_summary.get("total_reviews", 0)

        if total_reviews == 0:
            return "レビューなし - まだ評価が投稿されていません"

        summary_parts = [
            f"総合評価: {overall_avg:.1f}/5.0",
            f"({total_reviews}件のレビュー)"
        ]

        # 主要カテゴリーの評価を追加
        category_averages = review_summary.get("category_averages", {})
        if "recommendation" in category_averages:
            rec_avg = category_averages["recommendation"]
            summary_parts.append(f"総合推薦度: {rec_avg:.1f}")

        return " | ".join(summary_parts)

    async def validate_and_normalize_sort_params(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ソートパラメータの検証と正規化

        Args:
            search_params: 検索パラメータ

        Returns:
            正規化されたパラメータ
        """
        normalized_params = search_params.copy()

        # 有効なソートフィールド
        valid_sort_fields = {
            "overall_average", "total_reviews", "last_updated", "name"
        }

        # ソートフィールドの正規化
        sort_by = search_params.get("sort_by", "overall_average")
        if sort_by not in valid_sort_fields:
            sort_by = "overall_average"
        normalized_params["sort_by"] = sort_by

        # ソート方向の正規化
        sort_direction = search_params.get("sort_direction", "desc")
        if sort_direction.lower() not in ["asc", "desc"]:
            sort_direction = "desc"
        normalized_params["sort_direction"] = sort_direction.lower()

        return normalized_params

    async def get_sort_options(self) -> Dict[str, Any]:
        """
        利用可能なソートオプションを取得

        Returns:
            ソートオプション情報
        """
        return {
            "sort_fields": [
                {"value": "overall_average", "label": "総合評価", "default": True},
                {"value": "total_reviews", "label": "レビュー数", "default": False},
                {"value": "last_updated", "label": "最終更新日", "default": False},
                {"value": "name", "label": "企業名", "default": False}
            ],
            "sort_directions": [
                {"value": "desc", "label": "降順", "default": True},
                {"value": "asc", "label": "昇順", "default": False}
            ]
        }

    async def build_pagination_info(
        self,
        current_page: int,
        total_pages: int,
        per_page: int,
        total_count: int
    ) -> Dict[str, Any]:
        """
        詳細なページネーション情報を構築

        Args:
            current_page: 現在のページ
            total_pages: 総ページ数
            per_page: ページあたり件数
            total_count: 総件数

        Returns:
            詳細ページネーション情報
        """
        start_item = (current_page - 1) * per_page + 1
        end_item = min(current_page * per_page, total_count)

        # ページ範囲計算（前後2ページまで表示）
        page_range_start = max(1, current_page - 2)
        page_range_end = min(total_pages, current_page + 2)

        return {
            "current_page": current_page,
            "total_pages": total_pages,
            "per_page": per_page,
            "total_count": total_count,
            "start_item": start_item,
            "end_item": end_item,
            "has_previous": current_page > 1,
            "has_next": current_page < total_pages,
            "previous_page": current_page - 1 if current_page > 1 else None,
            "next_page": current_page + 1 if current_page < total_pages else None,
            "page_range": list(range(page_range_start, page_range_end + 1)),
            "show_first": page_range_start > 1,
            "show_last": page_range_end < total_pages
        }