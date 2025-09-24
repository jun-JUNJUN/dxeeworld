"""
Test for mobile bottom tab navigation - Task 4.1, 4.2
"""
import pytest
import re


class TestMobileTabNavigation:
    """モバイル下部タブナビゲーションテスト"""

    def test_mobile_tab_bar_exists_in_base_template(self):
        """base.htmlにモバイルタブバーが存在することを確認 - Task 4.1"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # モバイルタブバー要素の存在確認
        mobile_tab_patterns = [
            r'mobile-tab-bar',
            r'class="tab-item"',
            r'data-page="home"',
            r'data-page="reviews"',
            r'data-page="companies"',
        ]

        for pattern in mobile_tab_patterns:
            assert re.search(pattern, content, re.IGNORECASE), f"モバイルタブバー要素が見つかりません: {pattern}"

    def test_mobile_tab_bar_has_three_tabs(self):
        """モバイルタブバーが3つのタブ（Home, Reviews, Companies）を含むことを確認 - Task 4.1"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 各タブの存在確認
        required_tabs = [
            (r'href="/".*?Home', "Homeタブ"),
            (r'href="/review".*?Reviews', "Reviewsタブ"),
            (r'href="/companies".*?Companies', "Companiesタブ"),
        ]

        for pattern, description in required_tabs:
            assert re.search(pattern, content, re.IGNORECASE | re.DOTALL), f"{description}が見つかりません"

    def test_mobile_tab_bar_css_positioning(self):
        """モバイルタブバーのCSS固定配置が実装されていることを確認 - Task 4.1"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # CSS固定配置のパターンを確認
        positioning_patterns = [
            r'position:\s*fixed',
            r'bottom:\s*0',
            r'z-index:\s*\d+',
            r'@media.*max-width.*767px',
        ]

        for pattern in positioning_patterns:
            assert re.search(pattern, content, re.IGNORECASE), f"CSS固定配置要素が見つかりません: {pattern}"

    def test_sidebar_hidden_on_mobile(self):
        """モバイル環境でサイドバーが非表示になることを確認 - Task 4.2"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # モバイル環境でのサイドバー非表示CSS
        sidebar_hidden_patterns = [
            r'\.sidebar.*display:\s*none',
            r'@media.*max-width.*767px.*\.sidebar.*display:\s*none',
        ]

        found_sidebar_hidden = any(re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                                 for pattern in sidebar_hidden_patterns)
        assert found_sidebar_hidden, "モバイル環境でのサイドバー非表示CSSが見つかりません"

    def test_main_content_margin_adjustment(self):
        """メインコンテンツのマージン調整が実装されていることを確認 - Task 4.2"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # メインコンテンツのマージン調整パターン
        margin_patterns = [
            r'\.main-content.*margin-left:\s*0',
            r'\.main-content.*padding-bottom:\s*\d+px',
        ]

        found_margin_adjustments = []
        for pattern in margin_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                found_margin_adjustments.append(pattern)

        assert len(found_margin_adjustments) >= 1, f"メインコンテンツマージン調整が不足: 見つかった要素 {found_margin_adjustments}"

    def test_responsive_navigation_switching(self):
        """レスポンシブナビゲーション切り替えが実装されていることを確認"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # PC環境でのタブバー非表示確認
        pc_tab_hidden_patterns = [
            r'@media.*min-width:\s*768px.*\.mobile-tab-bar.*display:\s*none',
            r'\.mobile-tab-bar.*display:\s*none',
        ]

        found_pc_hidden = any(re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                            for pattern in pc_tab_hidden_patterns)
        assert found_pc_hidden, "PC環境でのタブバー非表示CSSが見つかりません"

    def test_tab_icons_and_labels_exist(self):
        """タブアイコンとラベルが存在することを確認 - Task 4.1"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # アイコンとラベルのパターン
        icon_label_patterns = [
            r'tab-icon.*🏠',  # Home icon
            r'tab-label.*Home',  # Home label
            r'tab-icon.*⭐',  # Reviews icon
            r'tab-label.*Reviews',  # Reviews label
            r'tab-icon.*🏢',  # Companies icon
            r'tab-label.*Companies',  # Companies label
        ]

        found_elements = []
        for pattern in icon_label_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                found_elements.append(pattern)

        assert len(found_elements) >= 4, f"タブアイコン・ラベル要素が不足: 見つかった要素 {len(found_elements)}/6"