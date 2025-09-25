"""
レビュー関連ハンドラー
"""
import logging
import tornado.web
from .base_handler import BaseHandler
from ..services.review_submission_service import ReviewSubmissionService
from ..services.company_search_service import CompanySearchService

logger = logging.getLogger(__name__)


class ReviewListHandler(BaseHandler):
    """レビュー一覧表示ハンドラー (/review)"""

    def initialize(self):
        """ハンドラー初期化"""
        self.company_search_service = CompanySearchService()

    async def get(self):
        """レビュー一覧ページを表示"""
        try:
            # 検索パラメータを取得
            search_params = {
                "name": self.get_argument("name", ""),
                "location": self.get_argument("location", ""),
                "min_rating": self.get_argument("min_rating", None),
                "max_rating": self.get_argument("max_rating", None),
                "page": int(self.get_argument("page", "1")),
                "limit": int(self.get_argument("limit", "20")),
                "sort": self.get_argument("sort", "rating_high")
            }

            # 評価範囲の型変換
            if search_params["min_rating"]:
                search_params["min_rating"] = float(search_params["min_rating"])
            if search_params["max_rating"]:
                search_params["max_rating"] = float(search_params["max_rating"])

            # 企業検索実行
            search_result = await self.company_search_service.search_companies_with_reviews(search_params)

            # テンプレートレンダリング
            self.render("reviews/list.html",
                       companies=search_result["companies"],
                       pagination=search_result["pagination"],
                       search_params=search_params)

        except Exception as e:
            logger.error(f"Review list error: {e}")
            self.render("reviews/list.html",
                       companies=[],
                       pagination={"page": 1, "total": 0, "pages": 0},
                       search_params={})


class ReviewCreateHandler(BaseHandler):
    """レビュー投稿ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.review_service = ReviewSubmissionService()

    async def get(self, company_id):
        """Task 5.3: レビュー投稿フォーム表示"""
        try:
            # 企業IDの検証
            if not company_id or len(company_id.strip()) == 0:
                raise tornado.web.HTTPError(400, "無効な企業IDです")

            # 会社情報を取得
            company = await self.review_service.get_company_info(company_id)
            if not company:
                logger.warning(f"Company not found: {company_id}")
                raise tornado.web.HTTPError(404, "企業が見つかりません")

            # 投稿権限チェック（オプション：認証が不要な場合はスキップ）
            user_id = self.get_current_user_id()
            if user_id:  # 認証済みの場合のみ権限チェック
                try:
                    permission = await self.review_service.check_review_permission(user_id, company_id)
                    if not permission.get("can_create", True):  # デフォルトでは投稿可能
                        raise tornado.web.HTTPError(403, "このレビューの投稿権限がありません")
                except Exception as perm_error:
                    logger.warning(f"Permission check failed for user {user_id}, company {company_id}: {perm_error}")
                    # 権限チェックが失敗した場合でも投稿フォームは表示（デフォルト許可）

            # フォームレンダリング
            self.render("reviews/create.html",
                       company=company,
                       categories=self._get_review_categories(),
                       company_id=company_id)

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Review create form error for company {company_id}: {e}")
            raise tornado.web.HTTPError(500, "内部エラーが発生しました")

    async def post(self, company_id):
        """Task 5.3: レビュー投稿処理"""
        try:
            # 企業IDの検証
            if not company_id or len(company_id.strip()) == 0:
                raise tornado.web.HTTPError(400, "無効な企業IDです")

            # 認証必須
            user_id = await self.require_authentication()

            # フォームデータを解析
            review_data = self._parse_review_form()
            review_data["company_id"] = company_id
            review_data["user_id"] = user_id

            # バリデーション
            validation_errors = self._validate_review_data(review_data)
            if validation_errors:
                logger.warning(f"Review validation failed for company {company_id}: {validation_errors}")
                # バリデーションエラーの場合は422 Unprocessable Entity
                raise tornado.web.HTTPError(422, f"入力データが無効です: {', '.join(validation_errors)}")

            # レビュー投稿
            result = await self.review_service.submit_review(review_data)

            if result and result.get("status") == "success":
                logger.info(f"Review successfully submitted for company {company_id} by user {user_id}")
                # Task 5.3: 成功時は企業詳細ページにリダイレクト
                self.redirect(f"/companies/{company_id}")
            else:
                error_message = result.get("message", "レビューの投稿に失敗しました") if result else "レビューサービスでエラーが発生しました"
                logger.error(f"Review submission failed for company {company_id}: {error_message}")
                raise tornado.web.HTTPError(400, error_message)

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Review submission error for company {company_id}: {e}")
            raise tornado.web.HTTPError(500, "レビュー投稿中に内部エラーが発生しました")

    def _parse_review_form(self):
        """フォームデータを解析"""
        ratings = {}
        comments = {}

        # 6つのカテゴリーから評価とコメントを取得
        categories = ["recommendation", "foreign_support", "company_culture",
                     "employee_relations", "evaluation_system", "promotion_treatment"]

        for category in categories:
            # 評価点数（1-5 or None）
            rating_value = self.get_argument(f"ratings[{category}]", None)
            if rating_value and rating_value != "no_answer":
                ratings[category] = int(rating_value)
            else:
                ratings[category] = None

            # コメント
            comment_value = self.get_argument(f"comments[{category}]", "")
            comments[category] = comment_value if comment_value else None

        return {
            "employment_status": self.get_argument("employment_status"),
            "ratings": ratings,
            "comments": comments
        }

    def _validate_review_data(self, data):
        """レビューデータのバリデーション"""
        errors = []

        # 在職状況チェック
        if data["employment_status"] not in ["current", "former"]:
            errors.append("Invalid employment status")

        # 評価値チェック
        for category, rating in data["ratings"].items():
            if rating is not None:
                if not isinstance(rating, int) or rating < 1 or rating > 5:
                    errors.append(f"Invalid rating for {category}")

        # コメント長チェック
        for category, comment in data["comments"].items():
            if comment and len(comment) > 1000:
                errors.append(f"Comment too long for {category}")

        return errors

    def _get_review_categories(self):
        """レビューカテゴリー定義を取得"""
        categories = [
            {
                "key": "recommendation",
                "title": "推薦度合い",
                "question": "他の外国人に就業を推薦したい会社ですか？"
            },
            {
                "key": "foreign_support",
                "title": "外国人の受け入れ制度",
                "question": "外国人の受け入れ制度が整っていますか？"
            },
            {
                "key": "company_culture",
                "title": "会社風土",
                "question": "会社方針は明確で、文化的多様性を尊重していますか？"
            },
            {
                "key": "employee_relations",
                "title": "社員との関係性",
                "question": "上司・部下とも尊敬の念を持って関係が構築できますか？"
            },
            {
                "key": "evaluation_system",
                "title": "成果・評価制度",
                "question": "外国人従業員の成果が認められる制度が整っていますか？"
            },
            {
                "key": "promotion_treatment",
                "title": "昇進・昇給・待遇",
                "question": "昇進・昇給機会は平等に与えられていますか？"
            }
        ]
        # Add index to each category for Tornado template compatibility
        for i, category in enumerate(categories):
            category['index'] = i + 1
        return categories

    def get_current_user_id(self):
        """現在のユーザーIDを取得"""
        user_id = self.get_secure_cookie("user_id")
        if user_id:
            return user_id.decode('utf-8')
        return None

    async def require_authentication(self):
        """認証を要求し、ユーザー情報を返す"""
        user_id = self.get_current_user_id()
        if not user_id:
            raise tornado.web.HTTPError(401, "Authentication required")
        return user_id


class ReviewEditHandler(BaseHandler):
    """レビュー編集ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.review_service = ReviewSubmissionService()

    async def get(self, review_id):
        """レビュー編集フォーム表示"""
        try:
            # 認証必須
            user_id = await self.require_authentication()

            # 編集権限チェック
            has_permission = await self.review_service.check_edit_permission(user_id, review_id)
            if not has_permission:
                raise tornado.web.HTTPError(403, "Edit permission denied")

            # 既存レビューデータを取得
            review = await self.review_service.get_review(review_id)
            if not review:
                raise tornado.web.HTTPError(404, "Review not found")

            # 会社情報を取得
            company = await self.review_service.get_company_info(review["company_id"])

            # 編集フォームレンダリング
            self.render("reviews/edit.html",
                       review=review,
                       company=company,
                       categories=self._get_review_categories())

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Review edit form error: {e}")
            raise tornado.web.HTTPError(500, "Internal server error")

    async def post(self, review_id):
        """レビュー更新処理"""
        try:
            # 認証必須
            user_id = await self.require_authentication()

            # 編集権限チェック
            has_permission = await self.review_service.check_edit_permission(user_id, review_id)
            if not has_permission:
                raise tornado.web.HTTPError(403, "Edit permission denied")

            # フォームデータを解析
            review_data = self._parse_review_form()

            # バリデーション
            validation_errors = self._validate_review_data(review_data)
            if validation_errors:
                raise tornado.web.HTTPError(400, "Validation failed")

            # レビュー更新
            result = await self.review_service.update_review(review_id, review_data)

            if result["status"] == "success":
                # 成功時はレビュー詳細ページにリダイレクト
                self.redirect(f"/reviews/{review_id}")
            else:
                raise tornado.web.HTTPError(400, result.get("message", "Update failed"))

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Review update error: {e}")
            raise tornado.web.HTTPError(500, "Internal server error")

    def _parse_review_form(self):
        """フォームデータを解析（CreateHandlerと同じロジック）"""
        ratings = {}
        comments = {}

        categories = ["recommendation", "foreign_support", "company_culture",
                     "employee_relations", "evaluation_system", "promotion_treatment"]

        for category in categories:
            rating_value = self.get_argument(f"ratings[{category}]", None)
            if rating_value and rating_value != "no_answer":
                ratings[category] = int(rating_value)
            else:
                ratings[category] = None

            comment_value = self.get_argument(f"comments[{category}]", "")
            comments[category] = comment_value if comment_value else None

        return {
            "employment_status": self.get_argument("employment_status"),
            "ratings": ratings,
            "comments": comments
        }

    def _validate_review_data(self, data):
        """レビューデータのバリデーション（CreateHandlerと同じロジック）"""
        errors = []

        if data["employment_status"] not in ["current", "former"]:
            errors.append("Invalid employment status")

        for category, rating in data["ratings"].items():
            if rating is not None:
                if not isinstance(rating, int) or rating < 1 or rating > 5:
                    errors.append(f"Invalid rating for {category}")

        for category, comment in data["comments"].items():
            if comment and len(comment) > 1000:
                errors.append(f"Comment too long for {category}")

        return errors

    def _get_review_categories(self):
        """レビューカテゴリー定義を取得（CreateHandlerと同じ）"""
        categories = [
            {
                "key": "recommendation",
                "title": "推薦度合い",
                "question": "他の外国人に就業を推薦したい会社ですか？"
            },
            {
                "key": "foreign_support",
                "title": "外国人の受け入れ制度",
                "question": "外国人の受け入れ制度が整っていますか？"
            },
            {
                "key": "company_culture",
                "title": "会社風土",
                "question": "会社方針は明確で、文化的多様性を尊重していますか？"
            },
            {
                "key": "employee_relations",
                "title": "社員との関係性",
                "question": "上司・部下とも尊敬の念を持って関係が構築できますか？"
            },
            {
                "key": "evaluation_system",
                "title": "成果・評価制度",
                "question": "外国人従業員の成果が認められる制度が整っていますか？"
            },
            {
                "key": "promotion_treatment",
                "title": "昇進・昇給・待遇",
                "question": "昇進・昇給機会は平等に与えられていますか？"
            }
        ]
        # Add index to each category for Tornado template compatibility
        for i, category in enumerate(categories):
            category['index'] = i + 1
        return categories

    def get_current_user_id(self):
        """現在のユーザーIDを取得"""
        user_id = self.get_secure_cookie("user_id")
        if user_id:
            return user_id.decode('utf-8')
        return None

    async def require_authentication(self):
        """認証を要求し、ユーザー情報を返す"""
        user_id = self.get_current_user_id()
        if not user_id:
            raise tornado.web.HTTPError(401, "Authentication required")
        return user_id