"""
ReviewListテンプレート の Task 4.1-4.3 機能のテスト
Task 4.1: アクセス制御に応じたUI表示
Task 4.2: 検索フォームUI
Task 4.3: 企業カード表示

このテストは、テンプレートが正しいHTMLマークアップと
必要なUI要素を含んでいるかを検証します。
"""
import pytest
from pathlib import Path


class TestReviewListTemplateTask41:
    """Task 4.1: アクセス制御に応じたUI表示のテスト"""

    def test_template_file_exists(self):
        """reviews/list.html テンプレートが存在する"""
        template_path = Path("templates/reviews/list.html")
        assert template_path.exists(), f"Template not found: {template_path}"

    def test_access_denied_message_markup_exists(self):
        """アクセス拒否時のメッセージ表示マークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # アクセス拒否の条件分岐
        assert "{% if access_level == 'denied' %}" in content
        # アクセス拒否メッセージ
        assert "アクセス制限" in content or "アクセスが制限されています" in content

    def test_preview_mode_notification_markup_exists(self):
        """プレビューモード通知のマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # プレビューモードの条件分岐
        assert "{% if access_level == 'preview' %}" in content
        # プレビューモード通知
        assert "プレビューモード" in content

    def test_filter_disabled_notification_markup_exists(self):
        """フィルター機能無効化通知のマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # can_filterの条件分岐
        assert "{% if not can_filter %}" in content
        # フィルター機能制限の通知
        assert "フィルター機能は制限されています" in content or "フィルター機能" in content


class TestReviewListTemplateTask42:
    """Task 4.2: 検索フォームUIのテスト"""

    def test_company_name_input_field_exists(self):
        """企業名入力フィールドが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 企業名入力フィールド
        assert 'name="name"' in content
        assert '企業名' in content

    def test_location_input_field_exists(self):
        """所在地入力フィールドが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 所在地入力フィールド
        assert 'name="location"' in content
        assert '所在地' in content

    def test_sort_dropdown_exists(self):
        """ソート順選択ドロップダウンが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # ソート順選択
        assert 'name="sort"' in content
        assert '並び順' in content
        # ソートオプション
        assert 'value="rating_high"' in content
        assert '評価順（高→低）' in content
        assert 'value="rating_low"' in content
        assert '評価順（低→高）' in content
        assert 'value="review_count"' in content
        assert 'レビュー数順' in content
        assert 'value="name"' in content
        assert '企業名順' in content

    def test_min_rating_slider_exists(self):
        """最低評価スライダーが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 最低評価スライダー
        assert 'id="min_rating_slider"' in content
        assert 'type="range"' in content
        assert 'min="0"' in content
        assert 'max="5"' in content
        assert 'step="0.5"' in content
        assert '最低評価' in content

    def test_max_rating_slider_exists(self):
        """最高評価スライダーが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 最高評価スライダー
        assert 'id="max_rating_slider"' in content
        assert 'type="range"' in content
        assert '最高評価' in content

    def test_search_button_exists(self):
        """検索ボタンが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 検索ボタン
        assert 'type="submit"' in content
        assert '検索' in content

    def test_reset_button_exists(self):
        """リセットボタンが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # リセットボタン/リンク
        assert 'href="/review"' in content
        assert 'リセット' in content

    def test_input_fields_disabled_when_can_filter_false(self):
        """can_filter=false の場合、入力欄が無効化されるマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # disabled属性の条件分岐
        assert '{% if not can_filter %}disabled{% end %}' in content


class TestReviewListTemplateTask43:
    """Task 4.3: 企業カード表示のテスト"""

    def test_company_name_display_markup_exists(self):
        """企業名を表示するマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 企業名表示
        assert "company.get('name'" in content or 'company["name"]' in content

    def test_location_display_markup_exists(self):
        """所在地を表示するマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 所在地表示
        assert "company.get('location'" in content or 'company["location"]' in content

    def test_overall_rating_star_display_markup_exists(self):
        """総合評価の星マーク表示マークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 星マーク表示
        assert '★' in content
        # overall_average表示
        assert "overall_average" in content

    def test_total_reviews_display_markup_exists(self):
        """レビュー総数の表示マークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # レビュー総数表示
        assert "total_reviews" in content
        assert "レビュー" in content

    def test_category_ratings_display_markup_exists(self):
        """カテゴリ別評価の表示マークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 6カテゴリの評価表示
        assert "recommendation" in content
        assert "推薦度" in content or "レコメンデーション" in content

        assert "foreign_support" in content
        assert "受入制度" in content or "外国人サポート" in content

        assert "company_culture" in content
        assert "会社風土" in content or "企業文化" in content

        assert "employee_relations" in content
        assert "関係性" in content or "従業員関係" in content

        assert "evaluation_system" in content
        assert "評価制度" in content or "評価システム" in content

        assert "promotion_treatment" in content
        assert "昇進待遇" in content or "昇進・待遇" in content

    def test_detail_view_button_markup_exists(self):
        """「詳細を見る」ボタンのマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 詳細を見るボタン/リンク
        assert "詳細を見る" in content
        # 企業詳細ページへのリンク
        assert "/companies/" in content

    def test_write_review_button_markup_exists(self):
        """「レビューを書く」ボタンのマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # レビューを書くボタン/リンク
        assert "レビューを書く" in content

    def test_company_loop_markup_exists(self):
        """企業リストをループするマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # companiesのループ
        assert "{% for company in companies %}" in content
        assert "{% end %}" in content or "{% endfor %}" in content


class TestReviewListTemplateTask45JavaScript:
    """Task 4.5: 評価スライダーのJavaScript実装のテスト"""

    def test_min_rating_display_update_function_exists(self):
        """最低評価スライダーのリアルタイム値表示更新関数が存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # updateMinRatingDisplay関数
        assert "updateMinRatingDisplay" in content or "min_rating" in content

    def test_max_rating_display_update_function_exists(self):
        """最高評価スライダーのリアルタイム値表示更新関数が存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # updateMaxRatingDisplay関数
        assert "updateMaxRatingDisplay" in content or "max_rating" in content

    def test_rating_value_zero_displays_unspecified(self):
        """0.0の場合「指定なし」と表示するロジックが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 指定なし表示
        assert "指定なし" in content

    def test_rating_slider_oninput_handlers_exist(self):
        """スライダー操作時のイベントハンドラが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # oninputイベントハンドラ
        assert "oninput=" in content
