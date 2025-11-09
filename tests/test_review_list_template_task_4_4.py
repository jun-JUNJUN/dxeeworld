"""
ReviewListテンプレート の Task 4.4 機能のテスト
Task 4.4: ページネーションUIの実装

このテストは、テンプレートが正しいページネーションマークアップと
必要なUI要素を含んでいるかを検証します。
"""
import pytest
from pathlib import Path


class TestReviewListTemplateTask44:
    """Task 4.4: ページネーションUIのテスト"""

    def test_template_file_exists(self):
        """reviews/list.html テンプレートが存在する"""
        template_path = Path("templates/reviews/list.html")
        assert template_path.exists(), f"Template not found: {template_path}"

    def test_page_number_links_markup_exists(self):
        """ページ番号リンクの表示マークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # ページ番号のループ
        assert "{% for page_num in range(" in content
        # ページ番号リンク
        assert "{{ page_num }}" in content

    def test_previous_button_markup_exists(self):
        """「前へ」ボタンのマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 前へボタン
        assert "前へ" in content
        # 1ページ目での無効化条件
        assert "{% if pagination['page'] > 1 %}" in content

    def test_next_button_markup_exists(self):
        """「次へ」ボタンのマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 次へボタン
        assert "次へ" in content
        # 最終ページでの無効化条件
        assert "{% if pagination['page'] < pagination['pages'] %}" in content

    def test_current_page_highlight_markup_exists(self):
        """現在のページ番号をハイライト表示するマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # activeクラスの条件分岐
        assert "{% if page_num == pagination['page'] %}active{% end %}" in content

    def test_search_params_preserved_in_pagination_links(self):
        """ページ遷移時に検索パラメータを保持するマークアップが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 検索パラメータの保持（前へボタン）
        assert "search_params.items()" in content
        # ページパラメータ以外を保持
        assert "if k != 'page'" in content

    def test_pagination_conditional_display(self):
        """ページ数が1より多い場合のみページネーションを表示する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # ページネーションの表示条件
        assert "{% if pagination['pages'] > 1 %}" in content

    def test_pagination_uses_bootstrap_classes(self):
        """Bootstrapのページネーションクラスを使用している"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # Bootstrapクラス
        assert "pagination" in content
        assert "page-item" in content
        assert "page-link" in content

    def test_pagination_navigation_accessible(self):
        """ページネーションにaria-label属性が設定されている"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # アクセシビリティ属性
        assert 'aria-label="Page navigation"' in content

    def test_page_range_calculation_logic(self):
        """ページ番号の範囲計算ロジックが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 現在ページの前後2ページを表示
        assert "pagination['page'] - 2" in content
        assert "pagination['page'] + 3" in content
        # 最小値と最大値の制約
        assert "max(1," in content
        assert "min(pagination['pages'] + 1," in content

    def test_previous_button_disabled_on_first_page(self):
        """1ページ目で「前へ」ボタンが表示されないロジック"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # pagination['page'] > 1 の条件チェック
        lines = content.split('\n')
        found_prev_condition = False
        found_prev_button = False

        for i, line in enumerate(lines):
            if "{% if pagination['page'] > 1 %}" in line:
                found_prev_condition = True
                # 次の数行以内に「前へ」ボタンがあるか確認
                for j in range(i, min(i + 10, len(lines))):
                    if "前へ" in lines[j]:
                        found_prev_button = True
                        break

        assert found_prev_condition, "Previous button condition not found"
        assert found_prev_button, "Previous button not found after condition"

    def test_next_button_disabled_on_last_page(self):
        """最終ページで「次へ」ボタンが表示されないロジック"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # pagination['page'] < pagination['pages'] の条件チェック
        lines = content.split('\n')
        found_next_condition = False
        found_next_button = False

        for i, line in enumerate(lines):
            if "{% if pagination['page'] < pagination['pages'] %}" in line:
                found_next_condition = True
                # 次の数行以内に「次へ」ボタンがあるか確認
                for j in range(i, min(i + 10, len(lines))):
                    if "次へ" in lines[j]:
                        found_next_button = True
                        break

        assert found_next_condition, "Next button condition not found"
        assert found_next_button, "Next button not found after condition"

    def test_page_links_preserve_all_search_params(self):
        """全てのページリンクが検索パラメータを保持する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # ページリンクでパラメータを保持
        # 前へボタン
        assert "?page={{ pagination['page'] - 1 }}&{{ '&'.join(" in content
        # ページ番号リンク
        assert "?page={{ page_num }}&{{ '&'.join(" in content
        # 次へボタン
        assert "?page={{ pagination['page'] + 1 }}&{{ '&'.join(" in content

    def test_pagination_displays_centered(self):
        """ページネーションが中央揃えで表示される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # Bootstrapの中央揃えクラス
        assert "justify-content-center" in content
