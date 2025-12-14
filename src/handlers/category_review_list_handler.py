"""
質問別レビュー一覧ページハンドラー
Task 3: 質問別レビュー一覧ページの実装
"""
import logging
import math
from typing import List, Dict, Any, Optional
import tornado.web
from bson import ObjectId
from bson.errors import InvalidId

from ..database import DatabaseService
from ..services.review_anonymization_service import ReviewAnonymizationService
from ..models.review import Review
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class CategoryReviewListHandler(BaseHandler):
    """質問別レビュー一覧ページハンドラー"""

    # 有効なカテゴリ名のホワイトリスト
    VALID_CATEGORIES = {
        "recommendation",
        "foreign_support",
        "company_culture",
        "employee_relations",
        "evaluation_system",
        "promotion_treatment"
    }

    # カテゴリ名の日本語ラベルマッピング
    CATEGORY_LABELS = {
        "recommendation": "推薦度",
        "foreign_support": "受入制度",
        "company_culture": "会社風土",
        "employee_relations": "関係性",
        "evaluation_system": "評価制度",
        "promotion_treatment": "昇進待遇"
    }

    # 1ページあたりのレビュー件数
    REVIEWS_PER_PAGE = 20

    def initialize(
        self,
        db_service: DatabaseService,
        anonymization_service: ReviewAnonymizationService
    ):
        """
        ハンドラーの初期化

        Args:
            db_service: データベースサービス
            anonymization_service: 匿名化サービス
        """
        self.db_service = db_service
        self.anonymization_service = anonymization_service

    async def get(self, company_id: str, category_name: str):
        """
        質問別レビュー一覧ページ表示

        Args:
            company_id: 企業ID
            category_name: 評価項目名（recommendation, foreign_support, etc.）

        Query Parameters:
            page: ページ番号（デフォルト: 1）

        Returns:
            HTML: レビュー一覧ページ

        Raises:
            HTTPError(400): 無効なカテゴリ名またはページ番号の場合
            HTTPError(404): 企業が見つからない場合
            HTTPError(500): サーバーエラーの場合
        """
        try:
            logger.info(
                "Category review list accessed: company_id=%s, category=%s",
                company_id,
                category_name
            )

            # カテゴリ名のバリデーション
            if not self._validate_category_name(category_name):
                logger.warning("Invalid category name: %s", category_name)
                raise tornado.web.HTTPError(400, "無効な評価項目です")

            # ページ番号の取得とバリデーション
            try:
                page = int(self.get_argument("page", "1"))
                if page < 1:
                    raise ValueError("Page number must be positive")
            except (ValueError, TypeError) as e:
                logger.warning("Invalid page number: %s", self.get_argument("page", "1"))
                raise tornado.web.HTTPError(400, "無効なページ番号です")

            # 企業の存在確認
            company_name = await self._get_company_name(company_id)
            if company_name is None:
                logger.info("Company not found: company_id=%s", company_id)
                raise tornado.web.HTTPError(404, "企業が見つかりません")

            # アクセスレベルの取得
            access_level = getattr(self, 'current_user_access_level', 'FULL')

            # レビューリストの取得
            reviews, total_count = await self._get_reviews_for_category(
                company_id,
                category_name,
                page,
                self.REVIEWS_PER_PAGE
            )

            # ページネーション情報の計算
            pagination = self._calculate_pagination(page, total_count, self.REVIEWS_PER_PAGE)

            # レビューの匿名化
            preview_mode = (access_level == "PREVIEW")
            anonymized_reviews = []
            for review_data in reviews:
                review = Review.from_dict(review_data)
                anonymized_review = self.anonymization_service.anonymize_review(
                    review,
                    preview_mode=preview_mode
                )
                anonymized_reviews.append(anonymized_review)

            # カテゴリラベルの取得
            category_label = self._get_category_label(category_name)

            # レンダリング
            self.render(
                "category_review_list.html",
                reviews=anonymized_reviews,
                company_name=company_name,
                company_id=company_id,
                category_name=category_name,
                category_label=category_label,
                pagination=pagination,
                preview_mode=preview_mode,
                access_level=access_level
            )

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.exception(
                "Failed to retrieve category reviews: company_id=%s, category=%s, error=%s",
                company_id,
                category_name,
                str(e)
            )
            raise tornado.web.HTTPError(500, "サーバーエラーが発生しました")

    def _validate_category_name(self, category_name: str) -> bool:
        """
        カテゴリ名のバリデーション

        Args:
            category_name: 評価項目名

        Returns:
            bool: 有効な場合True
        """
        if category_name is None:
            return False
        return category_name in self.VALID_CATEGORIES

    def _get_category_label(self, category_name: str) -> str:
        """
        カテゴリ名の日本語ラベル取得

        Args:
            category_name: 評価項目名

        Returns:
            str: 日本語ラベル
        """
        return self.CATEGORY_LABELS.get(category_name, category_name)

    def _validate_object_id(self, id_string: str, id_type: str) -> Optional[ObjectId]:
        """
        ObjectId形式のバリデーションと変換

        Args:
            id_string: 変換する文字列
            id_type: IDのタイプ（ログ出力用）

        Returns:
            ObjectId: 変換されたObjectId
            None: 無効な形式の場合
        """
        try:
            return ObjectId(id_string)
        except (InvalidId, TypeError):
            logger.warning("Invalid %s format: %s", id_type, id_string)
            return None

    async def _get_company_name(self, company_id: str) -> Optional[str]:
        """
        企業名を取得

        Args:
            company_id: 企業ID

        Returns:
            str: 企業名
            None: 企業が見つからない場合
        """
        # ObjectId形式に変換
        company_object_id = self._validate_object_id(company_id, "company_id")
        if company_object_id is None:
            return None

        # 企業情報を取得
        company_data = await self.db_service.find_one(
            "companies",
            {"_id": company_object_id}
        )

        if company_data is None:
            return None

        return company_data.get('name')

    async def _get_reviews_for_category(
        self,
        company_id: str,
        category_name: str,
        page: int,
        per_page: int
    ) -> tuple[List[Dict], int]:
        """
        指定カテゴリのレビューを取得

        Args:
            company_id: 企業ID
            category_name: 評価項目名
            page: ページ番号
            per_page: 1ページあたりの件数

        Returns:
            tuple[List[Dict], int]: (レビューリスト, 総件数)
        """
        # クエリ条件の構築
        query = {
            "company_id": company_id,
            "is_active": True,
            f"ratings.{category_name}": {"$ne": None}  # カテゴリに回答があるレビューのみ
        }

        # 総件数の取得
        total_count = await self.db_service.count_documents("reviews", query)

        # skip/limitの計算
        skip = (page - 1) * per_page

        # レビューリストの取得（投稿日時降順）
        reviews = await self.db_service.find_many(
            "reviews",
            query,
            sort=[("created_at", -1)],
            skip=skip,
            limit=per_page
        )

        return reviews, total_count

    def _calculate_pagination(
        self,
        current_page: int,
        total_count: int,
        per_page: int
    ) -> Dict[str, Any]:
        """
        ページネーション情報の計算

        Args:
            current_page: 現在のページ番号
            total_count: 総レビュー数
            per_page: 1ページあたりの件数

        Returns:
            Dict[str, Any]: ページネーション情報
        """
        # 総ページ数の計算
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        # 前後ページの有無
        has_prev = current_page > 1
        has_next = current_page < total_pages

        # 前後ページ番号
        prev_page = current_page - 1 if has_prev else None
        next_page = current_page + 1 if has_next else None

        return {
            "current_page": current_page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": per_page,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": prev_page,
            "next_page": next_page
        }
