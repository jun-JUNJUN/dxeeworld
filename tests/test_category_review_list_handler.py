"""
質問別レビュー一覧ページハンドラーのテスト
Task 3: 質問別レビュー一覧ページの実装
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import tornado.web
from bson import ObjectId

from src.handlers.category_review_list_handler import CategoryReviewListHandler
from src.database import DatabaseService
from src.services.review_anonymization_service import ReviewAnonymizationService
from src.models.review import Review, EmploymentStatus, EmploymentPeriod


class TestCategoryReviewListHandler:
    """CategoryReviewListHandlerのテストクラス"""

    @pytest.fixture
    def db_service(self):
        """モックのデータベースサービス"""
        return Mock(spec=DatabaseService)

    @pytest.fixture
    def anonymization_service(self):
        """モックの匿名化サービス"""
        service = Mock(spec=ReviewAnonymizationService)
        service.anonymize_review = Mock(side_effect=lambda review, preview_mode: {
            "id": review.id,
            "company_id": review.company_id,
            "anonymized_user": f"ユーザーA",
            "employment_status": review.employment_status.value,
            "employment_period": {
                "start_year": 2020,
                "end_year": None
            } if review.employment_period else None,
            "ratings": review.ratings,
            "comments": {k: "***" for k in review.comments.keys()} if preview_mode else review.comments,
            "individual_average": review.individual_average,
            "answered_count": review.answered_count,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "is_active": review.is_active,
            "language": review.language
        })
        return service

    @pytest.fixture
    def handler(self, db_service, anonymization_service):
        """ハンドラーインスタンスの作成"""
        # Create handler without going through __init__
        handler = CategoryReviewListHandler.__new__(CategoryReviewListHandler)

        # Initialize with services
        handler.initialize(
            db_service=db_service,
            anonymization_service=anonymization_service
        )

        # Mock methods that interact with HTTP response
        handler.render = Mock()
        handler.get_argument = Mock(return_value="1")
        handler.current_user_access_level = "FULL"

        return handler

    @pytest.fixture
    def sample_company_id(self):
        """テスト用の企業ID"""
        return str(ObjectId())

    @pytest.fixture
    def sample_review(self, sample_company_id):
        """サンプルレビューの作成"""
        return Review(
            id=str(ObjectId()),
            company_id=sample_company_id,
            user_id="user456",
            employment_status=EmploymentStatus.CURRENT,
            ratings={
                "recommendation": 4,
                "foreign_support": 3,
                "company_culture": 5,
                "employee_relations": 4,
                "evaluation_system": None,
                "promotion_treatment": 3
            },
            comments={
                "recommendation": "働きやすい会社です",
                "foreign_support": "サポート体制が充実",
                "company_culture": "オープンな雰囲気",
                "employee_relations": "チームワークが良い",
                "evaluation_system": None,
                "promotion_treatment": "昇進は実力次第"
            },
            individual_average=3.8,
            answered_count=5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True,
            employment_period=EmploymentPeriod(start_year=2020, end_year=None),
            language="ja"
        )

    # Task 3.1: リクエストハンドラーの基本実装
    @pytest.mark.asyncio
    async def test_handler_initialization(self, handler, db_service, anonymization_service):
        """ハンドラーが正しく初期化されることを確認"""
        assert handler.db_service == db_service
        assert handler.anonymization_service == anonymization_service

    # Task 3.2: カテゴリ名のバリデーション
    def test_validate_category_name_valid(self, handler):
        """有効なカテゴリ名のバリデーション"""
        valid_categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment"
        ]
        for category in valid_categories:
            assert handler._validate_category_name(category) is True

    def test_validate_category_name_invalid(self, handler):
        """無効なカテゴリ名のバリデーション"""
        invalid_categories = [
            "invalid_category",
            "salary",
            "benefits",
            "work_life_balance",
            "",
            None
        ]
        for category in invalid_categories:
            assert handler._validate_category_name(category) is False

    def test_get_category_label(self, handler):
        """カテゴリ名の日本語ラベル取得"""
        expected_labels = {
            "recommendation": "推薦度",
            "foreign_support": "受入制度",
            "company_culture": "会社風土",
            "employee_relations": "関係性",
            "evaluation_system": "評価制度",
            "promotion_treatment": "昇進待遇"
        }
        for category, expected_label in expected_labels.items():
            label = handler._get_category_label(category)
            assert label == expected_label

    @pytest.mark.asyncio
    async def test_get_with_invalid_category_returns_400(self, handler, sample_company_id):
        """無効なカテゴリ名で400エラーが返されること"""
        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(sample_company_id, "invalid_category")
        assert exc_info.value.status_code == 400

    # Task 3.3: レビューリストの取得とページネーション
    @pytest.mark.asyncio
    async def test_get_reviews_for_category_basic(self, handler, db_service, sample_review, sample_company_id):
        """指定カテゴリのレビュー取得（基本）"""
        # モックの設定
        db_service.find = AsyncMock(return_value=[
            sample_review.to_dict(),
            sample_review.to_dict()
        ])
        db_service.count_documents = AsyncMock(return_value=2)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # データベースクエリの確認
        db_service.find.assert_called_once()
        call_args = db_service.find.call_args

        # クエリ条件の確認
        query = call_args[0][1]
        assert query["company_id"] == sample_company_id
        assert query["is_active"] is True
        assert "ratings.recommendation" in query

        # ソート順の確認（投稿日時降順）
        assert call_args[1]["sort"] == [("created_at", -1)]

    @pytest.mark.asyncio
    async def test_get_reviews_pagination_first_page(self, handler, db_service, sample_review, sample_company_id):
        """ページネーション - 1ページ目"""
        # モックの設定
        reviews = [sample_review.to_dict() for _ in range(20)]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=50)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        handler.get_argument = Mock(return_value="1")

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # ページネーションパラメータの確認
        call_args = db_service.find.call_args
        assert call_args[1]["skip"] == 0
        assert call_args[1]["limit"] == 20

    @pytest.mark.asyncio
    async def test_get_reviews_pagination_second_page(self, handler, db_service, sample_review, sample_company_id):
        """ページネーション - 2ページ目"""
        # モックの設定
        reviews = [sample_review.to_dict() for _ in range(20)]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=50)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        handler.get_argument = Mock(return_value="2")

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # ページネーションパラメータの確認
        call_args = db_service.find.call_args
        assert call_args[1]["skip"] == 20
        assert call_args[1]["limit"] == 20

    @pytest.mark.asyncio
    async def test_pagination_info_calculation(self, handler, db_service, sample_review, sample_company_id):
        """ページネーション情報の計算"""
        # モックの設定
        reviews = [sample_review.to_dict() for _ in range(20)]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=87)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        handler.get_argument = Mock(return_value="2")

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # レンダリングされたページネーション情報の確認
        render_call = handler.render.call_args
        pagination = render_call[1]["pagination"]

        assert pagination["current_page"] == 2
        assert pagination["total_pages"] == 5
        assert pagination["total_count"] == 87
        assert pagination["per_page"] == 20
        assert pagination["has_prev"] is True
        assert pagination["has_next"] is True
        assert pagination["prev_page"] == 1
        assert pagination["next_page"] == 3

    # Task 3.4: 複数レビューの匿名化処理
    @pytest.mark.asyncio
    async def test_anonymize_all_reviews(self, handler, db_service, anonymization_service, sample_review, sample_company_id):
        """全レビューが匿名化されること"""
        # モックの設定
        reviews = [sample_review.to_dict() for _ in range(3)]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=3)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # 匿名化サービスが3回呼ばれることを確認
        assert anonymization_service.anonymize_review.call_count == 3

    @pytest.mark.asyncio
    async def test_preview_mode_masks_comments(self, handler, db_service, anonymization_service, sample_review, sample_company_id):
        """プレビューモードでコメントがマスクされること"""
        # モックの設定
        reviews = [sample_review.to_dict()]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=1)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        handler.current_user_access_level = "PREVIEW"

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # 匿名化サービスがpreview_mode=Trueで呼ばれることを確認
        anonymization_service.anonymize_review.assert_called()
        call_args = anonymization_service.anonymize_review.call_args[1]
        assert call_args["preview_mode"] is True

    @pytest.mark.asyncio
    async def test_full_access_shows_all_comments(self, handler, db_service, anonymization_service, sample_review, sample_company_id):
        """フルアクセスで全コメントが表示されること"""
        # モックの設定
        reviews = [sample_review.to_dict()]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=1)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        handler.current_user_access_level = "FULL"

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # 匿名化サービスがpreview_mode=Falseで呼ばれることを確認
        anonymization_service.anonymize_review.assert_called()
        call_args = anonymization_service.anonymize_review.call_args[1]
        assert call_args["preview_mode"] is False

    # Task 3.5: エラーハンドリングとエッジケース処理
    @pytest.mark.asyncio
    async def test_company_not_found_returns_404(self, handler, db_service):
        """企業が見つからない場合に404エラーが返されること"""
        db_service.find_one = AsyncMock(return_value=None)

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get("nonexistent_company", "recommendation")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_page_number_returns_400(self, handler, db_service, sample_company_id):
        """無効なページ番号で400エラーが返されること"""
        handler.get_argument = Mock(return_value="invalid")
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(sample_company_id, "recommendation")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_zero_page_number_returns_400(self, handler, db_service, sample_company_id):
        """ページ番号0で400エラーが返されること"""
        handler.get_argument = Mock(return_value="0")
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(sample_company_id, "recommendation")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_negative_page_number_returns_400(self, handler, db_service, sample_company_id):
        """負のページ番号で400エラーが返されること"""
        handler.get_argument = Mock(return_value="-1")
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(sample_company_id, "recommendation")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_no_reviews_shows_empty_message(self, handler, db_service, sample_company_id):
        """レビュー0件時に空メッセージが表示されること"""
        db_service.find = AsyncMock(return_value=[])
        db_service.count_documents = AsyncMock(return_value=0)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # レンダリングの確認
        handler.render.assert_called_once()
        render_call = handler.render.call_args

        # レビューリストが空であることを確認
        assert len(render_call[1]["reviews"]) == 0
        assert render_call[1]["pagination"]["total_count"] == 0

    @pytest.mark.asyncio
    async def test_database_error_returns_500(self, handler, db_service, sample_company_id):
        """データベースエラーで500エラーが返されること"""
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})
        db_service.find = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(sample_company_id, "recommendation")

        assert exc_info.value.status_code == 500

    # レンダリングのテスト
    @pytest.mark.asyncio
    async def test_render_with_correct_template_variables(self, handler, db_service, sample_review, sample_company_id):
        """正しいテンプレート変数でレンダリングされること"""
        # モックの設定
        reviews = [sample_review.to_dict()]
        db_service.find = AsyncMock(return_value=reviews)
        db_service.count_documents = AsyncMock(return_value=1)
        db_service.find_one = AsyncMock(return_value={"_id": ObjectId(sample_company_id), "name": "テスト企業"})

        # ハンドラーの実行
        await handler.get(sample_company_id, "recommendation")

        # レンダリングの確認
        handler.render.assert_called_once()
        render_call = handler.render.call_args

        # テンプレート名の確認
        assert render_call[0][0] == "category_review_list.html"

        # テンプレート変数の確認
        template_vars = render_call[1]
        assert "reviews" in template_vars
        assert "company_name" in template_vars
        assert "company_id" in template_vars
        assert "category_name" in template_vars
        assert "category_label" in template_vars
        assert "pagination" in template_vars
        assert "preview_mode" in template_vars
        assert "access_level" in template_vars

        assert template_vars["company_id"] == sample_company_id
        assert template_vars["category_name"] == "recommendation"
        assert template_vars["category_label"] == "推薦度"
        assert template_vars["company_name"] == "テスト企業"
