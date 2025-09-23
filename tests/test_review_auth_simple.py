"""
レビュー認証機能の簡潔なテスト
TDD Green Phase: 認証機能確認
"""
import pytest
from unittest.mock import AsyncMock, Mock
from src.services.review_submission_service import ReviewSubmissionService
from src.middleware.auth_middleware import AuthMiddleware


class TestReviewAuthenticationService:
    """レビュー認証統合テスト"""

    @pytest.mark.asyncio
    async def test_validate_session_token_valid(self):
        """有効なセッショントークンの検証テスト"""
        # Given: 認証ミドルウェアと有効なトークン
        auth_middleware = AuthMiddleware()
        auth_middleware.session_service = AsyncMock()

        # セッション検証が成功するようにモック設定
        mock_result = AsyncMock()
        mock_result.is_success = True
        auth_middleware.session_service.validate_session.return_value = mock_result

        # When: トークンを検証
        result = await auth_middleware.validate_session_token("valid_token_123")

        # Then: 有効と判定される
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_session_token_invalid(self):
        """無効なセッショントークンの検証テスト"""
        # Given: 認証ミドルウェアと無効なトークン
        auth_middleware = AuthMiddleware()
        auth_middleware.session_service = AsyncMock()

        # セッション検証が失敗するようにモック設定
        mock_result = AsyncMock()
        mock_result.is_success = False
        auth_middleware.session_service.validate_session.return_value = mock_result

        # When: 無効なトークンを検証
        result = await auth_middleware.validate_session_token("invalid_token")

        # Then: 無効と判定される
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_session_token_empty(self):
        """空のセッショントークンの検証テスト"""
        # Given: 認証ミドルウェアと空のトークン
        auth_middleware = AuthMiddleware()

        # When: 空のトークンを検証
        result = await auth_middleware.validate_session_token("")

        # Then: 無効と判定される
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_from_session_dict_valid(self):
        """有効なセッション辞書からのユーザー情報取得テスト"""
        # Given: 認証ミドルウェアと有効なセッションデータ
        auth_middleware = AuthMiddleware()
        auth_middleware.user_service = AsyncMock()

        session_data = {
            "user_id": "user123",
            "email": "test@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }

        user_doc = {
            "_id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "user_type": "job_seeker",
            "company_id": None,
            "position": "Engineer",
            "is_active": True
        }

        auth_middleware.user_service.db_service = AsyncMock()
        auth_middleware.user_service.db_service.find_one.return_value = user_doc

        # When: セッション辞書からユーザー情報を取得
        result = await auth_middleware.get_user_from_session_dict(session_data)

        # Then: 正しいユーザー情報が返される
        assert result is not None
        assert result["user_id"] == "user123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_user_from_session_dict_inactive_user(self):
        """非アクティブユーザーのセッション処理テスト"""
        # Given: 非アクティブなユーザーのセッションデータ
        auth_middleware = AuthMiddleware()
        auth_middleware.user_service = AsyncMock()

        session_data = {
            "user_id": "inactive_user",
            "email": "inactive@example.com"
        }

        user_doc = {
            "_id": "inactive_user",
            "email": "inactive@example.com",
            "is_active": False  # 非アクティブ
        }

        auth_middleware.user_service.db_service = AsyncMock()
        auth_middleware.user_service.db_service.find_one.return_value = user_doc

        # When: 非アクティブユーザーの情報を取得試行
        result = await auth_middleware.get_user_from_session_dict(session_data)

        # Then: Noneが返される
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_from_session_dict_user_not_found(self):
        """存在しないユーザーのセッション処理テスト"""
        # Given: 存在しないユーザーのセッションデータ
        auth_middleware = AuthMiddleware()
        auth_middleware.user_service = AsyncMock()

        session_data = {
            "user_id": "nonexistent_user"
        }

        # ユーザーが見つからない
        auth_middleware.user_service.db_service = AsyncMock()
        auth_middleware.user_service.db_service.find_one.return_value = None

        # When: 存在しないユーザーの情報を取得試行
        result = await auth_middleware.get_user_from_session_dict(session_data)

        # Then: Noneが返される
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_from_session_dict_empty_session(self):
        """空のセッションデータの処理テスト"""
        # Given: 空のセッションデータ
        auth_middleware = AuthMiddleware()

        # When: 空のセッションからユーザー情報を取得試行
        result = await auth_middleware.get_user_from_session_dict({})

        # Then: Noneが返される
        assert result is None


class TestReviewPermissionIntegration:
    """レビュー権限統合テスト（認証込み）"""

    @pytest.mark.asyncio
    async def test_review_creation_permission_with_authentication(self):
        """認証とレビュー投稿権限の統合テスト"""
        # Given: 認証されたユーザーと投稿制限チェック
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        user_id = "authenticated_user_123"
        company_id = "company_456"

        # 既存レビューなし（新規投稿可能）
        mock_db.find_one.return_value = None

        # When: 投稿権限をチェック
        permission = await service.validate_review_permissions(user_id, company_id)

        # Then: 投稿が許可される
        assert permission["can_create"] is True
        assert permission["can_update"] is False
        assert permission["existing_review_id"] is None
        assert permission["days_until_next"] == 0

    @pytest.mark.asyncio
    async def test_review_edit_permission_with_authentication(self):
        """認証とレビュー編集権限の統合テスト"""
        # Given: 認証されたユーザーと自分のレビュー
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        user_id = "authenticated_user_123"
        review_id = "review_789"

        # 自分が6ヶ月前に投稿したレビュー
        from datetime import datetime, timedelta
        review_data = {
            "_id": review_id,
            "user_id": user_id,
            "created_at": datetime.utcnow() - timedelta(days=180),
            "is_active": True
        }

        mock_db.find_one.return_value = review_data

        # When: 編集権限をチェック
        can_edit = await service.check_edit_permission(user_id, review_id)

        # Then: 編集が許可される
        assert can_edit is True

    @pytest.mark.asyncio
    async def test_review_edit_permission_denied_different_user(self):
        """異なるユーザーのレビュー編集権限拒否テスト"""
        # Given: 他のユーザーのレビューに対する編集試行
        service = ReviewSubmissionService()
        mock_db = AsyncMock()
        service.db = mock_db

        requesting_user_id = "user_A"
        review_owner_id = "user_B"
        review_id = "review_789"

        # 他のユーザーが投稿したレビュー
        from datetime import datetime, timedelta
        review_data = {
            "_id": review_id,
            "user_id": review_owner_id,  # 異なるユーザー
            "created_at": datetime.utcnow() - timedelta(days=30),
            "is_active": True
        }

        mock_db.find_one.return_value = review_data

        # When: 異なるユーザーが編集権限をチェック
        can_edit = await service.check_edit_permission(requesting_user_id, review_id)

        # Then: 編集が拒否される
        assert can_edit is False