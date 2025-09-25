"""
Task 6.2: UI Navigation Integration Tests
全機能統合テストと品質検証

Comprehensive integration tests for navigation, company listings, and responsive design.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from tornado.testing import AsyncHTTPTestCase
import sys
import os
from bs4 import BeautifulSoup
import re

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class UINavigationIntegrationTest(AsyncHTTPTestCase):
    """Task 6.2: UI Navigation統合テストと品質検証"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        from unittest.mock import MagicMock

        # テスト用企業データ
        self.test_companies = []
        for i in range(3):
            company = MagicMock()
            company.id = f'test-company-00{i+1}'
            company.name = f'テスト企業{i+1}株式会社'
            company.industry = MagicMock()
            company.industry.value = 'information_technology'
            company.size = MagicMock()
            company.size.value = 'medium'
            company.location = '東京都渋谷区'
            company.country = '日本'
            company.website_url = 'https://example.com'
            company.description = f'テスト企業{i+1}の説明'
            company.employee_count = 500 + i * 100
            company.founded_year = 2010 + i
            company.capital = 100000000 + i * 50000000
            self.test_companies.append(company)

        # 企業一覧用のページネーションデータ
        self.pagination_data = {
            'page': 1,
            'total': 3,
            'pages': 1,
            'has_prev': False,
            'has_next': False,
            'prev_num': None,
            'next_num': None
        }

    def test_complete_navigation_flow(self):
        """RED: ホーム→企業一覧→企業詳細の完全なユーザーフロー検証"""
        # 1. ホームページアクセス
        home_response = self.fetch('/')
        self.assertEqual(home_response.code, 200)

        home_soup = BeautifulSoup(home_response.body, 'html.parser')

        # ナビゲーションリンクの確認
        nav_links = home_soup.find_all('a', href=re.compile(r'/companies'))
        self.assertGreater(len(nav_links), 0, "企業一覧へのナビゲーションリンクが見つかりません")

        # 2. 企業一覧ページアクセス
        companies_response = self.fetch('/companies')
        self.assertEqual(companies_response.code, 200)

        companies_soup = BeautifulSoup(companies_response.body, 'html.parser')

        # 企業一覧の基本構造確認
        self.assertIsNotNone(companies_soup.find('h1'), "企業一覧ページにh1タグが存在しません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_company_detail_responsive_behavior(self, mock_get_company):
        """RED: 企業詳細ページのレスポンシブ動作の包括的テスト"""
        mock_get_company.return_value = self.test_companies[0]

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')
        response_body = response.body.decode('utf-8')

        # PC・モバイル両対応のレスポンシブ要素確認
        responsive_elements = [
            r'@media\s*\([^)]*min-width:\s*768px[^)]*\)',  # PC用メディアクエリ
            r'@media\s*\([^)]*max-width:\s*767px[^)]*\)',  # モバイル用メディアクエリ
            r'display:\s*grid',  # Gridレイアウト
            r'mobile-tab-bar'  # モバイルタブバー
        ]

        for pattern in responsive_elements:
            self.assertRegex(response_body, pattern,
                           f"レスポンシブ要素 '{pattern}' が見つかりません")

        # 企業情報の表示確認
        company_name = soup.find(string=re.compile(r'テスト企業1株式会社'))
        self.assertIsNotNone(company_name, "企業名が表示されていません")

    def test_navigation_consistency_across_pages(self):
        """RED: 全ページでのナビゲーション一貫性テスト"""
        # テストするページリスト
        test_pages = ['/', '/companies', '/reviews']

        navigation_elements = {}

        for page_url in test_pages:
            response = self.fetch(page_url)

            # 404以外のレスポンスを受け入れる（一部のページは未実装の可能性）
            if response.code == 404:
                continue

            soup = BeautifulSoup(response.body, 'html.parser')

            # ナビゲーション要素の収集
            nav_elements = soup.find_all(['nav', 'a'], href=True)
            nav_hrefs = [elem.get('href') for elem in nav_elements if elem.get('href')]

            navigation_elements[page_url] = nav_hrefs

        # 少なくとも2つのページで共通のナビゲーション要素があることを確認
        if len(navigation_elements) >= 2:
            common_nav_found = False
            pages = list(navigation_elements.keys())

            for i in range(len(pages)):
                for j in range(i + 1, len(pages)):
                    common_links = set(navigation_elements[pages[i]]) & set(navigation_elements[pages[j]])
                    if common_links:
                        common_nav_found = True
                        break
                if common_nav_found:
                    break

            self.assertTrue(common_nav_found, "ページ間でのナビゲーション一貫性が確保されていません")

    @patch('src.services.company_service.CompanyService.search_companies')
    def test_search_and_filtering_functionality(self, mock_search):
        """RED: 検索・フィルタリング機能の統合テスト"""
        # モック検索結果の設定
        mock_search.return_value = {
            'companies': self.test_companies[:2],  # 2件のみ返す
            'pagination': {
                'page': 1,
                'total': 2,
                'pages': 1,
                'has_prev': False,
                'has_next': False
            }
        }

        # 検索パラメータ付きでアクセス
        search_params = 'name=テスト&industry=information_technology&location=東京'
        response = self.fetch(f'/companies?{search_params}')

        self.assertEqual(response.code, 200)

        # 検索結果の表示確認
        soup = BeautifulSoup(response.body, 'html.parser')

        # 検索フォームの存在確認
        search_form = soup.find('form') or soup.find('input', {'type': 'search'})
        self.assertIsNotNone(search_form, "検索フォームが見つかりません")

    def test_error_handling_and_user_feedback(self):
        """RED: エラーハンドリングとユーザーフィードバックテスト"""
        # 存在しない企業IDでアクセス
        response = self.fetch('/companies/non-existent-company')

        # 404エラーまたは適切なエラーハンドリング
        self.assertIn(response.code, [404, 500],
                     f"存在しない企業に対して適切なエラーレスポンスが返されていません: {response.code}")

        if response.code == 404:
            # 404ページの内容確認
            soup = BeautifulSoup(response.body, 'html.parser')
            self.assertIsNotNone(soup.find(string=re.compile(r'見つかりません|Not Found', re.IGNORECASE)),
                               "404エラーページに適切なエラーメッセージがありません")

    def test_mobile_tab_navigation_functionality(self):
        """RED: モバイルタブナビゲーションの機能性テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # モバイルタブバーの存在確認
        mobile_tab_bar = soup.find(class_=re.compile(r'mobile-tab-bar|tab-bar'))
        self.assertIsNotNone(mobile_tab_bar, "モバイルタブバーが見つかりません")

        # タブアイテムの確認
        tab_links = mobile_tab_bar.find_all('a') if mobile_tab_bar else []
        self.assertGreaterEqual(len(tab_links), 3, "タブバーに十分なナビゲーションリンクがありません")

        # 各タブのhref属性確認
        expected_hrefs = ['/', '/companies', '/review']
        actual_hrefs = [link.get('href') for link in tab_links]

        for expected_href in expected_hrefs:
            self.assertIn(expected_href, actual_hrefs,
                         f"期待されるナビゲーション '{expected_href}' が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_system_integration(self, mock_get_company):
        """RED: レビューシステム統合の動作テスト"""
        mock_get_company.return_value = self.test_companies[0]

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー関連要素の確認
        review_elements = [
            soup.find(class_=re.compile(r'review')),  # レビュー関連クラス
            soup.find('a', href=re.compile(r'/reviews/new')),  # レビュー投稿リンク
            soup.find(string=re.compile(r'レビュー|Review', re.IGNORECASE))  # レビュー関連テキスト
        ]

        review_elements_found = sum(1 for elem in review_elements if elem is not None)
        self.assertGreater(review_elements_found, 0, "レビューシステムの統合要素が見つかりません")

    def test_cross_browser_compatibility_indicators(self):
        """RED: クロスブラウザ互換性の指標テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # 互換性を示すCSS機能の確認
        compatibility_features = [
            r'-webkit-',  # WebKit接頭辞
            r'-moz-',     # Mozilla接頭辞
            r'display:\s*flex',  # Flexboxサポート
            r'display:\s*grid',  # CSS Gridサポート
            r'@media',    # メディアクエリサポート
        ]

        compatibility_score = 0
        for feature in compatibility_features:
            if re.search(feature, response_body, re.IGNORECASE):
                compatibility_score += 1

        self.assertGreaterEqual(compatibility_score, 2,
                               f"クロスブラウザ互換性の指標が不足しています: {compatibility_score}/5")

    def test_accessibility_compliance_basic(self):
        """RED: 基本的なアクセシビリティ準拠テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # アクセシビリティ要素の確認
        accessibility_elements = {
            'alt_attributes': len(soup.find_all('img', alt=True)),
            'aria_labels': len(soup.find_all(attrs={'aria-label': True})),
            'semantic_headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'form_labels': len(soup.find_all('label'))
        }

        # 少なくとも2つのアクセシビリティ機能が存在することを確認
        accessibility_score = sum(1 for count in accessibility_elements.values() if count > 0)
        self.assertGreaterEqual(accessibility_score, 2,
                               f"アクセシビリティ要素が不足しています: {accessibility_elements}")

    def test_performance_optimization_indicators(self):
        """RED: パフォーマンス最適化指標テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')
        soup = BeautifulSoup(response.body, 'html.parser')

        # パフォーマンス最適化の指標
        optimization_indicators = {
            'minified_css': len(re.findall(r'<style[^>]*>.*?</style>', response_body, re.DOTALL)),
            'external_css': len(soup.find_all('link', {'rel': 'stylesheet'})),
            'meta_viewport': len(soup.find_all('meta', {'name': 'viewport'})),
            'compressed_structure': len(response_body) < 50000  # 50KB未満
        }

        # パフォーマンス指標のスコア計算
        performance_score = sum(1 for indicator, value in optimization_indicators.items()
                              if (isinstance(value, bool) and value) or (isinstance(value, int) and value > 0))

        self.assertGreaterEqual(performance_score, 2,
                               f"パフォーマンス最適化指標が不足しています: {optimization_indicators}")


if __name__ == '__main__':
    unittest.main()