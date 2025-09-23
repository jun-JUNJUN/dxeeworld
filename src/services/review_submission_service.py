"""
レビュー投稿システムサービス
"""
import html
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.models.review import Review, EmploymentStatus, ReviewCategory
from src.models.review_history import ReviewHistory, ReviewAction


class ReviewSubmissionService:
    """レビュー投稿・編集機能を担当するサービス"""

    def __init__(self, db_service=None, calculation_service=None):
        """
        Args:
            db_service: データベースサービス
            calculation_service: 計算サービス
        """
        self.db = db_service
        self.calc_service = calculation_service

    async def create_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レビューを投稿

        Args:
            review_data: レビューデータ

        Returns:
            投稿結果
        """
        try:
            # 1. バリデーション
            validation_errors = []

            # 評価値バリデーション
            rating_errors = self.calc_service.validate_rating_values(review_data["ratings"])
            if hasattr(rating_errors, '__await__'):
                rating_errors = await rating_errors
            validation_errors.extend(rating_errors)

            # 必須カテゴリーバリデーション
            category_errors = self.calc_service.validate_required_categories(review_data["ratings"])
            if hasattr(category_errors, '__await__'):
                category_errors = await category_errors
            validation_errors.extend(category_errors)

            if validation_errors:
                return {
                    "success": False,
                    "errors": validation_errors
                }

            # 2. 重複投稿チェック
            permission_check = await self.validate_review_permissions(
                review_data["user_id"],
                review_data["company_id"]
            )

            if not permission_check["can_create"]:
                return {
                    "success": False,
                    "error_code": "duplicate_review",
                    "existing_review_id": permission_check["existing_review_id"],
                    "days_until_next": permission_check["days_until_next"]
                }

            # 3. データサニタイズ
            sanitized_data = await self.sanitize_review_data(review_data)

            # 4. 平均点計算
            calc_result = self.calc_service.calculate_individual_average(sanitized_data["ratings"])
            if hasattr(calc_result, '__await__'):
                individual_average, answered_count = await calc_result
            else:
                individual_average, answered_count = calc_result

            # 5. Reviewオブジェクト構築
            review = await self.build_review_object(
                sanitized_data, individual_average, answered_count
            )

            # 6. データベース保存
            review_id = await self.db.create("reviews", review.to_dict())

            # 7. 履歴記録
            await self.create_review_history(
                review_id, review_data["user_id"], review_data["company_id"],
                ReviewAction.CREATE, None
            )

            # 8. 企業平均点再計算
            recalc_result = self.calc_service.recalculate_company_averages(review_data["company_id"])
            if hasattr(recalc_result, '__await__'):
                await recalc_result

            return {
                "success": True,
                "review_id": review_id,
                "individual_average": individual_average
            }

        except Exception as e:
            return {
                "success": False,
                "error_code": "database_error",
                "message": str(e)
            }

    async def validate_review_permissions(self, user_id: str, company_id: str) -> Dict[str, Any]:
        """
        レビュー投稿・更新権限をチェック

        Args:
            user_id: ユーザーID
            company_id: 企業ID

        Returns:
            権限情報
        """
        # 既存レビューを検索
        existing_review = await self.db.find_one(
            "reviews",
            {
                "user_id": user_id,
                "company_id": company_id,
                "is_active": True
            }
        )

        if not existing_review:
            return {
                "can_create": True,
                "can_update": False,
                "existing_review_id": None,
                "days_until_next": 0
            }

        # 1年経過チェック
        created_at = existing_review["created_at"]
        one_year_ago = datetime.utcnow() - timedelta(days=365)

        if created_at <= one_year_ago:
            # 1年経過済み - 新規投稿可能
            return {
                "can_create": True,
                "can_update": False,
                "existing_review_id": None,
                "days_until_next": 0
            }

        # 1年以内 - 更新のみ可能
        days_until_next = 365 - (datetime.utcnow() - created_at).days

        return {
            "can_create": False,
            "can_update": True,
            "existing_review_id": str(existing_review["_id"]),
            "days_until_next": days_until_next
        }

    async def sanitize_review_data(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レビューデータのサニタイズ処理

        Args:
            review_data: 生のレビューデータ

        Returns:
            サニタイズ済みデータ
        """
        sanitized = review_data.copy()

        # コメントのHTMLエスケープ
        if "comments" in sanitized:
            sanitized_comments = {}
            for category, comment in sanitized["comments"].items():
                if comment is not None and isinstance(comment, str):
                    sanitized_comments[category] = html.escape(comment)
                else:
                    sanitized_comments[category] = comment
            sanitized["comments"] = sanitized_comments

        return sanitized

    async def build_review_object(
        self,
        review_data: Dict[str, Any],
        individual_average: float,
        answered_count: int
    ) -> Review:
        """
        Reviewオブジェクトを構築

        Args:
            review_data: レビューデータ
            individual_average: 個別平均点
            answered_count: 回答項目数

        Returns:
            Reviewオブジェクト
        """
        now = datetime.utcnow()

        return Review(
            id="",  # データベース保存時に設定される
            company_id=review_data["company_id"],
            user_id=review_data["user_id"],
            employment_status=EmploymentStatus(review_data["employment_status"]),
            ratings=review_data["ratings"],
            comments=review_data["comments"],
            individual_average=individual_average,
            answered_count=answered_count,
            created_at=now,
            updated_at=now,
            is_active=True
        )

    async def create_review_history(
        self,
        review_id: str,
        user_id: str,
        company_id: str,
        action: ReviewAction,
        previous_data: Optional[Dict[str, Any]]
    ) -> str:
        """
        レビュー履歴を記録

        Args:
            review_id: レビューID
            user_id: ユーザーID
            company_id: 企業ID
            action: 操作種別
            previous_data: 更新前データ

        Returns:
            履歴ID
        """
        history = ReviewHistory(
            id="",  # データベース保存時に設定される
            review_id=review_id,
            user_id=user_id,
            company_id=company_id,
            action=action,
            previous_data=previous_data,
            timestamp=datetime.utcnow()
        )

        history_id = await self.db.create("review_history", history.to_dict())
        return history_id

    async def get_company_info(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        企業情報を取得

        Args:
            company_id: 企業ID

        Returns:
            企業情報
        """
        # モック実装
        return {
            "id": company_id,
            "name": "テスト企業",
            "location": "東京都"
        }

    async def check_review_permission(self, user_id: str, company_id: str) -> Dict[str, Any]:
        """
        レビュー投稿権限をチェック

        Args:
            user_id: ユーザーID
            company_id: 企業ID

        Returns:
            権限情報
        """
        # モック実装 - 常に投稿可能
        return {
            "can_create": True,
            "can_update": False,
            "existing_review_id": None,
            "days_until_next": 0
        }

    async def submit_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レビューを投稿

        Args:
            review_data: レビューデータ

        Returns:
            投稿結果
        """
        # モック実装
        return {
            "status": "success",
            "review_id": "new_review_id",
            "individual_average": 3.5
        }

    async def check_edit_permission(self, user_id: str, review_id: str) -> bool:
        """
        レビュー編集権限をチェック

        Args:
            user_id: ユーザーID
            review_id: レビューID

        Returns:
            編集可能かどうか
        """
        # モック実装 - 常に編集可能
        return True

    async def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """
        レビューを取得

        Args:
            review_id: レビューID

        Returns:
            レビューデータ
        """
        # モック実装
        return {
            "id": review_id,
            "company_id": "company1",
            "employment_status": "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": None,
                "employee_relations": 5,
                "evaluation_system": None,
                "promotion_treatment": 2
            },
            "comments": {
                "recommendation": "Great company",
                "foreign_support": "",
                "company_culture": None,
                "employee_relations": "Good relationships",
                "evaluation_system": None,
                "promotion_treatment": "Limited opportunities"
            },
            "individual_average": 3.5,
            "answered_count": 4,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1)
        }

    async def update_review(self, review_id: str, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レビューを更新

        Args:
            review_id: レビューID
            review_data: 新しいレビューデータ

        Returns:
            更新結果
        """
        # モック実装
        return {
            "status": "success",
            "individual_average": 3.2
        }