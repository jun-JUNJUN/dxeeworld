"""
Test for navigation menu cleanup - Task 2.1
"""
import pytest
import re


class TestNavigationMenuCleanup:
    """ナビゲーションメニュー整理テスト"""

    def test_forbidden_menu_items_not_present(self):
        """削除すべきメニュー項目が存在しないことを確認"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 削除すべき項目のパターンチェック
        forbidden_patterns = [
            (r'href="/jobs"', "求人情報"),
            (r'href="/talents"', "人材情報"),
        ]

        for pattern, description in forbidden_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, f"削除すべきナビゲーション項目が存在します: {description} (パターン: {pattern})"

    def test_required_menu_items_present(self):
        """必要なメニュー項目が存在することを確認"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 必須項目のパターンチェック
        required_patterns = [
            (r'href="/"', "ホーム"),
            (r'href="/companies"', "企業一覧"),
        ]

        for pattern, description in required_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) > 0, f"必須ナビゲーション項目が見つかりません: {description} (パターン: {pattern})"

    def test_navigation_includes_review_menu_item(self):
        """レビューページへのナビゲーション項目が存在することを確認 - Task 2.2"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # レビュー項目の確認
        review_pattern = r'href="/review"'
        matches = re.findall(review_pattern, content)
        assert len(matches) > 0, "レビューページへのナビゲーション項目が見つかりません (/review)"

    def test_specific_navigation_text_content(self):
        """ナビゲーション項目のテキスト内容を具体的に確認"""
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # ホームページリンクの確認
        home_pattern = r'<span class="nav-text">ホーム</span>'
        assert re.search(home_pattern, content), "ホームナビゲーションテキストが見つかりません"

        # 企業一覧ページリンクの確認
        companies_pattern = r'<span class="nav-text">企業一覧</span>'
        assert re.search(companies_pattern, content), "企業一覧ナビゲーションテキストが見つかりません"

        # 削除すべき項目のテキストが存在しないことを確認
        jobs_pattern = r'<span class="nav-text">求人情報</span>'
        talents_pattern = r'<span class="nav-text">人材情報</span>'

        assert not re.search(jobs_pattern, content), "削除すべき求人情報ナビゲーションテキストが存在します"
        assert not re.search(talents_pattern, content), "削除すべき人材情報ナビゲーションテキストが存在します"