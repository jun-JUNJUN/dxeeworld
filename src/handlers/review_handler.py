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
        # Task 3.3: データベースサービスを取得してCompanySearchServiceに渡す
        db_service = get_db_service()
        self.company_search_service = CompanySearchService(db_service)
        # Task 2.4: AccessControlMiddleware統合
        from ..middleware.access_control_middleware import AccessControlMiddleware

        self.access_control = AccessControlMiddleware(db_service)

    def parse_search_params(self, can_filter: bool) -> dict:
        """
        Task 3.2: 検索パラメータの解析と処理

        Args:
            can_filter: フィルター機能が有効かどうか

        Returns:
            dict: 解析された検索パラメータ
                - name: 企業名（部分一致、can_filter=True時のみ）
                - location: 所在地（部分一致、can_filter=True時のみ）
                - min_rating: 最低評価（0.0-5.0、can_filter=True時のみ）
                - max_rating: 最高評価（0.0-5.0、can_filter=True時のみ）
                - page: ページ番号（1始まり、デフォルト1）
                - per_page: 1ページあたりの件数（デフォルト20）
                - sort_by: ソートキー（デフォルトrating_high）
        """
        params = {}

        # ページ番号とソートは常に有効
        page_str = self.get_argument("page", None)
        try:
            params["page"] = int(page_str) if page_str else 1
            if params["page"] < 1:
                params["page"] = 1
        except (ValueError, TypeError):
            params["page"] = 1

        per_page_str = self.get_argument("per_page", None)
        try:
            params["per_page"] = int(per_page_str) if per_page_str else 20
        except (ValueError, TypeError):
            params["per_page"] = 20

        # ソートキーの変換（デフォルト: rating_high）
        sort_param = self.get_argument("sort", None)
        params["sort_by"] = sort_param if sort_param else "rating_high"

        # can_filter=True の場合のみフィルターパラメータを追加
        if can_filter:
            # 企業名フィルター
            name = self.get_argument("name", None)
            if name and name.strip():
                params["name"] = name.strip()

            # 所在地フィルター
            location = self.get_argument("location", None)
            if location and location.strip():
                params["location"] = location.strip()

            # 最低評価フィルター
            min_rating_str = self.get_argument("min_rating", None)
            if min_rating_str:
                try:
                    min_rating = float(min_rating_str)
                    if 0.0 <= min_rating <= 5.0:
                        params["min_rating"] = min_rating
                except (ValueError, TypeError):
                    pass  # 不正な値は無視

            # 最高評価フィルター
            max_rating_str = self.get_argument("max_rating", None)
            if max_rating_str:
                try:
                    max_rating = float(max_rating_str)
                    if 0.0 <= max_rating <= 5.0:
                        params["max_rating"] = max_rating
                except (ValueError, TypeError):
                    pass  # 不正な値は無視

        return params

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
        """
        Task 3.3: レビュー一覧ページを表示 - 企業検索の実行とページレンダリング

        処理フロー:
        1. Task 3.1: セッションからユーザーIDを取得し、アクセス制御チェック
        2. アクセス拒否の場合、エラーメッセージを表示して終了
        3. Task 3.2: 検索パラメータを解析（can_filterに応じてフィルター無効化）
        4. Task 3.3: CompanySearchServiceで企業検索を実行
        5. 検索結果とページネーション情報をテンプレートに渡してレンダリング
        """
        try:
            # Task 3.1: セッションIDからユーザーIDを取得
            user_id = await self.get_current_user_id()

            # Task 3.1: User-Agentを取得（クローラー検出用）
            user_agent = self.request.headers.get("User-Agent", "")

            # Task 3.1: アクセス制御チェック
            access_result = await self.access_control.check_review_list_access(
                user_id, user_agent
            )
            access_level = access_result.get("access_level", "preview")
            can_filter = access_result.get("can_filter", False)

            # Task 3.1: アクセス拒否の場合、エラーメッセージを表示
            if access_level == "denied":
                self.render(
                    "reviews/list.html",
                    companies=[],
                    pagination={
                        "page": 1,
                        "total": 0,
                        "total_count": 0,
                        "total_pages": 0,
                        "per_page": 20
                    },
                    search_params={},
                    access_level=access_level,
                    can_filter=False,
                    access_message=access_result.get("message", ""),
                )
                return

            # Task 3.2: 検索パラメータの解析
            search_params = self.parse_search_params(can_filter)

            # Task 3.3: CompanySearchServiceで企業検索を実行
            search_result = await self.company_search_service.search_companies(
                search_params
            )

            # Debug: Log search results
            logger.info(
                "Company search completed: total_count=%d, companies_returned=%d, page=%d",
                search_result.get("total_count", 0),
                len(search_result.get("companies", [])),
                search_result.get("current_page", 1)
            )

            # Task 3.3: 検索成功時のレンダリング
            if search_result.get("success"):
                self.render(
                    "reviews/list.html",
                    companies=search_result["companies"],
                    pagination={
                        "page": search_result["current_page"],
                        "total": search_result["total_count"],
                        "total_count": search_result["total_count"],
                        "total_pages": search_result["total_pages"],
                        "per_page": search_result["per_page"]
                    },
                    search_params=search_params,
                    access_level=access_level,
                    can_filter=can_filter,
                    access_message=access_result.get("message", ""),
                )
            else:
                # Task 3.3: 検索エラー時の処理（空のリスト表示、エラーログ記録）
                logger.error(
                    f"Company search failed: {search_result.get('error_code')} - "
                    f"{search_result.get('message', 'Unknown error')}"
                )
                self.render(
                    "reviews/list.html",
                    companies=[],
                    pagination={
                        "page": 1,
                        "total": 0,
                        "total_count": 0,
                        "total_pages": 0,
                        "per_page": 20
                    },
                    search_params=search_params,
                    access_level=access_level,
                    can_filter=can_filter,
                    access_message="検索中にエラーが発生しました",
                )

        except Exception as e:
            # Task 3.3: 予期しないエラー時の処理（空のリスト表示、エラーログ記録）
            logger.exception(f"Unexpected error in review list handler: {e}")
            self.render(
                "reviews/list.html",
                companies=[],
                pagination={
                    "page": 1,
                    "total": 0,
                    "total_count": 0,
                    "total_pages": 0,
                    "per_page": 20
                },
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

        # Task 1.3: ReviewAggregationService統合（非同期集計処理）
        from ..services.review_aggregation_service import ReviewAggregationService

        self.access_control = AccessControlMiddleware(self.db_service)
        self.i18n_service = I18nFormService()
        self.translation_service = TranslationService()
        self.aggregation_service = ReviewAggregationService(self.db_service)

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
                categories=self._get_review_categories(default_language),
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

                # 最適化: hidden fieldから翻訳データを取得（DeepL API呼び出しを削減）
                has_cached_translations = self._check_cached_translations()

                if has_cached_translations:
                    # 確認画面からの翻訳データを再利用
                    logger.info("Reusing cached translations from confirmation screen (no API calls)")
                    translated_comments_all = self._parse_cached_translations()
                else:
                    # 翻訳データがない場合のみAPI呼び出し（フォールバック）- 並列翻訳版
                    logger.info("No cached translations found, calling DeepL API (parallel translation)")
                    import asyncio

                    translated_comments_all = {}
                    translation_tasks = []
                    categories_with_comments = []

                    # 各カテゴリーのコメントを並列翻訳
                    for category, comment in review_data["comments"].items():
                        if comment:
                            categories_with_comments.append((category, comment))
                            translation_tasks.append(
                                self.translation_service.translate_to_other_languages(
                                    text=comment, source_language=selected_language
                                )
                            )

                    # 全カテゴリーのコメントを並列翻訳
                    if translation_tasks:
                        translation_results = await asyncio.gather(
                            *translation_tasks, return_exceptions=True
                        )

                        # 結果を整理
                        for (category, comment), result in zip(
                            categories_with_comments, translation_results
                        ):
                            if isinstance(result, Exception):
                                logger.warning(
                                    f"Translation failed for category {category}: {result}"
                                )
                                # 翻訳失敗時はNoneを設定（Graceful Degradation）
                                for lang in ["ja", "en", "zh"]:
                                    if lang != selected_language:
                                        if lang not in translated_comments_all:
                                            translated_comments_all[lang] = {}
                                        translated_comments_all[lang][category] = None
                            else:
                                # 成功した翻訳を結果に追加
                                for lang, translated_text in result.items():
                                    if lang not in translated_comments_all:
                                        translated_comments_all[lang] = {}
                                    translated_comments_all[lang][category] = translated_text

                    # コメントがないカテゴリーはNoneを設定
                    for category in review_data["comments"].keys():
                        if category not in [cat for cat, _ in categories_with_comments]:
                            for lang in ["ja", "en", "zh"]:
                                if lang != selected_language:
                                    if lang not in translated_comments_all:
                                        translated_comments_all[lang] = {}
                                    translated_comments_all[lang][category] = None

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

                    # Task 1.3: レビュー投稿成功後、非同期で企業集計処理を起動
                    import asyncio
                    asyncio.create_task(
                        self.aggregation_service.aggregate_and_update_company(company_id)
                    )
                    logger.info(f"Async aggregation task created for company {company_id}")

                    # Task 8.1: 投稿成功メッセージを設定
                    self.set_flash_message(
                        "Review投稿しました。ありがとうございました。", "success"
                    )
                    # Task 5.3: 成功時は企業詳細ページにリダイレクト
                    self.redirect(f"/companies/{company_id}")
                else:
                    # Task 8.2: 投稿失敗時のエラーハンドリング
                    error_code = result.get("error_code") if result else None

                    # エラーコードに応じたメッセージを生成
                    if error_code == "duplicate_review":
                        days_until_next = result.get("days_until_next", 0)
                        if days_until_next > 0:
                            error_message = (
                                f"この企業には既にレビューを投稿済みです。\n"
                                f"1つの企業に対して投稿できるレビューは1年に1件までです。\n"
                                f"次のレビューを投稿できるのは約{days_until_next}日後になります。"
                            )
                        else:
                            error_message = (
                                "この企業には既にレビューを投稿済みです。\n"
                                "1つの企業に対して投稿できるレビューは1年に1件までです。"
                            )
                    elif error_code == "database_error":
                        error_message = result.get("message", "データベースエラーが発生しました")
                    elif result and "errors" in result:
                        # バリデーションエラーの場合
                        errors = result.get("errors", [])
                        error_message = "入力内容に問題があります：" + "、".join(errors)
                    else:
                        error_message = (
                            result.get("message", "レビューの投稿に失敗しました")
                            if result
                            else "レビューサービスでエラーが発生しました"
                        )

                    logger.error(
                        "Review submission failed for company %s: %s (error_code: %s)",
                        company_id, error_message, error_code
                    )
                    # Task 8.2: エラー発生時にユーザーを確認画面に留める
                    # 確認画面を再表示し、エラーメッセージを表示
                    company = await self.review_service.get_company_info(company_id)
                    selected_language = review_data.get("language", "ja")
                    confirm_i18n = self._get_confirmation_i18n(selected_language)
                    self.render(
                        "reviews/confirm.html",
                        company=company,
                        review_data=review_data,
                        translated_comments={},  # 翻訳データは再取得不要
                        translated_comments_all={"ja": {}, "en": {}, "zh": {}},
                        selected_language=selected_language,
                        categories=self._get_review_categories(selected_language),
                        error_message=error_message,  # Task 8.2: エラーメッセージを渡す
                        i18n=confirm_i18n,  # 確認画面の翻訳辞書
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

            # 選択された言語を取得（review_dataから）
            selected_language = review_data.get("selected_language", "ja")

            # Task 6: 元言語以外の2言語に並列翻訳（asyncio.gather）
            import asyncio

            translated_comments_all = {}

            # 各カテゴリーのコメントを並列翻訳
            translation_tasks = []
            categories_with_comments = []

            for category, comment in review_data["comments"].items():
                if comment:
                    categories_with_comments.append((category, comment))
                    translation_tasks.append(
                        self.translation_service.translate_to_other_languages(
                            text=comment, source_language=selected_language
                        )
                    )

            # 全カテゴリーのコメントを並列翻訳
            if translation_tasks:
                translation_results = await asyncio.gather(*translation_tasks, return_exceptions=True)

                # 結果を整理
                for (category, comment), result in zip(categories_with_comments, translation_results):
                    if isinstance(result, Exception):
                        logger.warning(
                            f"Translation failed for category {category}: {result}"
                        )
                        # 翻訳失敗時は空にする（Graceful Degradation）
                        for lang in ["ja", "en", "zh"]:
                            if lang != selected_language:
                                if lang not in translated_comments_all:
                                    translated_comments_all[lang] = {}
                                translated_comments_all[lang][category] = None
                    else:
                        # 成功した翻訳を結果に追加
                        for lang, translated_text in result.items():
                            if lang not in translated_comments_all:
                                translated_comments_all[lang] = {}
                            translated_comments_all[lang][category] = translated_text

            # コメントがないカテゴリーはNoneを設定
            for category in review_data["comments"].keys():
                if category not in [cat for cat, _ in categories_with_comments]:
                    for lang in ["ja", "en", "zh"]:
                        if lang != selected_language:
                            if lang not in translated_comments_all:
                                translated_comments_all[lang] = {}
                            translated_comments_all[lang][category] = None

            # 後方互換性のため、translated_commentsも渡す（日本語翻訳）
            translated_comments = translated_comments_all.get("ja", review_data["comments"].copy())

            # 確認画面用の翻訳辞書
            confirm_i18n = self._get_confirmation_i18n(selected_language)

            # 確認画面をレンダリング
            self.render(
                "reviews/confirm.html",
                company=company,
                review_data=review_data,
                translated_comments=translated_comments,  # 後方互換性
                translated_comments_all=translated_comments_all,  # 3言語すべて
                selected_language=selected_language,
                categories=self._get_review_categories(selected_language),
                error_message=None,  # テンプレートでエラーチェックに使用
                i18n=confirm_i18n,  # 確認画面の翻訳
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
            "selected_language": self.get_argument(
                "review_language", "ja"
            ),  # フォームの name="review_language" から取得
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

    def _get_review_categories(self, language: str = "ja"):
        """
        レビューカテゴリー定義を取得（多言語対応）

        Args:
            language: 言語コード ("ja", "en", "zh")

        Returns:
            カテゴリーのリスト（title と question が指定言語で翻訳済み）
        """
        # 翻訳辞書を取得
        translations = self.i18n_service.get_form_translations()
        labels = translations.get("labels", {})

        # カテゴリーキーのリスト
        category_keys = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

        categories = []
        for key in category_keys:
            title_key = key
            question_key = f"{key}_question"

            # 翻訳辞書から title と question を取得
            title = labels.get(title_key, {}).get(language, labels.get(title_key, {}).get("ja", ""))
            question = labels.get(question_key, {}).get(language, labels.get(question_key, {}).get("ja", ""))

            categories.append({
                "key": key,
                "title": title,
                "question": question,
            })

        # Add index to each category for Tornado template compatibility
        for i, category in enumerate(categories):
            category["index"] = i + 1

        return categories

    def _check_cached_translations(self) -> bool:
        """
        確認画面からの翻訳データが存在するかチェック

        Returns:
            翻訳データが存在する場合True
        """
        # 少なくとも1つの言語の翻訳データが存在するかチェック
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

        for category in categories:
            # 日本語、英語、中国語のいずれかの翻訳が存在するかチェック
            if (
                self.get_argument(f"translated_comments_ja[{category}]", None)
                or self.get_argument(f"translated_comments_en[{category}]", None)
                or self.get_argument(f"translated_comments_zh[{category}]", None)
            ):
                return True

        return False

    def _parse_cached_translations(self) -> dict:
        """
        確認画面からの翻訳データを解析

        Returns:
            翻訳データの辞書 {"ja": {...}, "en": {...}, "zh": {...}}
        """
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

        translated_comments_all = {"ja": {}, "en": {}, "zh": {}}

        for category in categories:
            # 日本語翻訳
            ja_translation = self.get_argument(f"translated_comments_ja[{category}]", None)
            if ja_translation:
                translated_comments_all["ja"][category] = ja_translation

            # 英語翻訳
            en_translation = self.get_argument(f"translated_comments_en[{category}]", None)
            if en_translation:
                translated_comments_all["en"][category] = en_translation

            # 中国語翻訳
            zh_translation = self.get_argument(f"translated_comments_zh[{category}]", None)
            if zh_translation:
                translated_comments_all["zh"][category] = zh_translation

        return translated_comments_all

    def _get_confirmation_i18n(self, language: str) -> dict:
        """確認画面の翻訳辞書を取得"""
        translations = {
            "ja": {
                "page_title": "レビュー確認",
                "error_label": "エラー:",
                "input_language_label": "入力言語:",
                "language_ja": "日本語",
                "language_en": "英語（English）",
                "language_zh": "中国語（中文）",
                "language_unknown": "不明",
                "translation_note": "以下に元のコメントと他の言語への翻訳を表示します。翻訳内容を確認してください。",
                "employment_status_title": "在職状況",
                "employment_status_label": "在職状況",
                "employment_current": "現従業員",
                "employment_former": "元従業員",
                "employment_unknown": "未設定",
                "ratings_comments_title": "評価とコメント",
                "rating_label": "評価:",
                "no_rating": "評価なし",
                "comment_label_original_ja": "コメント（日本語・原文）:",
                "comment_label_original_en": "Comment (English - Original):",
                "comment_label_original_zh": "评论（中文 - 原文）:",
                "comment_label_original_default": "コメント（原文）:",
                "comment_label_translated_ja": "翻訳（日本語）:",
                "comment_label_translated_en": "Translation (English):",
                "comment_label_translated_zh": "翻译（中文）:",
                "comment_label": "コメント:",
                "no_comment": "コメントなし",
                "button_back": "← 戻って編集",
                "button_submit": "投稿する →",
                "confirm_dialog": "レビューを投稿してもよろしいですか？",
                "location_unknown": "所在地未設定",
                "company_name_unknown": "企業名未設定",
            },
            "en": {
                "page_title": "Review Confirmation",
                "error_label": "Error:",
                "input_language_label": "Input Language:",
                "language_ja": "Japanese (日本語)",
                "language_en": "English",
                "language_zh": "Chinese (中文)",
                "language_unknown": "Unknown",
                "translation_note": "Below are your original comments and translations to other languages. Please review the translations.",
                "employment_status_title": "Employment Status",
                "employment_status_label": "Employment Status",
                "employment_current": "Current Employee",
                "employment_former": "Former Employee",
                "employment_unknown": "Not Set",
                "ratings_comments_title": "Ratings and Comments",
                "rating_label": "Rating:",
                "no_rating": "No Rating",
                "comment_label_original_ja": "Comment (Japanese - Original):",
                "comment_label_original_en": "Comment (English - Original):",
                "comment_label_original_zh": "Comment (Chinese - Original):",
                "comment_label_original_default": "Comment (Original):",
                "comment_label_translated_ja": "Translation (Japanese):",
                "comment_label_translated_en": "Translation (English):",
                "comment_label_translated_zh": "Translation (Chinese):",
                "comment_label": "Comment:",
                "no_comment": "No Comment",
                "button_back": "← Back to Edit",
                "button_submit": "Submit Review →",
                "confirm_dialog": "Are you sure you want to submit this review?",
                "location_unknown": "Location Not Set",
                "company_name_unknown": "Company Name Not Set",
            },
            "zh": {
                "page_title": "评价确认",
                "error_label": "错误:",
                "input_language_label": "输入语言:",
                "language_ja": "日语（日本語）",
                "language_en": "英语（English）",
                "language_zh": "中文",
                "language_unknown": "未知",
                "translation_note": "以下是您的原始评论和其他语言的翻译。请确认翻译内容。",
                "employment_status_title": "在职状况",
                "employment_status_label": "在职状况",
                "employment_current": "现员工",
                "employment_former": "前员工",
                "employment_unknown": "未设置",
                "ratings_comments_title": "评分和评论",
                "rating_label": "评分:",
                "no_rating": "无评分",
                "comment_label_original_ja": "评论（日语 - 原文）:",
                "comment_label_original_en": "Comment (English - Original):",
                "comment_label_original_zh": "评论（中文 - 原文）:",
                "comment_label_original_default": "评论（原文）:",
                "comment_label_translated_ja": "翻译（日语）:",
                "comment_label_translated_en": "Translation (English):",
                "comment_label_translated_zh": "翻译（中文）:",
                "comment_label": "评论:",
                "no_comment": "无评论",
                "button_back": "← 返回编辑",
                "button_submit": "提交评价 →",
                "confirm_dialog": "确定要提交此评价吗？",
                "location_unknown": "地址未设置",
                "company_name_unknown": "公司名称未设置",
            },
        }
        return translations.get(language, translations["ja"])


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
        # I18nFormService統合（多言語対応）
        from ..services.i18n_form_service import I18nFormService

        self.access_control = AccessControlMiddleware(self.db_service)
        self.i18n_service = I18nFormService()

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

    def _get_review_categories(self, language: str = "ja"):
        """
        レビューカテゴリー定義を取得（多言語対応）

        Args:
            language: 言語コード ("ja", "en", "zh")

        Returns:
            カテゴリーのリスト（title と question が指定言語で翻訳済み）
        """
        # 翻訳辞書を取得
        translations = self.i18n_service.get_form_translations()
        labels = translations.get("labels", {})

        # カテゴリーキーのリスト
        category_keys = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment",
        ]

        categories = []
        for key in category_keys:
            title_key = key
            question_key = f"{key}_question"

            # 翻訳辞書から title と question を取得
            title = labels.get(title_key, {}).get(language, labels.get(title_key, {}).get("ja", ""))
            question = labels.get(question_key, {}).get(language, labels.get(question_key, {}).get("ja", ""))

            categories.append({
                "key": key,
                "title": title,
                "question": question,
            })

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
