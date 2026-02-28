"""
Test for company detail page redesign - Task 5

TDD Implementation: RED phase - Write failing tests first
"""
import pytest
import re


class TestCompanyDetailRedesignTask5:
    """企業詳細ページの再設計テスト - Task 5"""

    # ========== 5.1 企業詳細ページヘッダー実装 ==========

    def test_company_detail_header_has_white_background(self):
        """企業詳細ページヘッダーが背景色#FFFFFFを持つこと - Requirement 7.2"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # ヘッダーセクションの存在を確認
        header_patterns = [
            r'company.*header',
            r'background.*#fff|background.*white',
            r'padding:\s*32px',
        ]

        found_patterns = []
        for pattern in header_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"企業詳細ヘッダーのスタイル要素が不足しています。見つかった要素: {found_patterns}"

    def test_company_header_has_company_name_28px_bold(self):
        """企業名が28px、font-weight 700で表示されること - Requirement 7.2"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 企業名のスタイル確認
        company_name_patterns = [
            r'company.*name.*28px',
            r'font-size:\s*28px',
            r'font-weight:\s*700',
        ]

        found_patterns = []
        for pattern in company_name_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"企業名のスタイル要素が不足しています。見つかった要素: {found_patterns}"

    def test_company_header_has_rating_stars_24px(self):
        """評価スターが24pxで表示されること - Requirement 7.1, 7.2"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 評価スターの表示確認
        rating_patterns = [
            r'rating.*star',
            r'\u2605|\u2606|★',  # 星記号
            r'24px|font-size:\s*1\.5rem',  # 24px相当
        ]

        found_patterns = []
        for pattern in rating_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"評価スター表示要素が不足しています。見つかった要素: {found_patterns}"

    def test_company_header_has_tagline(self):
        """タグラインが表示されること - Requirement 7.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # タグラインまたは説明文の存在確認
        tagline_patterns = [
            r'tagline',
            r'description',
            r'company.*desc',
        ]

        found_pattern = any(re.search(pattern, content, re.IGNORECASE) for pattern in tagline_patterns)
        assert found_pattern, "タグラインまたは企業説明文が見つかりません"

    def test_company_header_has_meta_info(self):
        """業種・地域・企業規模が表示されること - Requirement 7.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # メタ情報の表示確認
        meta_patterns = [
            r'industry|業界',
            r'location|地域|所在地',
            r'size|規模',
        ]

        found_patterns = []
        for pattern in meta_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"企業メタ情報が不足しています。見つかった要素: {found_patterns}"

    def test_company_header_has_external_links(self):
        """外部リンクボタン「🌐 Website」「📧 Careers」が存在すること - Requirement 7.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 外部リンクの確認
        external_link_patterns = [
            r'Website|website',
            r'Careers|jobs',
            r'🌐|\u1f310',  # 地球絵文字
            r'📧|\u1f4e7',  # 封筒絵文字
            r'href.*company\.',
        ]

        found_patterns = []
        for pattern in external_link_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 3, \
            f"外部リンクボタンが不足しています。見つかった要素: {found_patterns}"

    # ========== 5.2 タブナビゲーション実装 ==========

    def test_tab_navigation_has_four_tabs(self):
        """タブナビゲーションが「概要」「レビュー(125)」「統計」「求人情報」を含むこと - Requirement 7.3"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # タブの存在確認
        tab_patterns = [
            r'概要|Overview',
            r'レビュー|Review',
            r'統計|Stats',
            r'求人情報|Jobs',
        ]

        found_patterns = []
        for pattern in tab_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 3, \
            f"タブナビゲーションが不足しています。見つかった要素: {found_patterns}"

    def test_tab_normal_state_color_666(self):
        """タブの通常状態でcolor #666、border-bottom 2px solid transparentが適用されること - Requirement 7.5"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 通常状態のタブスタイル確認
        normal_tab_patterns = [
            r'#666|rgb\(102,\s*102,\s*102\)',
            r'border-bottom:\s*2px\s+solid\s+transparent',
        ]

        found_patterns = []
        for pattern in normal_tab_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 1, \
            f"タブ通常状態のスタイルが見つかりません。見つかった要素: {found_patterns}"

    def test_tab_active_state_primary_color(self):
        """タブ活性化時でcolor #20BEFF、border-bottom 2px solid #20BEFF、font-weight 600が適用されること - Requirement 7.4"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 活性状態のタブスタイル確認
        active_tab_patterns = [
            r'#20beff|rgb\(32,\s*190,\s*255\)',
            r'border-bottom:\s*2px\s+solid\s+#20beff',
            r'font-weight:\s*600',
        ]

        found_patterns = []
        for pattern in active_tab_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"タブ活性状態のスタイルが不足しています。見つかった要素: {found_patterns}"

    def test_tab_hover_state_color_1a8fcc(self):
        """タブホバー状態でcolor #1A8FCCが適用されること - Requirement 7.4"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # ホバー状態の確認
        hover_patterns = [
            r'#1a8fcc|rgb\(26,\s*143,\s*204\)',
            r':hover',
        ]

        found_hover = any(re.search(pattern, content, re.IGNORECASE) for pattern in hover_patterns)
        assert found_hover, "タブホバー状態のスタイルが見つかりません"

    def test_tab_click_switches_content(self):
        """タブクリック時の内容切り替え機能が実装されていること - Requirement 7.5"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # タブ切り替え機能の確認（JavaScriptまたはCSS）
        tab_switch_patterns = [
            r'onclick|addEventListener|click',
            r'tab.*switch|tab.*change',
            r'content.*tab|tab.*content',
            r'display:\s*none|visibility:\s*hidden',
        ]

        found_patterns = []
        for pattern in tab_switch_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"タブ切り替え機能が不足しています。見つかった要素: {found_patterns}"

    # ========== 5.3 統計情報表示セクション実装 ==========

    def test_stats_section_has_overall_rating(self):
        """統計情報セクションに総合評価★スコア表示があること - Requirement 7.6, 12.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 総合評価スコアの表示確認
        overall_rating_patterns = [
            r'overall.*rating|総合評価',
            r'\u2605|\u2606|★',  # 星記号
            r'score|スコア',
        ]

        found_patterns = []
        for pattern in overall_rating_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, \
            f"総合評価スコア表示が不足しています。見つかった要素: {found_patterns}"

    def test_stats_section_has_category_scores(self):
        """カテゴリー別平均スコア（8カテゴリー）が表示されること - Requirement 7.6, 12.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 8カテゴリーのスコア表示確認
        # 新しい8カテゴリー: 待遇・報酬, ワークライフバランス, 企業文化, キャリア・成長, マネジメント・組織, 評価・処遇制度, 職場環境, 事業・製品
        category_patterns = [
            r'待遇.*報酬|compensation',
            r'ワークライフ|work.?life',
            r'企業文化|culture',
            r'キャリア|career',
            r'マネジメント|management',
            r'評価.*処遇|performance|evaluation',
            r'職場環境|environment',
            r'事業.*製品|business',
        ]

        found_patterns = []
        for pattern in category_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 4, \
            f"カテゴリー別スコア表示が不足しています。見つかった要素: {found_patterns}"

    def test_stats_section_has_radar_or_bar_chart(self):
        """レーダーチャートまたは棒グラフでの可視化があること - Requirement 7.6, 12.4, 12.6"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # チャート表示の確認
        chart_patterns = [
            r'radar.*chart|レーダーチャート',
            r'bar.*chart|棒グラフ',
            r'chart\.js|d3\.js|canvas',
            r'visualization|可視化',
        ]

        found_chart = any(re.search(pattern, content, re.IGNORECASE) for pattern in chart_patterns)
        assert found_chart, "チャート表示要素が見つかりません"

    def test_stats_section_has_industry_comparison(self):
        """業界平均値との比較表示があること - Requirement 12.3, 12.4"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 業界平均比較の確認
        comparison_patterns = [
            r'industry.*average|業界平均',
            r'benchmark|ベンチマーク',
            r'comparison|比較',
        ]

        found_comparison = any(re.search(pattern, content, re.IGNORECASE) for pattern in comparison_patterns)
        assert found_comparison, "業界平均比較要素が見つかりません"

    def test_stats_mobile_radar_to_bar_switch(self):
        """モバイル対応：レーダーチャートを棒グラフに切り替えられること - Requirement 7.6, 12.6"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # モバイル用チャート切り替え機能の確認
        mobile_chart_patterns = [
            r'@media.*max-width.*768px',
            r'mobile.*chart|モバイル.*チャート',
            r'bar.*chart.*mobile|モバイル.*bar.*chart',
        ]

        found_mobile = any(re.search(pattern, content, re.IGNORECASE) for pattern in mobile_chart_patterns)
        assert found_mobile, "モバイル用チャート切り替え機能が見つかりません"

    # ========== 5.4 companies/detail.html テンプレート統合 ==========

    def test_detail_template_has_header_tabs_stats_reviews(self):
        """ヘッダー、タブナビゲーション、統計セクション、レビューリストが統合されていること - Requirement 7.1~7.6"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 全セクションの存在確認
        all_sections_patterns = [
            (r'company.*header|企業.*ヘッダー', '企業ヘッダー'),
            (r'tab.*navigation|タブ.*ナビ|tab-', 'タブナビゲーション'),
            (r'stats.*section|統計.*セクション|stats-', '統計セクション'),
            (r'review.*section|レビュー.*セクション|review-', 'レビューリスト'),
        ]

        found_sections = {}
        for pattern, name in all_sections_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_sections[name] = True
            else:
                found_sections[name] = False

        missing_sections = [name for name, found in found_sections.items() if not found]

        assert len(missing_sections) == 0, \
            f"テンプレートに不足しているセクションがあります: {missing_sections}"

    def test_template_uses_css_variables(self):
        """テンプレートがCSS変数を使用していること - Requirement 13.1~13.5"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # CSS変数の使用確認
        css_var_patterns = [
            r'var\(--color-primary',
            r'var\(--color-text-primary',
            r'var\(--spacing-',
            r'var\(--font-size-',
        ]

        found_vars = []
        for pattern in css_var_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_vars.append(pattern)

        assert len(found_vars) >= 2, \
            f"CSS変数の使用が不足しています。見つかった変数: {found_vars}"
