"""
個別レビュー詳細テンプレートのテスト (Task 4.1: TDD RED 段階)

このテストはテンプレートが正しくレンダリングされ、必要な要素が含まれていることを確認します。
"""
import pytest
from tornado.template import Loader
from datetime import datetime, timezone
from pathlib import Path


class TestReviewDetailTemplateRendering:
    """Task 4.1: 個別レビュー詳細テンプレートのレンダリングテスト"""

    @pytest.fixture
    def template_loader(self):
        """テンプレートローダーを作成"""
        template_path = Path(__file__).parent.parent / "templates"
        return Loader(str(template_path))

    @pytest.fixture
    def sample_review_data(self):
        """テスト用のサンプルレビューデータ"""
        from zoneinfo import ZoneInfo

        created_at_utc = datetime(2025, 11, 15, 10, 30, 0, tzinfo=timezone.utc)
        created_at_jst = created_at_utc.astimezone(ZoneInfo("Asia/Tokyo"))

        return {
            "id": "test_review_123",
            "company_id": "test_company_456",
            "anonymous_user": "ユーザーA",
            "employment_status": "現職",
            "employment_period": {
                "start_year": 2020,
                "end_year": None
            },
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
            "created_at": created_at_utc,
            "created_at_jst": created_at_jst,
            "language": "ja"
        }

    @pytest.fixture
    def category_labels(self):
        """評価項目の日本語ラベル"""
        return {
            "recommendation": "推薦度",
            "foreign_support": "受入制度",
            "company_culture": "会社風土",
            "employee_relations": "関係性",
            "evaluation_system": "評価制度",
            "promotion_treatment": "昇進待遇"
        }

    def test_template_file_exists(self):
        """review_detail.htmlテンプレートファイルが存在することを確認"""
        template_path = Path(__file__).parent.parent / "templates" / "review_detail.html"
        assert template_path.exists(), "review_detail.html テンプレートファイルが存在しません"

    def test_template_renders_without_error(self, template_loader, sample_review_data, category_labels):
        """テンプレートがエラーなしでレンダリングできることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        )

        assert html is not None
        assert len(html) > 0

    def test_template_contains_breadcrumb(self, template_loader, sample_review_data, category_labels):
        """パンくずリストが含まれていることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "breadcrumb" in html.lower() or "パンくず" in html
        assert "ホーム" in html
        assert "企業一覧" in html
        assert "株式会社テスト" in html

    def test_template_contains_company_name_link(self, template_loader, sample_review_data, category_labels):
        """企業名リンクが含まれていることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "株式会社テスト" in html
        assert "/companies/test_company_456" in html or "test_company_456" in html

    def test_template_contains_anonymous_user(self, template_loader, sample_review_data, category_labels):
        """匿名化されたユーザー名が表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "ユーザーA" in html

    def test_template_contains_employment_status(self, template_loader, sample_review_data, category_labels):
        """在籍状況が表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "現職" in html

    def test_template_contains_employment_period(self, template_loader, sample_review_data, category_labels):
        """勤務期間が表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "2020" in html

    def test_template_contains_individual_average_rating(self, template_loader, sample_review_data, category_labels):
        """個別平均評価スコアが表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "3.8" in html

    def test_template_contains_all_category_labels(self, template_loader, sample_review_data, category_labels):
        """すべての評価項目ラベルが表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "推薦度" in html
        assert "受入制度" in html
        assert "会社風土" in html
        assert "関係性" in html
        assert "評価制度" in html
        assert "昇進待遇" in html

    def test_template_shows_ratings(self, template_loader, sample_review_data, category_labels):
        """評価スコアが表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # 星評価または数値評価が表示されていることを確認
        assert "★" in html or "star" in html.lower() or "4" in html

    def test_template_shows_comments_in_full_mode(self, template_loader, sample_review_data, category_labels):
        """フルモードでコメントが表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "働きやすい会社です" in html
        assert "サポート体制が充実" in html
        assert "オープンな文化" in html

    def test_template_masks_comments_in_preview_mode(self, template_loader, sample_review_data, category_labels):
        """プレビューモードでコメントがマスクされることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=True,
            access_level="PREVIEW",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # コメントがマスクされているか、元のコメントが表示されていないことを確認
        assert "働きやすい会社です" not in html or "***" in html or "マスク" in html or "レビューを投稿" in html

    def test_template_shows_unanswered_for_null_ratings(self, template_loader, sample_review_data, category_labels):
        """未回答の項目で「未回答」が表示されることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # evaluation_systemは未回答なので「未回答」が表示されるべき
        assert "未回答" in html or "N/A" in html or "回答なし" in html

    def test_template_contains_back_to_company_link(self, template_loader, sample_review_data, category_labels):
        """企業ページに戻るリンクが含まれていることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        assert "戻る" in html or "企業ページ" in html
        assert "/companies/test_company_456" in html

    def test_template_has_responsive_meta_tag(self, template_loader, sample_review_data, category_labels):
        """テンプレートがbase.htmlを継承してレスポンシブ対応していることを確認"""
        template = template_loader.load("review_detail.html")

        html = template.generate(
            review=sample_review_data,
            company_name="株式会社テスト",
            company_id="test_company_456",
            preview_mode=False,
            access_level="FULL",
            category_labels=category_labels,
            handler=type('Handler', (), {'get_flash_message': lambda self: None})()
        ).decode('utf-8')

        # base.htmlを継承しているため、viewportメタタグが含まれているはず
        assert "viewport" in html.lower() or "responsive" in html.lower() or html.startswith("<!doctype html")
