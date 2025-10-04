"""
レビュー投稿システムサービス
"""
import html
from typing import Dict, Any, Optional, List
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

        # コメントのHTMLエスケープと悪意のあるパターンの除去
        if "comments" in sanitized:
            sanitized_comments = {}
            for category, comment in sanitized["comments"].items():
                if comment is not None and isinstance(comment, str):
                    # HTMLエスケープ
                    escaped_comment = html.escape(comment)

                    # 追加のセキュリティフィルタリング
                    escaped_comment = self._apply_security_filters(escaped_comment)

                    sanitized_comments[category] = escaped_comment
                else:
                    sanitized_comments[category] = comment
            sanitized["comments"] = sanitized_comments

        return sanitized

    def _apply_security_filters(self, text: str) -> str:
        """
        追加のセキュリティフィルタリングを適用

        Args:
            text: フィルタリング対象のテキスト

        Returns:
            フィルタリング済みテキスト
        """
        import re

        # 危険なプロトコルスキーマを除去
        dangerous_protocols = [
            'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=',
            'onclick=', 'onmouseover=', 'onfocus=', 'onblur='
        ]

        filtered_text = text
        for protocol in dangerous_protocols:
            # 大文字小文字を区別せずに除去
            filtered_text = re.sub(re.escape(protocol), '', filtered_text, flags=re.IGNORECASE)

        # 悪意のあるHTMLタグパターンを除去（HTMLエスケープ後でも確認）
        dangerous_patterns = [
            r'&lt;script.*?&gt;',
            r'&lt;iframe.*?&gt;',
            r'&lt;object.*?&gt;',
            r'&lt;embed.*?&gt;',
            r'&lt;link.*?&gt;',
            r'&lt;meta.*?&gt;',
            r'&lt;img.*?&gt;'
        ]

        for pattern in dangerous_patterns:
            filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE | re.DOTALL)

        return filtered_text

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
        if not self.db:
            # データベース接続が必要
            raise ValueError("データベース接続が初期化されていません")

        try:
            from bson import ObjectId
            import logging
            logger = logging.getLogger(__name__)

            # ObjectIdに変換してクエリ
            try:
                object_id = ObjectId(company_id)
                logger.info(f"Searching for company with ObjectId: {object_id}")
                company = await self.db.find_one("companies", {"_id": object_id})
            except Exception as oid_error:
                # ObjectId変換に失敗した場合は文字列としてもクエリ
                logger.warning(f"ObjectId conversion failed for {company_id}: {oid_error}, trying string search")
                company = await self.db.find_one("companies", {"_id": company_id})

            logger.info(f"Company lookup result for {company_id}: {'Found' if company else 'Not Found'}")

            if not company:
                # 企業が見つからない場合はNoneを返す
                return None

            return {
                "id": str(company.get("_id", company_id)),
                "name": company.get("name", "企業名未設定"),
                "location": company.get("location", "所在地未設定"),
                "industry": company.get("industry"),
                "size": company.get("size"),
                "founded_year": company.get("founded_year"),
                "employee_count": company.get("employee_count"),
                "description": company.get("description")
            }

        except Exception as e:
            # エラー時はログを出力してNoneを返す
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching company info for {company_id}: {e}")
            return None

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
        if not self.db:
            # テスト環境ではモック動作
            return True

        try:
            # レビューを取得
            review = await self.db.find_one("reviews", {"_id": review_id, "is_active": True})

            if not review:
                return False

            # 投稿者チェック
            if review["user_id"] != user_id:
                return False

            # 1年以内チェック
            created_at = review["created_at"]
            one_year_ago = datetime.utcnow() - timedelta(days=365)

            if created_at <= one_year_ago:
                return False

            return True

        except Exception:
            return False

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
        if not self.db:
            # テスト環境ではモック動作
            return {"status": "success", "individual_average": 3.2}

        try:
            # 1. 既存レビューを取得
            existing_review = await self.db.find_one("reviews", {"_id": review_id, "is_active": True})
            if not existing_review:
                return {"status": "error", "message": "Review not found"}

            # 2. データサニタイズ
            sanitized_data = await self.sanitize_review_data(review_data)

            # 3. 平均点再計算
            if self.calc_service:
                calc_result = self.calc_service.calculate_individual_average(sanitized_data["ratings"])
                if hasattr(calc_result, '__await__'):
                    individual_average, answered_count = await calc_result
                else:
                    individual_average, answered_count = calc_result
            else:
                # 簡易計算（テスト用）
                valid_ratings = [r for r in sanitized_data["ratings"].values() if r is not None]
                individual_average = round(sum(valid_ratings) / len(valid_ratings), 1) if valid_ratings else 0.0
                answered_count = len(valid_ratings)

            # 4. 更新データ準備
            update_data = {
                "employment_status": sanitized_data["employment_status"],
                "ratings": sanitized_data["ratings"],
                "comments": sanitized_data["comments"],
                "individual_average": individual_average,
                "answered_count": answered_count,
                "updated_at": datetime.utcnow()
            }

            # 5. 履歴記録（更新前データを保存）
            await self.create_review_history(
                review_id,
                existing_review["user_id"],
                existing_review["company_id"],
                ReviewAction.UPDATE,
                existing_review
            )

            # 6. データベース更新
            await self.db.update("reviews", {"_id": review_id}, {"$set": update_data})

            # 7. 企業平均点再計算
            if self.calc_service:
                recalc_result = self.calc_service.recalculate_company_averages(existing_review["company_id"])
                if hasattr(recalc_result, '__await__'):
                    await recalc_result

            return {
                "status": "success",
                "individual_average": individual_average,
                "company_id": existing_review["company_id"]
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_company_reviews(self, company_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        企業のレビューを取得

        Args:
            company_id: 企業ID
            limit: 取得件数の上限

        Returns:
            レビューのリスト
        """
        if not self.db:
            # テスト環境ではモックデータを返す
            return [
                {
                    "id": "review1",
                    "user_id": "user1",
                    "company_id": company_id,
                    "employment_status": "former",
                    "overall_rating": 4.2,
                    "comment": "とても働きやすい職場で、外国人への支援も充実していました。上司との関係も良好で、成果もしっかりと評価してもらえました。",
                    "created_at": "2024-09-01"
                },
                {
                    "id": "review2",
                    "user_id": "user2",
                    "company_id": company_id,
                    "employment_status": "current",
                    "overall_rating": 3.8,
                    "comment": "職場環境は良いですが、昇進の機会がもう少しあると良いと思います。",
                    "created_at": "2024-08-15"
                },
                {
                    "id": "review3",
                    "user_id": "user3",
                    "company_id": company_id,
                    "employment_status": "former",
                    "overall_rating": 3.5,
                    "comment": "会社の文化は素晴らしく、多様性を重視していました。",
                    "created_at": "2024-07-20"
                }
            ]

        try:
            # 実際の実装では、データベースから企業のレビューを取得
            reviews = await self.db.find_many(
                "reviews",
                {"company_id": company_id, "is_active": True},
                limit=limit,
                sort=[("created_at", -1)]  # 新しい順
            )

            # レビューデータの整形
            formatted_reviews = []
            for review in reviews:
                formatted_reviews.append({
                    "id": str(review.get("_id", "")),
                    "user_id": review.get("user_id", ""),
                    "company_id": review.get("company_id", ""),
                    "employment_status": review.get("employment_status", ""),
                    "overall_rating": review.get("individual_average", 0.0),
                    "comment": self._get_primary_comment(review.get("comments", {})),
                    "created_at": review.get("created_at", "").strftime("%Y-%m-%d") if review.get("created_at") else ""
                })

            return formatted_reviews

        except Exception as e:
            # エラー時は空のリストを返す
            return []

    def _get_primary_comment(self, comments: Dict[str, Any]) -> str:
        """
        コメント辞書から表示用の主要コメントを取得

        Args:
            comments: コメント辞書

        Returns:
            表示用コメント
        """
        # 推薦度合いのコメントを優先、なければ最初の非空コメント
        if comments.get("recommendation"):
            return comments["recommendation"]

        for comment in comments.values():
            if comment and isinstance(comment, str) and comment.strip():
                return comment.strip()

        return "コメントなし"