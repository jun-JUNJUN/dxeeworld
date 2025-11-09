"""
CompanySearchService の検索パラメータバリデーション機能のテスト
"""
import pytest
import pytest_asyncio
from src.services.company_search_service import CompanySearchService
from src.database import DatabaseService


@pytest_asyncio.fixture
async def service_and_db():
    """テスト用サービスインスタンスとデータベース"""
    db = DatabaseService()
    await db.connect()

    # テストデータをクリーンアップ
    await db.delete_many("companies", {})

    service = CompanySearchService(db)

    yield service, db

    # テスト後のクリーンアップ
    await db.delete_many("companies", {})
    await db.close()


class TestCompanySearchValidation:
    """CompanySearchService の検索パラメータバリデーション機能のテスト"""

    @pytest.mark.asyncio
    async def test_validation_page_positive_integer(self, service_and_db):
        """ページ番号のバリデーション（正の整数）"""
        service, db = service_and_db

        # ページ番号が0以下の場合
        errors = await service.validate_search_params({"page": 0})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # ページ番号が負の場合
        errors = await service.validate_search_params({"page": -1})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # ページ番号が正の整数の場合
        errors = await service.validate_search_params({"page": 1})
        assert len(errors) == 0

        errors = await service.validate_search_params({"page": 100})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validation_per_page_positive_integer(self, service_and_db):
        """1ページあたりの件数のバリデーション（正の整数）"""
        service, db = service_and_db

        # per_pageが0以下の場合
        errors = await service.validate_search_params({"per_page": 0})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # per_pageが負の場合
        errors = await service.validate_search_params({"per_page": -10})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # per_pageが正の整数の場合（100を超えても許容、実行時に制限される）
        errors = await service.validate_search_params({"per_page": 1})
        assert len(errors) == 0

        errors = await service.validate_search_params({"per_page": 50})
        assert len(errors) == 0

        errors = await service.validate_search_params({"per_page": 100})
        assert len(errors) == 0

        errors = await service.validate_search_params({"per_page": 200})
        assert len(errors) == 0  # バリデーションエラーなし（実行時に100に制限）

    @pytest.mark.asyncio
    async def test_validation_min_rating_range(self, service_and_db):
        """最低評価のバリデーション（0.0〜5.0）"""
        service, db = service_and_db

        # 範囲外（負の値）
        errors = await service.validate_search_params({"min_rating": -1.0})
        assert len(errors) > 0
        assert any("Min rating must be between 0 and 5" in err for err in errors)

        # 範囲外（5.0を超える）
        errors = await service.validate_search_params({"min_rating": 5.5})
        assert len(errors) > 0
        assert any("Min rating must be between 0 and 5" in err for err in errors)

        # 範囲内
        errors = await service.validate_search_params({"min_rating": 0.0})
        assert len(errors) == 0

        errors = await service.validate_search_params({"min_rating": 2.5})
        assert len(errors) == 0

        errors = await service.validate_search_params({"min_rating": 5.0})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validation_max_rating_range(self, service_and_db):
        """最高評価のバリデーション（0.0〜5.0）"""
        service, db = service_and_db

        # 範囲外（負の値）
        errors = await service.validate_search_params({"max_rating": -0.5})
        assert len(errors) > 0
        assert any("Max rating must be between 0 and 5" in err for err in errors)

        # 範囲外（5.0を超える）
        errors = await service.validate_search_params({"max_rating": 6.0})
        assert len(errors) > 0
        assert any("Max rating must be between 0 and 5" in err for err in errors)

        # 範囲内
        errors = await service.validate_search_params({"max_rating": 0.0})
        assert len(errors) == 0

        errors = await service.validate_search_params({"max_rating": 3.5})
        assert len(errors) == 0

        errors = await service.validate_search_params({"max_rating": 5.0})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validation_rating_range_min_max_relationship(self, service_and_db):
        """評価範囲のバリデーション（min ≤ max）"""
        service, db = service_and_db

        # min > max の場合
        errors = await service.validate_search_params({
            "min_rating": 4.0,
            "max_rating": 2.0
        })
        assert len(errors) > 0
        assert any("Min rating cannot be greater than max rating" in err for err in errors)

        # min = max の場合（有効）
        errors = await service.validate_search_params({
            "min_rating": 3.0,
            "max_rating": 3.0
        })
        assert len(errors) == 0

        # min < max の場合（有効）
        errors = await service.validate_search_params({
            "min_rating": 2.0,
            "max_rating": 4.0
        })
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validation_multiple_errors(self, service_and_db):
        """複数のバリデーションエラーが同時に返される"""
        service, db = service_and_db

        errors = await service.validate_search_params({
            "page": -1,
            "per_page": 0,
            "min_rating": -1.0,
            "max_rating": 6.0
        })

        # 複数のエラーが含まれることを確認
        assert len(errors) >= 3
        assert any("Page must be a positive integer" in err for err in errors)
        assert any("per_page must be a positive integer" in err for err in errors)
        assert any("rating" in err.lower() for err in errors)

    @pytest.mark.asyncio
    async def test_validation_empty_params(self, service_and_db):
        """パラメータが空の場合（デフォルト値が使用される）"""
        service, db = service_and_db

        errors = await service.validate_search_params({})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validation_type_errors(self, service_and_db):
        """型エラーのバリデーション"""
        service, db = service_and_db

        # ページ番号が文字列の場合
        errors = await service.validate_search_params({"page": "abc"})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # per_pageが文字列の場合
        errors = await service.validate_search_params({"per_page": "xyz"})
        assert len(errors) > 0
        assert any("positive integer" in err for err in errors)

        # 評価が文字列の場合
        errors = await service.validate_search_params({"min_rating": "high"})
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_search_with_invalid_params_returns_error(self, service_and_db):
        """無効なパラメータでの検索がエラーを返す"""
        service, db = service_and_db

        result = await service.search_companies({
            "page": -1,
            "min_rating": 10.0
        })

        assert result["success"] is False
        assert result["error_code"] == "validation_error"
        assert "errors" in result
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_search_with_valid_params_succeeds(self, service_and_db):
        """有効なパラメータでの検索が成功する"""
        service, db = service_and_db

        result = await service.search_companies({
            "page": 1,
            "per_page": 20,
            "min_rating": 2.0,
            "max_rating": 4.5,
            "name": "テスト",
            "location": "東京"
        })

        assert result["success"] is True
        assert "companies" in result
        assert "total_count" in result
