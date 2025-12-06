"""
質問別レビュー一覧テンプレートのテスト (Task 4.2 & 4.3: TDD RED 段階)

このテストはテンプレートが正しくレンダリングされ、必要な要素が含まれていることを確認します。
"""
import pytest
from tornado.template import Loader
from datetime import datetime, timezone
from pathlib import Path


class TestCategoryReviewListTemplateRendering:
    """Task 4.2 & 4.3: 質問別レビュー一覧テンプレートのレンダリングテスト"""

    @pytest.fixture
    def template_loader(self):
        """テンプレートローダーを作成"""
        template_path = Path(__file__).parent.parent / "templates"
        return Loader(str(template_path))

    @pytest.fixture
    def sample_reviews_data(self):
        """テスト用のサンプルレビューリストデータ"""
        from zoneinfo import ZoneInfo

        jst = ZoneInfo("Asia/Tokyo")

        created_at_1 = datetime(2025, 11, 15, 10, 30, 0, tzinfo=timezone.utc)
        created_at_2 = datetime(2025, 11, 10, 15, 45, 0, tzinfo=timezone.utc)
        created_at_3 = datetime(2025, 11, 5, 9, 15, 0, tzinfo=timezone.utc)

        return [
            {
                "id": "review_1",
                "company_id": "test_company_456",
                "anonymous_user": "ユーザーA",
                "employment_status": "現職",
                "employment_period": {
                    "start_year": 2020,
                    "end_year": None
                },
                "ratings": {
                    "foreign_support": 4
                },
                "comments": {
                    "foreign_support": "サポート体制が充実しています"
                },
                "created_at": created_at_1,
                "created_at_jst": created_at_1.astimezone(jst)
            },
            {
                "id": "review_2",
                "company_id": "test_company_456",
                "anonymous_user": "ユーザーB",
                "employment_status": "元職",
                "employment_period": {
                    "start_year": 2018,
                    "end_year": 2023
                },
                "ratings": {
                    "foreign_support": 3
                },
                "comments": {
                    "foreign_support": "改善の余地があります"
                },
                "created_at": created_at_2,
                "created_at_jst": created_at_2.astimezone(jst)
            },
            {
                "id": "review_3",
                "company_id": "test_company_456",
                "anonymous_user": "ユーザーC",
                "employment_status": "現職",
                "employment_period": {
                    "start_year": 2021,
                    "end_year": None
                },
                "ratings": {
                    "foreign_support": None
                },
                "comments": {
                    "foreign_support": None
                },
                "created_at": created_at_3,
                "created_at_jst": created_at_3.astimezone(jst)
            }
        ]

    @pytest.fixture
    def pagination_info(self):
        """ページネーション情報"""
        return {
            "current_page": 1,
            "total_pages": 3,
            "total_count": 52,
            "per_page": 20,
            "has_prev": False,
            "has_next": True,
            "prev_page": None,
            "next_page": 2
        }

    def test_template_file_exists(self):
        """category_review_list.htmlテンプレートファイルが存在することを確認"""
        template_path = Path(__file__).parent.parent / "templates" / "category_review_list.html"
        assert template_path.exists(), "category_review_list.html テンプレートファイルが存在しません"

    def test_template_renders_without_error(self, template_loader, sample_reviews_data, pagination_info):
        """テンプレートがエラーなしでレンダリングできることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        )

        assert html is not None
        assert len(html) > 0

    def test_template_contains_breadcrumb(self, template_loader, sample_reviews_data, pagination_info):
        """パンくずリストが含まれていることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "breadcrumb" in html.lower() or "パンくず" in html
        assert "ホーム" in html
        assert "企業一覧" in html
        assert "株式会社テスト" in html
        assert "受入制度" in html

    def test_template_contains_page_header(self, template_loader, sample_reviews_data, pagination_info):
        """ページヘッダーが含まれていることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # ページヘッダーに企業名、評価項目名、レビュー総数が含まれていることを確認
        assert "株式会社テスト" in html
        assert "受入制度" in html
        assert "52" in html  # total_count

    def test_template_displays_review_cards(self, template_loader, sample_reviews_data, pagination_info):
        """レビューカードが表示されることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # レビューカードの要素が含まれていることを確認
        assert "ユーザーA" in html
        assert "ユーザーB" in html
        assert "現職" in html
        assert "元職" in html

    def test_template_shows_review_comments_in_full_mode(self, template_loader, sample_reviews_data, pagination_info):
        """フルモードでコメントが表示されることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "サポート体制が充実しています" in html
        assert "改善の余地があります" in html

    def test_template_masks_comments_in_preview_mode(self, template_loader, sample_reviews_data, pagination_info):
        """プレビューモードでコメントがマスクされることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=True,
            access_level="PREVIEW",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # コメントがマスクされていることを確認
        assert "サポート体制が充実しています" not in html or "***" in html or "マスク" in html or "レビューを投稿" in html

    def test_template_shows_unanswered_reviews(self, template_loader, sample_reviews_data, pagination_info):
        """未回答レビューが適切に表示されることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # ユーザーCは未回答なので、「未回答」が表示されるべき
        assert "未回答" in html or "回答なし" in html or "N/A" in html

    def test_template_contains_detail_links(self, template_loader, sample_reviews_data, pagination_info):
        """詳細リンクが含まれていることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # 詳細リンクが含まれていることを確認
        assert "詳細" in html or "detail" in html.lower()
        assert "/companies/test_company_456/reviews/review_1" in html

    def test_template_contains_pagination(self, template_loader, sample_reviews_data, pagination_info):
        """ページネーションが含まれていることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # ページネーション要素が含まれていることを確認
        assert "pagination" in html.lower() or "ページ" in html
        assert "次" in html or "next" in html.lower()

    def test_template_shows_current_page_number(self, template_loader, sample_reviews_data, pagination_info):
        """現在のページ番号が表示されることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # 現在のページ番号と総ページ数が表示されていることを確認
        assert "1" in html
        assert "3" in html

    def test_template_shows_empty_message_for_zero_reviews(self, template_loader, pagination_info):
        """レビュー0件時のメッセージが表示されることを確認"""
        template = template_loader.load("category_review_list.html")

        empty_pagination = pagination_info.copy()
        empty_pagination["total_count"] = 0
        empty_pagination["total_pages"] = 0

        html = template.generate(
            reviews=[],
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=empty_pagination,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # レビューがない旨のメッセージが表示されていることを確認
        assert "レビューがありません" in html or "レビューはまだありません" in html or "No reviews" in html.lower()

    def test_template_contains_back_to_company_link(self, template_loader, sample_reviews_data, pagination_info):
        """企業ページに戻るリンクが含まれていることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "戻る" in html or "企業ページ" in html
        assert "/companies/test_company_456" in html

    def test_template_has_responsive_design(self, template_loader, sample_reviews_data, pagination_info):
        """テンプレートがレスポンシブデザインに対応していることを確認"""
        template = template_loader.load("category_review_list.html")

        html = template.generate(
            reviews=sample_reviews_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            category_name="foreign_support",
            category_label="受入制度",
            pagination=pagination_info,
            preview_mode=False,
            access_level="FULL",
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # レスポンシブデザインのためのメタタグやメディアクエリが含まれていることを確認
        assert "viewport" in html.lower() or "@media" in html.lower() or "responsive" in html.lower()
