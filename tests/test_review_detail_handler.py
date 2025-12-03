"""
ReviewDetailHandler のテスト (Task 2: 個別レビュー詳細ページ)
TDD approach: Tests using mocks to avoid database dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from bson import ObjectId
import tornado.web

from src.handlers.review_detail_handler import ReviewDetailHandler
from src.services.review_anonymization_service import ReviewAnonymizationService
from src.models.review import Review, EmploymentStatus, EmploymentPeriod


def create_test_review_data(company_id="test_company_123", review_id="test_review_456"):
    """テスト用レビューデータを作成"""
    return {
        "_id": ObjectId(),
        "company_id": company_id,
        "user_id": "test_user_123",
        "employment_status": "current",
        "ratings": {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": 5,
            "employee_relations": 4,
            "evaluation_system": None,
            "promotion_treatment": 3
        },
        "comments": {
            "recommendation": "働きやすい会社です",
            "foreign_support": "サポート体制が充実",
            "company_culture": "オープンな文化",
            "employee_relations": "チームワークが良い",
            "evaluation_system": None,
            "promotion_treatment": "昇進機会あり"
        },
        "individual_average": 3.8,
        "answered_count": 5,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
        "employment_period": {
            "start_year": 2020,
            "end_year": None
        },
        "language": "ja"
    }


class TestReviewDetailHandlerBasicStructure:
    """Task 2.1: リクエストハンドラーの基本実装のテスト"""

    @pytest.mark.asyncio
    async def test_handler_class_exists(self):
        """ReviewDetailHandlerクラスが存在することを確認"""
        assert ReviewDetailHandler is not None
        assert issubclass(ReviewDetailHandler, tornado.web.RequestHandler)

    @pytest.mark.asyncio
    async def test_handler_has_initialize_method(self):
        """initializeメソッドが存在することを確認"""
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        assert hasattr(handler, 'initialize')
        assert callable(getattr(handler, 'initialize'))

    @pytest.mark.asyncio
    async def test_handler_has_get_method(self):
        """getメソッドが存在することを確認"""
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        assert hasattr(handler, 'get')
        assert callable(getattr(handler, 'get'))

    @pytest.mark.asyncio
    async def test_initialize_accepts_db_and_anonymization_services(self):
        """initializeがdb_serviceとanonymization_serviceを受け取ることを確認"""
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        db_service = Mock()
        anonymization_service = Mock()

        # Should not raise exception
        handler.initialize(
            db_service=db_service,
            anonymization_service=anonymization_service
        )

        assert handler.db_service == db_service
        assert handler.anonymization_service == anonymization_service


class TestReviewDataRetrieval:
    """Task 2.2: レビューデータ取得とバリデーションのテスト"""

    @pytest.mark.asyncio
    async def test_get_review_method_exists(self):
        """_get_reviewメソッドが存在することを確認"""
        mock_db = Mock()
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        assert hasattr(handler, '_get_review')
        assert callable(getattr(handler, '_get_review'))

    @pytest.mark.asyncio
    async def test_get_review_returns_review_object(self):
        """_get_reviewが正しくレビューオブジェクトを返すことを確認"""
        company_id = "test_company_123"
        review_id = str(ObjectId())
        test_review_data = create_test_review_data(company_id, review_id)

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=test_review_data)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        review = await handler._get_review(company_id, review_id)

        assert review is not None
        assert isinstance(review, Review)
        assert review.company_id == company_id

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_nonexistent_review(self):
        """存在しないレビューIDの場合、Noneを返すことを確認"""
        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=None)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        fake_review_id = str(ObjectId())
        review = await handler._get_review("test_company_123", fake_review_id)

        assert review is None

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_inactive_review(self):
        """is_active=Falseのレビューの場合、Noneを返すことを確認"""
        company_id = "test_company_123"
        review_id = str(ObjectId())
        inactive_review_data = create_test_review_data(company_id, review_id)
        inactive_review_data['is_active'] = False

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=inactive_review_data)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        review = await handler._get_review(company_id, review_id)

        assert review is None

    @pytest.mark.asyncio
    async def test_get_review_validates_company_id_match(self):
        """company_idが一致しない場合、Noneを返すことを確認"""
        company_id = "test_company_123"
        wrong_company_id = "wrong_company_456"
        review_id = str(ObjectId())
        test_review_data = create_test_review_data(company_id, review_id)

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=test_review_data)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        review = await handler._get_review(wrong_company_id, review_id)

        assert review is None

    @pytest.mark.asyncio
    async def test_get_company_name_method_exists(self):
        """_get_company_nameメソッドが存在することを確認"""
        mock_db = Mock()
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        assert hasattr(handler, '_get_company_name')
        assert callable(getattr(handler, '_get_company_name'))

    @pytest.mark.asyncio
    async def test_get_company_name_returns_company_name(self):
        """_get_company_nameが正しく企業名を返すことを確認"""
        company_id = str(ObjectId())
        company_data = {"_id": ObjectId(), "name": "テスト株式会社"}

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=company_data)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        company_name = await handler._get_company_name(company_id)

        assert company_name == "テスト株式会社"

    @pytest.mark.asyncio
    async def test_get_company_name_returns_none_for_nonexistent_company(self):
        """存在しない企業IDの場合、Noneを返すことを確認"""
        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=None)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=Mock())

        fake_company_id = str(ObjectId())
        company_name = await handler._get_company_name(fake_company_id)

        assert company_name is None


class TestAccessLevelRendering:
    """Task 2.3: アクセスレベルに応じたレンダリング処理のテスト"""

    @pytest.mark.asyncio
    async def test_render_review_detail_method_exists(self):
        """_render_review_detailメソッドが存在することを確認"""
        mock_db = Mock()
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=ReviewAnonymizationService())

        assert hasattr(handler, '_render_review_detail')
        assert callable(getattr(handler, '_render_review_detail'))

    @pytest.mark.asyncio
    async def test_render_applies_anonymization(self):
        """レンダリング時に匿名化サービスが適用されることを確認"""
        test_review_data = create_test_review_data()
        review = Review.from_dict(test_review_data)

        anonymization_service = ReviewAnonymizationService()
        mock_db = Mock()
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=anonymization_service)
        handler.render = Mock()  # Mock render method

        handler._render_review_detail(review, "テスト株式会社", "FULL")

        # Verify render was called
        handler.render.assert_called_once()
        call_args = handler.render.call_args[0]
        template_name = call_args[0]

        assert template_name == "review_detail.html"

    @pytest.mark.asyncio
    async def test_render_preview_mode_masks_comments(self):
        """プレビューモードでコメントがマスクされることを確認"""
        test_review_data = create_test_review_data()
        review = Review.from_dict(test_review_data)

        anonymization_service = ReviewAnonymizationService()
        mock_db = Mock()
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=anonymization_service)
        handler.render = Mock()

        handler._render_review_detail(review, "テスト株式会社", "PREVIEW")

        # Verify render was called with preview_mode=True
        handler.render.assert_called_once()
        call_kwargs = handler.render.call_args[1]

        assert call_kwargs.get("preview_mode") is True

    @pytest.mark.asyncio
    async def test_render_full_mode_shows_all_comments(self):
        """フルアクセスモードで全コメントが表示されることを確認"""
        test_review_data = create_test_review_data()
        review = Review.from_dict(test_review_data)

        anonymization_service = ReviewAnonymizationService()
        mock_db = Mock()
        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=anonymization_service)
        handler.render = Mock()

        handler._render_review_detail(review, "テスト株式会社", "FULL")

        # Verify render was called with preview_mode=False
        handler.render.assert_called_once()
        call_kwargs = handler.render.call_args[1]

        assert call_kwargs.get("preview_mode") is False


class TestErrorHandling:
    """Task 2.4: エラーハンドリングの実装のテスト"""

    @pytest.mark.asyncio
    async def test_get_raises_404_for_nonexistent_review(self):
        """存在しないレビューIDで404エラーが発生することを確認"""
        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=None)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=ReviewAnonymizationService())

        handler.request = Mock()
        handler.current_user_access_level = "FULL"

        fake_review_id = str(ObjectId())

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get("test_company_123", fake_review_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_raises_404_for_nonexistent_company(self):
        """存在しない企業IDで404エラーが発生することを確認"""
        test_review_data = create_test_review_data()

        mock_db = AsyncMock()
        # First call returns review, second call returns None (no company)
        mock_db.find_one = AsyncMock(side_effect=[test_review_data, None])

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=ReviewAnonymizationService())

        handler.request = Mock()
        handler.current_user_access_level = "FULL"

        fake_company_id = str(ObjectId())
        review_id = str(ObjectId())

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(fake_company_id, review_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_raises_404_for_inactive_review(self):
        """is_active=Falseのレビューで404エラーが発生することを確認"""
        inactive_review_data = create_test_review_data()
        inactive_review_data['is_active'] = False

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(return_value=inactive_review_data)

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=ReviewAnonymizationService())

        handler.request = Mock()
        handler.current_user_access_level = "FULL"

        company_id = "test_company_123"
        review_id = str(ObjectId())

        with pytest.raises(tornado.web.HTTPError) as exc_info:
            await handler.get(company_id, review_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_logs_appropriate_messages(self):
        """適切なログメッセージが出力されることを確認"""
        company_id = str(ObjectId())
        review_id = str(ObjectId())
        test_review_data = create_test_review_data(company_id, review_id)
        company_data = {"_id": ObjectId(), "name": "テスト株式会社"}

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(side_effect=[test_review_data, company_data])

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=ReviewAnonymizationService())

        handler.request = Mock()
        handler.current_user_access_level = "FULL"
        handler.render = Mock()

        with patch('src.handlers.review_detail_handler.logger') as mock_logger:
            await handler.get(company_id, review_id)

            # Verify info log was called
            mock_logger.info.assert_called()


class TestIntegrationWithAccessControl:
    """アクセス制御との統合テスト"""

    @pytest.mark.asyncio
    async def test_get_method_exists(self):
        """getメソッドが存在することを確認"""
        get_method = ReviewDetailHandler.get
        assert hasattr(get_method, '__name__')
        assert get_method.__name__ == 'get'

    @pytest.mark.asyncio
    async def test_handler_respects_access_level_from_middleware(self):
        """ミドルウェアから設定されたアクセスレベルを尊重することを確認"""
        company_id = str(ObjectId())
        review_id = str(ObjectId())
        test_review_data = create_test_review_data(company_id, review_id)
        company_data = {"_id": ObjectId(), "name": "テスト株式会社"}

        mock_db = AsyncMock()
        mock_db.find_one = AsyncMock(side_effect=[test_review_data, company_data])

        handler = ReviewDetailHandler.__new__(ReviewDetailHandler)
        handler.initialize(db_service=mock_db, anonymization_service=ReviewAnonymizationService())

        handler.request = Mock()
        handler.render = Mock()

        # Simulate middleware setting access level
        handler.current_user_access_level = "PREVIEW"

        await handler.get(company_id, review_id)

        # Verify preview mode was used
        call_kwargs = handler.render.call_args[1]
        assert call_kwargs.get("preview_mode") is True
