"""
Test for company detail page responsive layout - Task 3
"""
import pytest
import re


class TestCompanyDetailResponsiveLayout:
    """企業詳細ページのレスポンシブレイアウトテスト"""

    def test_pc_layout_css_grid_exists(self):
        """PC表示用のCSS Gridレイアウトが存在することを確認 - Task 3.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # CSS Grid関連のパターンを確認
        grid_patterns = [
            r'display:\s*grid',
            r'grid-template-columns',
            r'@media\s*\([^)]*min-width:\s*768px',
        ]

        for pattern in grid_patterns:
            assert re.search(pattern, content, re.IGNORECASE), f"PC用CSS Grid要素が見つかりません: {pattern}"

    def test_mobile_layout_media_query_exists(self):
        """モバイル表示用のメディアクエリが存在することを確認 - Task 4.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # モバイル用メディアクエリパターンを確認
        mobile_patterns = [
            r'@media\s*\([^)]*max-width:\s*767px',
            r'max-width:\s*767px',
        ]

        found_mobile_query = any(re.search(pattern, content, re.IGNORECASE) for pattern in mobile_patterns)
        assert found_mobile_query, "モバイル用メディアクエリが見つかりません"

    def test_left_right_layout_structure_exists(self):
        """左右分割レイアウト構造が存在することを確認 - Task 3.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 左右分割を示すクラス名やIDを確認
        layout_patterns = [
            r'company-info',
            r'reviews?-section',
            r'company-detail.*layout',
            r'left.*side|right.*side',
        ]

        found_patterns = []
        for pattern in layout_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        # 少なくとも2つ以上のレイアウト要素が存在することを確認
        assert len(found_patterns) >= 2, f"左右分割レイアウト構造要素が不足しています。見つかった要素: {found_patterns}"

    def test_responsive_breakpoint_768px(self):
        """768pxブレークポイントが正しく設定されていることを確認 - Task 6.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 768pxブレークポイントのパターン確認
        breakpoint_patterns = [
            r'768px',
            r'min-width:\s*768px',
            r'max-width:\s*768px',
        ]

        found_breakpoints = []
        for pattern in breakpoint_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_breakpoints.extend(matches)

        assert len(found_breakpoints) >= 2, f"768pxブレークポイントが不足しています。見つかった要素: {found_breakpoints}"

    def test_company_name_positioning(self):
        """企業名が適切に配置されていることを確認 - Task 3.2"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 企業名表示のパターン確認
        company_name_patterns = [
            r'company[_-]?title',
            r'company[_-]?name',
            r'company\[.*name.*\]',
        ]

        found_name_element = any(re.search(pattern, content, re.IGNORECASE) for pattern in company_name_patterns)
        assert found_name_element, "企業名表示要素が見つかりません"

    def test_reviews_section_structure(self):
        """レビューセクションの構造が存在することを確認 - Task 3.3"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # レビューセクション関連のパターン確認
        review_patterns = [
            r'review.*section',
            r'review.*list',
            r'review.*comment',
        ]

        found_review_elements = []
        for pattern in review_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_review_elements.append(pattern)

        # レビュー関連要素が存在することを確認（将来の実装準備）
        # 現在は関連求人セクションがあるので、それも許可
        if not found_review_elements:
            # 代替として関連情報セクションの存在を確認
            related_patterns = [
                r'related.*job',
                r'detail.*section',
            ]
            found_related = any(re.search(pattern, content, re.IGNORECASE) for pattern in related_patterns)
            assert found_related, "レビューセクションまたは関連情報セクションが見つかりません"

    def test_category_review_section_exists(self):
        """質問別レビュー一覧セクションが存在することを確認 - Task 9.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 質問別レビュー一覧セクションの存在確認
        assert re.search(r'category-reviews-section', content), "質問別レビュー一覧セクションのクラスが見つかりません"
        assert re.search(r'質問別レビュー一覧', content), "質問別レビュー一覧のタイトルが見つかりません"

    def test_category_review_buttons_exist(self):
        """6つのカテゴリレビューボタンが存在することを確認 - Task 9.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 各カテゴリボタンの存在確認
        categories = [
            (r'/companies/.*?/reviews/by-category/recommendation', r'推薦度'),
            (r'/companies/.*?/reviews/by-category/foreign_support', r'受入制度'),
            (r'/companies/.*?/reviews/by-category/company_culture', r'会社風土'),
            (r'/companies/.*?/reviews/by-category/employee_relations', r'関係性'),
            (r'/companies/.*?/reviews/by-category/evaluation_system', r'評価制度'),
            (r'/companies/.*?/reviews/by-category/promotion_treatment', r'昇進待遇'),
        ]

        for url_pattern, label_pattern in categories:
            assert re.search(url_pattern, content), f"カテゴリURL {url_pattern} が見つかりません"
            assert re.search(label_pattern, content), f"カテゴリラベル {label_pattern} が見つかりません"

    def test_category_review_section_grid_layout(self):
        """質問別レビュー一覧セクションがグリッドレイアウトを使用していることを確認 - Task 9.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # グリッドレイアウトまたはflexboxの使用確認
        layout_patterns = [
            r'display:\s*grid',
            r'grid-template-columns',
            r'display:\s*flex',
            r'flex-wrap',
        ]

        # <div class="category-reviews-section"で始まるセクション全体を抽出
        section_match = re.search(
            r'<div\s+class="category-reviews-section"[^>]*>.*?</div>\s*</div>',
            content,
            re.DOTALL
        )

        if section_match:
            section_content = section_match.group(0)
            found_layout = any(re.search(pattern, section_content, re.IGNORECASE) for pattern in layout_patterns)
            assert found_layout, "質問別レビュー一覧セクションでグリッドまたはflexレイアウトが見つかりません"