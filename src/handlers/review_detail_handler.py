"""
個別レビュー詳細ページハンドラー
Task 2: 個別レビュー詳細ページの実装
"""
import logging
from typing import Optional
import tornado.web
from bson import ObjectId
from bson.errors import InvalidId

from ..database import DatabaseService
from ..services.review_anonymization_service import ReviewAnonymizationService
from ..models.review import Review

logger = logging.getLogger(__name__)


class ReviewDetailHandler(tornado.web.RequestHandler):
    """個別レビュー詳細ページハンドラー"""

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

    async def get(self, company_id: str, review_id: str):
        """
        個別レビュー詳細ページ表示

        Args:
            company_id: 企業ID
            review_id: レビューID

        Returns:
            HTML: レビュー詳細ページ

        Raises:
            HTTPError(404): レビューまたは企業が見つからない場合
            HTTPError(500): データベースエラーの場合
        """
        try:
            logger.info(
                "Review detail page accessed: company_id=%s, review_id=%s",
                company_id,
                review_id
            )

            # Get access level from middleware (set by access_control_middleware decorator)
            access_level = getattr(self, 'current_user_access_level', 'FULL')

            # レビューを取得
            review = await self._get_review(company_id, review_id)
            if review is None:
                logger.info("Review not found: company_id=%s, review_id=%s", company_id, review_id)
                raise tornado.web.HTTPError(404, "レビューが見つかりません")

            # 企業名を取得
            company_name = await self._get_company_name(company_id)
            if company_name is None:
                logger.info("Company not found: company_id=%s", company_id)
                raise tornado.web.HTTPError(404, "企業が見つかりません")

            # レンダリング
            self._render_review_detail(review, company_name, access_level)

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.exception(
                "Failed to retrieve review: company_id=%s, review_id=%s, error=%s",
                company_id,
                review_id,
                str(e)
            )
            raise tornado.web.HTTPError(500, "サーバーエラーが発生しました")

    def _validate_object_id(self, id_string: str, id_type: str) -> Optional[ObjectId]:
        """
        ObjectId形式のバリデーションと変換

        Args:
            id_string: 変換する文字列
            id_type: IDのタイプ（ログ出力用、例: "review_id", "company_id"）

        Returns:
            ObjectId: 変換されたObjectId
            None: 無効な形式の場合
        """
        try:
            return ObjectId(id_string)
        except (InvalidId, TypeError):
            logger.warning("Invalid %s format: %s", id_type, id_string)
            return None

    async def _get_review(
        self,
        company_id: str,
        review_id: str
    ) -> Optional[Review]:
        """
        レビューを取得

        Args:
            company_id: 企業ID
            review_id: レビューID

        Returns:
            Review: レビューオブジェクト
            None: レビューが見つからない、または条件に合わない場合

        Raises:
            Exception: データベースエラーなど予期しないエラーの場合
        """
        # ObjectId形式に変換
        review_object_id = self._validate_object_id(review_id, "review_id")
        if review_object_id is None:
            return None

        # レビューを取得
        review_data = await self.db_service.find_one(
            "reviews",
            {"_id": review_object_id}
        )

        if review_data is None:
            return None

        # is_activeチェック
        if not review_data.get('is_active', True):
            logger.info("Review is inactive: review_id=%s", review_id)
            return None

        # company_id一致チェック
        if review_data.get('company_id') != company_id:
            logger.warning(
                "Company ID mismatch: expected=%s, actual=%s",
                company_id,
                review_data.get('company_id')
            )
            return None

        # Reviewオブジェクトに変換
        review = Review.from_dict(review_data)
        return review

    async def _get_company_name(self, company_id: str) -> Optional[str]:
        """
        企業名を取得

        Args:
            company_id: 企業ID

        Returns:
            str: 企業名
            None: 企業が見つからない場合

        Raises:
            Exception: データベースエラーなど予期しないエラーの場合
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

    def _render_review_detail(
        self,
        review: Review,
        company_name: str,
        access_level: str
    ):
        """
        レビュー詳細ページをレンダリング

        Args:
            review: レビューオブジェクト
            company_name: 企業名
            access_level: アクセスレベル (DENIED, PREVIEW, FULL, CRAWLER)
        """
        # アクセスレベルに基づいてプレビューモードを決定
        preview_mode = (access_level == "PREVIEW")

        # レビューを匿名化
        anonymized_review = self.anonymization_service.anonymize_review(
            review,
            preview_mode=preview_mode
        )

        # カテゴリ名の日本語ラベルマッピング
        category_labels = {
            "recommendation": "推薦度",
            "foreign_support": "受入制度",
            "company_culture": "会社風土",
            "employee_relations": "関係性",
            "evaluation_system": "評価制度",
            "promotion_treatment": "昇進待遇"
        }

        # テンプレートをレンダリング
        self.render(
            "review_detail.html",
            review=anonymized_review,
            company_name=company_name,
            company_id=review.company_id,
            preview_mode=preview_mode,
            access_level=access_level,
            category_labels=category_labels
        )
