"""
Test for navigation integration between pages - Task 9.3

Tests navigation links and user flows across:
- Company detail page to review detail page
- Company detail page to category review list page
- Review listing page to category review list page
- Mobile and desktop responsive behavior
"""
import pytest
import re


class TestNavigationIntegration:
    """ナビゲーション統合のテスト - Task 9.3"""

    def test_company_detail_to_review_detail_link_exists(self):
        """企業詳細ページからレビュー詳細ページへのリンクが存在することを確認 - Task 9.3.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 「詳細を見る」リンクの存在確認
        # URL pattern: /companies/{{ company['id'] }}/reviews/{{ review['id'] }}
        detail_link_pattern = r'/companies/.*?/reviews/.*?[\'"]'
        assert re.search(detail_link_pattern, content), "企業詳細ページにレビュー詳細リンクが見つかりません"

        # 「詳細を見る」テキストの存在確認
        assert re.search(r'詳細を見る', content), "「詳細を見る」テキストが見つかりません"

    def test_company_detail_to_category_review_list_links_exist(self):
        """企業詳細ページからカテゴリ別レビュー一覧へのリンクが存在することを確認 - Task 9.3.2"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 6つのカテゴリへのリンクを確認
        categories = [
            'recommendation',
            'foreign_support',
            'company_culture',
            'employee_relations',
            'evaluation_system',
            'promotion_treatment'
        ]

        for category in categories:
            category_link_pattern = rf'/companies/.*?/reviews/by-category/{category}'
            assert re.search(category_link_pattern, content), \
                f"カテゴリ {category} へのリンクが企業詳細ページに見つかりません"

    def test_review_list_to_category_review_list_links_exist(self):
        """レビュー一覧ページからカテゴリ別レビュー一覧へのリンクが存在することを確認 - Task 9.3.3"""
        with open('templates/reviews/list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # カテゴリバッジリンクの存在確認
        # URL pattern: /companies/{{ company['id'] }}/reviews/by-category/{category_name}
        category_link_pattern = r'/companies/.*?/reviews/by-category/.*?[\'"]'

        # 複数のカテゴリリンクが存在することを確認
        matches = re.findall(category_link_pattern, content)
        assert len(matches) >= 6, \
            f"レビュー一覧ページにカテゴリリンクが不足しています。期待: 6以上, 実際: {len(matches)}"

    def test_review_detail_back_to_company_link_exists(self):
        """レビュー詳細ページから企業詳細ページへの戻るリンクが存在することを確認 - Task 9.3.4"""
        with open('templates/review_detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 企業詳細ページへのリンクパターン
        company_link_pattern = r'/companies/.*?[\'"]'
        assert re.search(company_link_pattern, content), \
            "レビュー詳細ページに企業ページへのリンクが見つかりません"

        # 「戻る」または企業名リンクの存在確認
        back_patterns = [
            r'戻る',
            r'企業ページ',
            r'class=[\'"]company.*?name[\'"]',
        ]

        found_back_link = any(re.search(pattern, content, re.IGNORECASE)
                             for pattern in back_patterns)
        assert found_back_link, "レビュー詳細ページに戻るリンクまたは企業名リンクが見つかりません"

    def test_category_review_list_back_to_company_link_exists(self):
        """カテゴリ別レビュー一覧ページから企業詳細ページへの戻るリンクが存在することを確認 - Task 9.3.5"""
        with open('templates/category_review_list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 企業詳細ページへのリンクパターン
        company_link_pattern = r'/companies/.*?[\'"]'
        assert re.search(company_link_pattern, content), \
            "カテゴリ別レビュー一覧ページに企業ページへのリンクが見つかりません"

        # 「戻る」または企業名リンクの存在確認
        back_patterns = [
            r'戻る',
            r'企業ページ',
            r'class=[\'"]company.*?name[\'"]',
        ]

        found_back_link = any(re.search(pattern, content, re.IGNORECASE)
                             for pattern in back_patterns)
        assert found_back_link, "カテゴリ別レビュー一覧ページに戻るリンクまたは企業名リンクが見つかりません"

    def test_mobile_responsive_navigation_elements(self):
        """モバイルレスポンシブなナビゲーション要素が存在することを確認 - Task 9.3.6"""
        templates = [
            'templates/companies/detail.html',
            'templates/review_detail.html',
            'templates/category_review_list.html'
        ]

        for template_path in templates:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # モバイルレスポンシブ要素の確認
            responsive_patterns = [
                r'@media.*?(max-width|min-width).*?768px',
                r'class=[\'"].*?responsive.*?[\'"]',
                r'class=[\'"].*?mobile.*?[\'"]',
                r'class=[\'"].*?(col-|row-).*?[\'"]',  # Bootstrap grid
            ]

            found_responsive = any(re.search(pattern, content, re.IGNORECASE)
                                  for pattern in responsive_patterns)
            assert found_responsive, \
                f"{template_path} にモバイルレスポンシブ要素が見つかりません"

    def test_navigation_links_use_same_tab(self):
        """ナビゲーションリンクが同一タブで開くことを確認（target="_blank"がない） - Task 9.3.7"""
        templates = [
            ('templates/companies/detail.html', '企業詳細ページ'),
            ('templates/review_detail.html', 'レビュー詳細ページ'),
            ('templates/category_review_list.html', 'カテゴリ別レビュー一覧ページ'),
            ('templates/reviews/list.html', 'レビュー一覧ページ')
        ]

        for template_path, page_name in templates:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 内部リンク（/companies/, /reviews/）でtarget="_blank"を使っていないことを確認
            # 外部リンクは除外
            internal_links = re.findall(
                r'<a[^>]*href=[\'"]/(companies|reviews)/[^>]*>',
                content,
                re.IGNORECASE
            )

            for link in internal_links:
                assert 'target="_blank"' not in link.lower(), \
                    f"{page_name} の内部リンクで target='_blank' が使用されています: {link[:100]}"

    def test_breadcrumb_navigation_exists(self):
        """パンくずナビゲーションが存在することを確認 - Task 9.3.8"""
        templates_with_breadcrumbs = [
            ('templates/review_detail.html', 'レビュー詳細ページ'),
            ('templates/category_review_list.html', 'カテゴリ別レビュー一覧ページ')
        ]

        for template_path, page_name in templates_with_breadcrumbs:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # パンくずナビゲーションの存在確認
            breadcrumb_patterns = [
                r'breadcrumb',
                r'ホーム.*?企業一覧',
                r'nav.*?aria-label=[\'"]breadcrumb[\'"]',
            ]

            found_breadcrumb = any(re.search(pattern, content, re.IGNORECASE)
                                  for pattern in breadcrumb_patterns)
            assert found_breadcrumb, f"{page_name} にパンくずナビゲーションが見つかりません"

    def test_category_buttons_have_hover_effects(self):
        """カテゴリボタンがホバー効果を持つことを確認 - Task 9.3.9"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # ホバー効果の存在確認（CSS内またはstyle属性）
        hover_patterns = [
            r':hover',
            r'transition',
            r'opacity',
            r'transform',
            r'box-shadow',
        ]

        # カテゴリボタンセクション内でホバー効果が定義されているか確認
        category_section_match = re.search(
            r'category-reviews-section.*?</div>\s*</div>',
            content,
            re.DOTALL
        )

        if category_section_match:
            section_content = category_section_match.group(0)
            found_hover = any(re.search(pattern, section_content, re.IGNORECASE)
                            for pattern in hover_patterns)
            assert found_hover, "カテゴリボタンセクションにホバー効果が見つかりません"

    def test_all_category_links_are_consistent(self):
        """すべてのカテゴリリンクが一貫したURL形式を使用していることを確認 - Task 9.3.10"""
        templates = [
            'templates/companies/detail.html',
            'templates/reviews/list.html'
        ]

        expected_categories = [
            'recommendation',
            'foreign_support',
            'company_culture',
            'employee_relations',
            'evaluation_system',
            'promotion_treatment'
        ]

        for template_path in templates:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for category in expected_categories:
                # 正しいURL形式: /companies/{id}/reviews/by-category/{category}
                pattern = rf'/companies/\{{{{.*?\}}}}/reviews/by-category/{category}'
                assert re.search(pattern, content), \
                    f"{template_path} でカテゴリ {category} のURL形式が正しくありません"
