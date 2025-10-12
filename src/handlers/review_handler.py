"""
レビュー関連ハンドラー
"""

import logging
import tornado.web
import traceback
from .base_handler import BaseHandler
from ..services.review_submission_service import ReviewSubmissionService
from ..services.company_search_service import CompanySearchService
from ..services.review_calculation_service import ReviewCalculationService
from ..database import get_db_service

logger = logging.getLogger(__name__)


class ReviewListHandler(BaseHandler):
    """レビュー一覧表示ハンドラー (/review)"""

    def initialize(self):
        """ハンドラー初期化"""
        self.company_search_service = CompanySearchService()
        # Task 2.4: AccessControlMiddleware統合
        from ..middleware.access_control_middleware import AccessControlMiddleware

        self.access_control = AccessControlMiddleware()

    @staticmethod
    def truncate_comment_for_preview(comment: str, max_chars: int = 128) -> dict:
        """
        レビューコメントをプレビュー用に切り詰める

        Args:
            comment: レビューコメント
            max_chars: 最大表示文字数（デフォルト: 128）

        Returns:
            dict: {
                "visible_text": 表示する部分（最初の1行または最初のmax_chars文字）,
                "masked_text": 伏せ字部分（"●●●●●"）,
                "has_more": 続きがあるか（bool）
            }
        """
        if not comment:
            return {"visible_text": "", "masked_text": "", "has_more": False}

        # コメントを改行で分割し、最初の1行を取得
        lines = comment.split("\n")
        first_line = lines[0]

        # 最初の1行がmax_chars以下の場合
        if len(first_line) <= max_chars:
            # 2行目以降がある場合は伏せ字を追加
            if len(lines) > 1 or len(first_line) < len(comment):
                return {"visible_text": first_line, "masked_text": "●●●●●", "has_more": True}
            else:
                # 1行のみでmax_chars以下の場合、伏せ字なし
                return {"visible_text": first_line, "masked_text": "", "has_more": False}
        else:
            # 最初の1行がmax_charsを超える場合、max_chars文字で切り詰め
            return {
                "visible_text": first_line[:max_chars],
                "masked_text": "●●●●●",
                "has_more": True,
            }

    async def get(self):
        """Task 2.4: レビュー一覧ページを表示 - アクセス制御とフィルター統合"""
        try:
            # Task 2.4: アクセス制御チェック
            session_id = self.get_secure_cookie("session_id")
            if session_id:
                session_id = session_id.decode("utf-8")

            # ユーザーIDを取得
            user_id = None
            if session_id:
                from ..services.session_service import SessionService

                session_service = SessionService()
                session_result = await session_service.validate_session(session_id)
                if session_result.is_success:
                    user_id = session_result.data.get("identity_id")

            # アクセスレベルの判定
            access_result = await self.access_control.check_review_list_access(user_id)
            access_level = access_result.get("access_level", "preview")
            can_filter = access_result.get("can_filter", False)

            # Task 2.4: アクセスレベルに応じた処理
            if access_level == "denied":
                # アクセス拒否メッセージを表示
                self.render(
                    "reviews/list.html",
                    companies=[],
                    pagination={"page": 1, "total": 0, "pages": 0},
                    search_params={},
                    access_level=access_level,
                    can_filter=False,
                    access_message=access_result.get("message", ""),
                )
                return

            # 検索パラメータを取得
            search_params = {
                "name": self.get_argument("name", ""),
                "location": self.get_argument("location", ""),
                "min_rating": self.get_argument("min_rating", None),
                "max_rating": self.get_argument("max_rating", None),
                "page": int(self.get_argument("page", "1")),
                "limit": int(self.get_argument("limit", "20")),
                "sort": self.get_argument("sort", "rating_high"),
            }

            # Task 2.4: フィルターはcan_filter=Trueの場合のみ適用
            if not can_filter:
                # フィルターを無効化
                search_params["name"] = ""
                search_params["location"] = ""
                search_params["min_rating"] = None
                search_params["max_rating"] = None

            # 評価範囲の型変換
            if search_params["min_rating"]:
                search_params["min_rating"] = float(search_params["min_rating"])
            if search_params["max_rating"]:
                search_params["max_rating"] = float(search_params["max_rating"])

            # 企業検索実行
            search_result = await self.company_search_service.search_companies_with_reviews(
                search_params
            )

            # テンプレートレンダリング
            self.render(
                "reviews/list.html",
                companies=search_result["companies"],
                pagination=search_result["pagination"],
                search_params=search_params,
                access_level=access_level,
                can_filter=can_filter,
                access_message=access_result.get("message", ""),
            )

        except Exception as e:
            logger.error(f"Review list error: {e}")
            self.render(
                "reviews/list.html",
                companies=[],
                pagination={"page": 1, "total": 0, "pages": 0},
                search_params={},
                access_level="preview",
                can_filter=False,
                access_message="",
            )


class ReviewCreateHandler(BaseHandler):
    """レビュー投稿ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.db_service = get_db_service()
        self.calc_service = ReviewCalculationService()
        self.review_service = ReviewSubmissionService(
            db_service=self.db_service, calculation_service=self.calc_service
        )
        # Task 4.2: AccessControlMiddleware統合
        from ..middleware.access_control_middleware import AccessControlMiddleware

        # Task 3.2: I18nFormService統合
        from ..services.i18n_form_service import I18nFormService

        # Task 6.1: TranslationService統合
        from ..services.translation_service import TranslationService

        self.access_control = AccessControlMiddleware()
        self.i18n_service = I18nFormService()
        self.translation_service = TranslationService()

    async def get(self, company_id):
        """Task 4.2: レビュー投稿フォーム表示 - AccessControlMiddleware統合"""
        try:
            logger.info(f"ReviewCreateHandler.get called for company_id: {company_id}")
            traceback.print_stack()

            # 企業IDの検証
            if not company_id or len(company_id.strip()) == 0:
                raise tornado.web.HTTPError(400, "無効な企業IDです")

            # 会社情報を取得（認証チェック前に取得、Mini Panel表示時にも必要）
            company = await self.review_service.get_company_info(company_id)
            if not company:
                logger.warning(f"Company not found: {company_id}")
                raise tornado.web.HTTPError(404, "企業が見つかりません")

            # Task 4.2: AccessControlMiddlewareによる認証チェック
            session_id = self.get_secure_cookie("session_id")
            if session_id:
                session_id = session_id.decode("utf-8")

            access_result = await self.access_control.check_access(
                self.request.path, session_id, self.request.remote_ip
            )

            # デバッグログ: アクセス制御結果を出力
            logger.info(
                f"D-00006: Access control result - is_success: {access_result.is_success}, data: {access_result.data if access_result.is_success else 'N/A'}, session_id: {session_id}, path: {self.request.path}"
            )

            # 未認証の場合、ログインページにリダイレクト
            if not access_result.is_success:
                logger.info(
                    f"D-00005:Unauthenticated access to review creation for company {company_id}, redirecting to login"
                )
                import urllib.parse

                return_url = self.request.uri
                login_url = f"/auth/email/login?return_url={urllib.parse.quote(return_url)}"
                self.redirect(login_url)
                return

            # access_granted チェック（access_result.is_success が True の場合のみ）
            if not access_result.data.get("access_granted", False):
                logger.info(
                    f"D-00005:Access denied for review creation for company {company_id}, redirecting to login"
                )
                import urllib.parse

                return_url = self.request.uri
                login_url = f"/auth/email/login?return_url={urllib.parse.quote(return_url)}"
                self.redirect(login_url)
                return

            # 認証済みの場合、通常のレビューフォームを表示
            user_context = access_result.data.get("user_context") or {}
            logger.info(f"D-00005: user has a session {user_context}")
            user_id = user_context.get("identity_id")

            # 投稿権限チェック（認証済みユーザーのみ）
            try:
                permission = await self.review_service.check_review_permission(user_id, company_id)
                if not permission.get("can_create", True):  # デフォルトでは投稿可能
                    raise tornado.web.HTTPError(403, "このレビューの投稿権限がありません")
            except Exception as perm_error:
                logger.warning(
                    f"Permission check failed for user {user_id}, company {company_id}: {perm_error}"
                )
                # 権限チェックが失敗した場合でも投稿フォームは表示（デフォルト許可）

            # Task 3.2: ブラウザ言語検出と翻訳辞書取得
            import tornado.escape

            accept_language = self.request.headers.get("Accept-Language", "")
            default_language = self.i18n_service.detect_browser_language(accept_language)
            translations = self.i18n_service.get_form_translations()
            supported_languages = self.i18n_service.get_supported_languages()

            # フォームレンダリング（認証済み）
            self.render(
                "reviews/create.html",
                company=company,
                categories=self._get_review_categories(),
                company_id=company_id,
                show_login_panel=False,
                review_form_visible=True,
                default_language=default_language,
                translations=tornado.escape.json_encode(
                    translations
                ),  # JSON文字列に変換（エスケープなし）
                supported_languages=supported_languages,
            )

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.exception(f"Review create form error for company {company_id}: {e}")
            raise tornado.web.HTTPError(500, "内部エラーが発生しました")

    async def post(self, company_id):
        """Task 7.1: レビュー投稿処理 - 多言語データ保存対応"""
        try:
            # 企業IDの検証
            if not company_id or len(company_id.strip()) == 0:
                raise tornado.web.HTTPError(400, "無効な企業IDです")

            # 認証必須
            user_id = await self.require_authentication()

            # モード判定: confirm=1の場合は確認画面を表示
            mode = self.get_argument("mode", "")

            # フォームデータを解析
            review_data = self._parse_review_form()
            review_data["company_id"] = company_id
            review_data["user_id"] = user_id

            # バリデーション
            validation_errors = self._validate_review_data(review_data)
            if validation_errors:
                logger.warning(
                    f"Review validation failed for company {company_id}: {validation_errors}"
                )
                # バリデーションエラーの場合は422 Unprocessable Entity
                raise tornado.web.HTTPError(
                    422, f"入力データが無効です: {', '.join(validation_errors)}"
                )

            # Task 6.1: 確認画面モード
            if mode == "preview":
                await self._show_confirmation_screen(company_id, review_data)
                return

            # Task 7.1: 投稿モード（mode="submit"）- 多言語データ保存
            if mode == "submit":
                # Task 7.1: 選択言語を取得
                selected_language = self.get_argument("selected_language", "ja")
                review_data["language"] = selected_language

                # Task 7.1: 元言語以外の2言語に翻訳して保存
                translated_comments_all = {}
                target_languages = []

                # 元言語に応じて翻訳先言語を決定
                if selected_language == "ja":
                    target_languages = ["en", "zh"]  # 日本語 → 英語 + 中国語
                elif selected_language == "en":
                    target_languages = ["ja", "zh"]  # 英語 → 日本語 + 中国語
                elif selected_language == "zh":
                    target_languages = ["ja", "en"]  # 中国語 → 日本語 + 英語
                else:
                    # デフォルト: 日本語を選択言語とする
                    selected_language = "ja"
                    target_languages = ["en", "zh"]

                # 各言語への翻訳
                for target_lang in target_languages:
                    translated_comments_all[target_lang] = {}
                    for category, comment in review_data["comments"].items():
                        if comment:
                            translation_result = await self.translation_service.translate_text(
                                text=comment,
                                source_lang=selected_language,
                                target_lang=target_lang,
                                context="company review",
                            )
                            if translation_result.is_success:
                                translated_comments_all[target_lang][category] = (
                                    translation_result.data
                                )
                            else:
                                # 翻訳失敗時はログ出力のみ（Graceful Degradation）
                                logger.warning(
                                    f"Translation failed for {category} to {target_lang}: {translation_result.error}"
                                )
                                translated_comments_all[target_lang][category] = None
                        else:
                            translated_comments_all[target_lang][category] = None

                # Task 7.1: 翻訳データをreview_dataに追加
                review_data["comments_ja"] = translated_comments_all.get("ja")
                review_data["comments_en"] = translated_comments_all.get("en")
                review_data["comments_zh"] = translated_comments_all.get("zh")

                # レビュー投稿
                result = await self.review_service.submit_review(review_data)

                if result and result.get("status") == "success":
                    logger.info(
                        f"Review successfully submitted for company {company_id} by user {user_id}"
                    )
                    # Task 8.1: 投稿成功メッセージを設定
                    self.set_flash_message(
                        "Review投稿しました。ありがとうございました。", "success"
                    )
                    # Task 5.3: 成功時は企業詳細ページにリダイレクト
                    self.redirect(f"/companies/{company_id}")
                else:
                    # Task 8.2: 投稿失敗時のエラーハンドリング
                    error_message = (
                        result.get("message", "レビューの投稿に失敗しました")
                        if result
                        else "レビューサービスでエラーが発生しました"
                    )
                    logger.error(
                        f"Review submission failed for company {company_id}: {error_message}"
                    )
                    # Task 8.2: エラー発生時にユーザーを確認画面に留める
                    # 確認画面を再表示し、エラーメッセージを表示
                    company = await self.review_service.get_company_info(company_id)
                    self.render(
                        "reviews/confirm.html",
                        company=company,
                        review_data=review_data,
                        translated_comments={},  # 翻訳データは再取得不要
                        translated_comments_all={"ja": {}, "en": {}, "zh": {}},
                        selected_language=review_data.get("language", "ja"),
                        categories=self._get_review_categories(),
                        error_message=error_message,  # Task 8.2: エラーメッセージを渡す
                    )
                    return
            else:
                # モード不明の場合はエラー
                raise tornado.web.HTTPError(400, "Invalid mode parameter")

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Review submission error for company {company_id}: {e}")
            raise tornado.web.HTTPError(500, "レビュー投稿中に内部エラーが発生しました")

    async def _show_confirmation_screen(self, company_id: str, review_data: dict):
        """Task 6: 確認画面を表示 - 3言語すべての翻訳対応"""
        try:
            # 会社情報を取得
            company = await self.review_service.get_company_info(company_id)
            if not company:
                raise tornado.web.HTTPError(404, "企業が見つかりません")

            # 選択された言語を取得
            selected_language = self.get_argument("selected_language", "ja")

            # Task 6: 元言語以外の2言語に翻訳
            translated_comments_all = {}
            target_languages = []

            # 元言語に応じて翻訳先言語を決定
            if selected_language == "ja":
                target_languages = ["en", "zh"]  # 日本語 → 英語 + 中国語
            elif selected_language == "en":
                target_languages = ["ja", "zh"]  # 英語 → 日本語 + 中国語
            elif selected_language == "zh":
                target_languages = ["ja", "en"]  # 中国語 → 日本語 + 英語

            # 各言語への翻訳
            for target_lang in target_languages:
                translated_comments_all[target_lang] = {}
                for category, comment in review_data["comments"].items():
                    if comment:
                        translation_result = await self.translation_service.translate_text(
                            text=comment,
                            source_lang=selected_language,
                            target_lang=target_lang,
                            context="company review",
                        )
                        if translation_result.is_success:
                            translated_comments_all[target_lang][category] = translation_result.data
                        else:
                            # 翻訳失敗時は元のテキストを使用（Graceful Degradation）
                            logger.warning(
                                f"Translation failed for {category} to {target_lang}, using original text: {translation_result.error}"
                            )
                            translated_comments_all[target_lang][category] = f"[翻訳失敗] {comment}"
                    else:
                        translated_comments_all[target_lang][category] = None

            # 後方互換性のため、translated_commentsも渡す（日本語翻訳）
            translated_comments = translated_comments_all.get("ja", review_data["comments"].copy())

            # 確認画面をレンダリング
            self.render(
                "reviews/confirm.html",
                company=company,
                review_data=review_data,
                translated_comments=translated_comments,  # 後方互換性
                translated_comments_all=translated_comments_all,  # 3言語すべて
                selected_language=selected_language,
                categories=self._get_review_categories(),
            )

        except Exception as e:
            logger.exception(f"Failed to show confirmation screen: {e}")
            raise tornado.web.HTTPError(500, "確認画面の表示に失敗しました")

    def _parse_review_form(self):
        """フォームデータを解析"""
        ratings = {}
        comments = {}

        # 6つのカテゴリーから評価とコメントを取得
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

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
            "comments": comments,
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
                "question": "他の外国人に就業を推薦したい会社ですか？",
            },
            {
                "key": "foreign_support",
                "title": "外国人の受け入れ制度",
                "question": "外国人の受け入れ制度が整っていますか？",
            },
            {
                "key": "company_culture",
                "title": "会社風土",
                "question": "会社方針は明確で、文化的多様性を尊重していますか？",
            },
            {
                "key": "employee_relations",
                "title": "社員との関係性",
                "question": "上司・部下とも尊敬の念を持って関係が構築できますか？",
            },
            {
                "key": "evaluation_system",
                "title": "成果・評価制度",
                "question": "外国人従業員の成果が認められる制度が整っていますか？",
            },
            {
                "key": "promotion_treatment",
                "title": "昇進・昇給・待遇",
                "question": "昇進・昇給機会は平等に与えられていますか？",
            },
        ]
        # Add index to each category for Tornado template compatibility
        for i, category in enumerate(categories):
            category["index"] = i + 1
        return categories


class ReviewEditHandler(BaseHandler):
    """レビュー編集ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.db_service = get_db_service()
        self.calc_service = ReviewCalculationService()
        self.review_service = ReviewSubmissionService(
            db_service=self.db_service, calculation_service=self.calc_service
        )
        # Task 4.3: AccessControlMiddleware統合
        from ..middleware.access_control_middleware import AccessControlMiddleware

        self.access_control = AccessControlMiddleware()

    async def get(self, review_id):
        """Task 4.3: レビュー編集フォーム表示 - AccessControlMiddleware統合"""
        try:
            # 既存レビューデータを取得（認証チェック前に取得、Mini Panel表示時にも必要）
            review = await self.review_service.get_review(review_id)
            if not review:
                raise tornado.web.HTTPError(404, "Review not found")

            # 会社情報を取得
            company = await self.review_service.get_company_info(review["company_id"])

            # Task 4.3: AccessControlMiddlewareによる認証チェック
            session_id = self.get_secure_cookie("session_id")
            if session_id:
                session_id = session_id.decode("utf-8")

            access_result = await self.access_control.check_access(
                self.request.path, session_id, self.request.remote_ip
            )

            # 未認証の場合、Mini Panelを表示して編集フォームを非表示
            if not access_result.is_success:
                logger.info(f"Unauthenticated access to review editing for review {review_id}")
                self.render(
                    "reviews/edit.html",
                    review=review,
                    company=company,
                    categories=self._get_review_categories(),
                    show_login_panel=True,
                    review_form_visible=False,
                )
                return

            # access_granted チェック（access_result.is_success が True の場合のみ）
            if not access_result.data.get("access_granted", False):
                logger.info(f"Access denied for review editing for review {review_id}")
                self.render(
                    "reviews/edit.html",
                    review=review,
                    company=company,
                    categories=self._get_review_categories(),
                    show_login_panel=True,
                    review_form_visible=False,
                )
                return

            # 認証済みの場合、編集権限チェック
            user_context = access_result.data.get("user_context") or {}
            user_id = user_context.get("identity_id")

            # 編集権限チェック
            has_permission = await self.review_service.check_edit_permission(user_id, review_id)
            if not has_permission:
                raise tornado.web.HTTPError(403, "Edit permission denied")

            # 編集フォームレンダリング（認証済み）
            self.render(
                "reviews/edit.html",
                review=review,
                company=company,
                categories=self._get_review_categories(),
                show_login_panel=False,
                review_form_visible=True,
            )

        except tornado.web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Review edit form error for review {review_id}: {e}")
            raise tornado.web.HTTPError(500, "内部エラーが発生しました")

    def _get_review_categories(self):
        """レビューカテゴリー定義を取得"""
        categories = [
            {
                "key": "recommendation",
                "title": "推薦度合い",
                "question": "他の外国人に就業を推薦したい会社ですか？",
            },
            {
                "key": "foreign_support",
                "title": "外国人の受け入れ制度",
                "question": "外国人の受け入れ制度が整っていますか？",
            },
            {
                "key": "company_culture",
                "title": "会社風土",
                "question": "会社方針は明確で、文化的多様性を尊重していますか？",
            },
            {
                "key": "employee_relations",
                "title": "社員との関係性",
                "question": "上司・部下とも尊敬の念を持って関係が構築できますか？",
            },
            {
                "key": "evaluation_system",
                "title": "成果・評価制度",
                "question": "外国人従業員の成果が認められる制度が整っていますか？",
            },
            {
                "key": "promotion_treatment",
                "title": "昇進・昇給・待遇",
                "question": "昇進・昇給機会は平等に与えられていますか？",
            },
        ]
        # Add index to each category for Tornado template compatibility
        for i, category in enumerate(categories):
            category["index"] = i + 1
        return categories

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

        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

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
            "comments": comments,
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
                "question": "他の外国人に就業を推薦したい会社ですか？",
            },
            {
                "key": "foreign_support",
                "title": "外国人の受け入れ制度",
                "question": "外国人の受け入れ制度が整っていますか？",
            },
            {
                "key": "company_culture",
                "title": "会社風土",
                "question": "会社方針は明確で、文化的多様性を尊重していますか？",
            },
            {
                "key": "employee_relations",
                "title": "社員との関係性",
                "question": "上司・部下とも尊敬の念を持って関係が構築できますか？",
            },
            {
                "key": "evaluation_system",
                "title": "成果・評価制度",
                "question": "外国人従業員の成果が認められる制度が整っていますか？",
            },
            {
                "key": "promotion_treatment",
                "title": "昇進・昇給・待遇",
                "question": "昇進・昇給機会は平等に与えられていますか？",
            },
        ]
        # Add index to each category for Tornado template compatibility
        for i, category in enumerate(categories):
            category["index"] = i + 1
        return categories

    async def get_current_user_id(self):
        """現在のユーザーIDを取得"""
        from ..services.session_service import SessionService

        session_id = self.get_secure_cookie("session_id")
        if not session_id:
            return None

        session_id = session_id.decode("utf-8") if isinstance(session_id, bytes) else session_id
        session_service = SessionService()

        # セッション検証
        session_result = await session_service.validate_session(session_id)
        if not session_result.is_success:
            return None

        session_data = session_result.data
        return session_data.get("identity_id")

    async def require_authentication(self):
        """認証を要求し、ユーザー情報を返す"""
        user_id = await self.get_current_user_id()
        if not user_id:
            raise tornado.web.HTTPError(401, "Authentication required")
        return user_id
