"""
Task 6.3: Performance Optimization Tests
パフォーマンス最適化と最終調整

Tests for rendering speed, loading times, and user experience optimization.
"""

import unittest
from unittest.mock import patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
import sys
import os
from bs4 import BeautifulSoup
import re
import time

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class PerformanceOptimizationTest(AsyncHTTPTestCase):
    """Task 6.3: パフォーマンス最適化と最終調整テスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        from unittest.mock import MagicMock

        # テスト用企業データ
        self.test_company = MagicMock()
        self.test_company.id = 'test-company-001'
        self.test_company.name = 'テスト企業株式会社'
        self.test_company.industry = MagicMock()
        self.test_company.industry.value = 'information_technology'
        self.test_company.size = MagicMock()
        self.test_company.size.value = 'medium'
        self.test_company.location = '東京都渋谷区'
        self.test_company.country = '日本'
        self.test_company.website_url = 'https://example.com'
        self.test_company.description = 'テスト企業の説明'
        self.test_company.employee_count = 500
        self.test_company.founded_year = 2010
        self.test_company.capital = 100000000

    def test_response_time_performance(self):
        """RED: レスポンス時間のパフォーマンステスト"""
        # 複数のページでレスポンス時間を測定
        test_urls = ['/', '/companies']

        for url in test_urls:
            with self.subTest(url=url):
                start_time = time.time()
                response = self.fetch(url)
                response_time = time.time() - start_time

                # レスポンス時間は2秒以下であることを期待
                self.assertLess(response_time, 2.0,
                               f"レスポンス時間が遅すぎます: {response_time:.2f}秒 for {url}")

                # HTTPステータスコードの確認
                self.assertEqual(response.code, 200, f"不正なレスポンスコード for {url}")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_css_minification_indicators(self, mock_get_company):
        """RED: CSS最適化指標のテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # CSS最適化の指標を確認
        css_optimization_indicators = {
            'inline_css_present': '<style>' in response_body,
            'css_compression_hints': len([line for line in response_body.split('\n')
                                        if line.strip() and '{' in line and '}' in line]),
            'redundant_whitespace': response_body.count('  ') / len(response_body) < 0.05,  # 5%未満の冗長な空白
            'css_rules_count': response_body.count('{')
        }

        # インラインCSSが存在し、ある程度最適化されていることを確認
        self.assertTrue(css_optimization_indicators['inline_css_present'],
                       "インラインCSSが見つかりません")

        self.assertGreater(css_optimization_indicators['css_rules_count'], 10,
                          "CSS規則が不足しています")

    def test_html_structure_optimization(self):
        """RED: HTML構造の最適化テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')
        response_body = response.body.decode('utf-8')

        # HTML構造の最適化指標
        optimization_indicators = {
            'semantic_elements': len(soup.find_all(['header', 'nav', 'main', 'section', 'article', 'aside', 'footer'])),
            'proper_heading_hierarchy': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])) > 0,
            'meta_viewport': soup.find('meta', {'name': 'viewport'}) is not None,
            'lang_attribute': soup.html.get('lang') is not None if soup.html else False,
            'document_size': len(response_body)
        }

        # セマンティックHTML要素の使用を確認
        self.assertGreater(optimization_indicators['semantic_elements'], 3,
                          f"セマンティック要素が不足しています: {optimization_indicators['semantic_elements']}")

        # 適切なヘッダー階層の確認
        self.assertTrue(optimization_indicators['proper_heading_hierarchy'],
                       "適切なヘッダー階層が設定されていません")

        # 基本的なメタタグの確認
        self.assertTrue(optimization_indicators['meta_viewport'],
                       "viewportメタタグが設定されていません")

        # ドキュメントサイズが合理的な範囲内であることを確認（100KB未満）
        self.assertLess(optimization_indicators['document_size'], 100000,
                       f"ドキュメントサイズが大きすぎます: {optimization_indicators['document_size']} bytes")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_responsive_layout_rendering_efficiency(self, mock_get_company):
        """RED: レスポンシブレイアウトレンダリング効率テスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # レスポンシブデザインの効率性指標
        responsive_efficiency = {
            'media_query_count': len(re.findall(r'@media[^{]*\{', response_body)),
            'css_grid_usage': 'display: grid' in response_body or 'display:grid' in response_body,
            'flexbox_usage': 'display: flex' in response_body or 'display:flex' in response_body,
            'mobile_first_approach': response_body.find('@media') < response_body.find('min-width') if '@media' in response_body else False,
            'redundant_media_queries': response_body.count('768px') < 10  # 過剰なブレークポイントの回避
        }

        # メディアクエリが効率的に使用されていることを確認
        self.assertGreater(responsive_efficiency['media_query_count'], 1,
                          "メディアクエリが不足しています")

        self.assertLess(responsive_efficiency['media_query_count'], 8,
                       f"メディアクエリが多すぎます: {responsive_efficiency['media_query_count']}")

        # 現代的なレイアウト手法の使用を確認
        modern_layout_usage = responsive_efficiency['css_grid_usage'] or responsive_efficiency['flexbox_usage']
        self.assertTrue(modern_layout_usage,
                       "CSS GridまたはFlexboxが使用されていません")

    def test_javascript_optimization_indicators(self):
        """RED: JavaScript最適化指標テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')
        response_body = response.body.decode('utf-8')

        # JavaScript最適化の指標
        js_optimization = {
            'inline_scripts': len(soup.find_all('script', string=True)),
            'external_scripts': len(soup.find_all('script', src=True)),
            'event_listeners_efficient': 'addEventListener' in response_body,
            'dom_ready_optimization': 'DOMContentLoaded' in response_body,
            'script_placement': True  # スクリプトが適切な位置にあるか
        }

        # インラインスクリプトとJavaScript機能の適切な使用を確認
        total_scripts = js_optimization['inline_scripts'] + js_optimization['external_scripts']

        # 適度なJavaScript使用（0-5個のスクリプト）
        self.assertLessEqual(total_scripts, 5,
                           f"JavaScriptファイルが多すぎます: {total_scripts}")

    def test_network_request_optimization(self):
        """RED: ネットワークリクエスト最適化テスト"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # ネットワークリクエスト最適化の指標
        network_optimization = {
            'external_stylesheets': len(soup.find_all('link', {'rel': 'stylesheet'})),
            'external_scripts': len(soup.find_all('script', src=True)),
            'inline_styles': len(soup.find_all('style')),
            'external_images': len(soup.find_all('img', src=True)),
            'preload_hints': len(soup.find_all('link', {'rel': 'preload'})),
            'dns_prefetch_hints': len(soup.find_all('link', {'rel': 'dns-prefetch'}))
        }

        # 外部リソースの数が合理的な範囲内であることを確認
        total_external_resources = (network_optimization['external_stylesheets'] +
                                   network_optimization['external_scripts'])

        self.assertLessEqual(total_external_resources, 8,
                           f"外部リソースが多すぎます: {total_external_resources}")

        # インラインスタイルの適切な使用を確認（CSS配信の最適化）
        self.assertGreater(network_optimization['inline_styles'], 0,
                          "レンダリングブロックを避けるためのインラインCSSが設定されていません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_content_optimization(self, mock_get_company):
        """RED: コンテンツ最適化テスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')
        response_body = response.body.decode('utf-8')

        # コンテンツ最適化の指標
        content_optimization = {
            'text_compression_ratio': len(response_body.replace(' ', '')) / len(response_body),
            'image_alt_attributes': len(soup.find_all('img', alt=True)),
            'heading_structure': len(soup.find_all(['h1', 'h2', 'h3'])),
            'list_usage': len(soup.find_all(['ul', 'ol'])),
            'table_usage': len(soup.find_all('table')),
            'redundant_content': response_body.count('同じ文字列') < 3  # 冗長なコンテンツの回避
        }

        # コンテンツの構造化が適切に行われていることを確認
        self.assertGreater(content_optimization['heading_structure'], 2,
                          f"ヘッダー構造が不十分です: {content_optimization['heading_structure']}")

        # テキスト圧縮率が適切であることを確認（空白の最適化）
        self.assertGreater(content_optimization['text_compression_ratio'], 0.8,
                          f"テキスト圧縮率が低すぎます: {content_optimization['text_compression_ratio']}")

    def test_mobile_performance_optimization(self):
        """RED: モバイルパフォーマンス最適化テスト"""
        # モバイルユーザーエージェントでアクセス
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}

        start_time = time.time()
        response = self.fetch('/', headers=headers)
        mobile_response_time = time.time() - start_time

        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')
        response_body = response.body.decode('utf-8')

        # モバイル最適化の指標
        mobile_optimization = {
            'viewport_meta': soup.find('meta', {'name': 'viewport'}) is not None,
            'touch_friendly_elements': 'min-height: 44px' in response_body or '44px' in response_body,
            'mobile_css': '@media' in response_body and '767px' in response_body,
            'response_time': mobile_response_time,
            'content_size': len(response_body)
        }

        # モバイル最適化の基本要件を確認
        self.assertTrue(mobile_optimization['viewport_meta'],
                       "viewportメタタグが設定されていません")

        self.assertTrue(mobile_optimization['mobile_css'],
                       "モバイル向けCSSが設定されていません")

        # モバイルでのレスポンス時間が許容範囲内であることを確認
        self.assertLess(mobile_optimization['response_time'], 3.0,
                       f"モバイルレスポンス時間が遅すぎます: {mobile_optimization['response_time']:.2f}秒")

    def test_caching_and_compression_indicators(self):
        """RED: キャッシングと圧縮の指標テスト"""
        response = self.fetch('/')

        # HTTPヘッダーの確認
        headers = dict(response.headers)

        # キャッシングと圧縮の指標
        caching_indicators = {
            'content_type_set': 'Content-Type' in headers,
            'content_length_reasonable': int(headers.get('Content-Length', 0)) < 100000,  # 100KB未満
            'response_structure': response.code == 200,
            'header_count': len(headers)
        }

        # 基本的なHTTPヘッダーが適切に設定されていることを確認
        self.assertTrue(caching_indicators['content_type_set'],
                       "Content-Typeヘッダーが設定されていません")

        self.assertTrue(caching_indicators['content_length_reasonable'],
                       f"コンテンツサイズが大きすぎます: {headers.get('Content-Length', 'N/A')}")

        # レスポンス構造が正常であることを確認
        self.assertTrue(caching_indicators['response_structure'],
                       "レスポンス構造に問題があります")

    def test_user_experience_optimization_metrics(self):
        """RED: ユーザビリティとユーザーエクスペリエンス最適化メトリクス"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')
        response_body = response.body.decode('utf-8')

        # UX最適化の指標
        ux_optimization = {
            'navigation_clarity': len(soup.find_all(['nav', 'a'])) > 3,
            'visual_hierarchy': len(soup.find_all(['h1', 'h2', 'h3'])) > 2,
            'interactive_elements': len(soup.find_all(['button', 'a', 'input'])) > 0,
            'loading_indicators': 'loading' in response_body.lower() or 'spinner' in response_body.lower(),
            'error_handling': 'error' in response_body.lower() or '404' in response_body,
            'accessibility_features': len(soup.find_all(attrs={'aria-label': True})) > 0
        }

        # ユーザビリティの基本要件を確認
        self.assertTrue(ux_optimization['navigation_clarity'],
                       "ナビゲーション要素が不足しています")

        self.assertTrue(ux_optimization['visual_hierarchy'],
                       "視覚的階層が不適切です")

        self.assertTrue(ux_optimization['interactive_elements'],
                       "インタラクティブ要素が不足しています")

        # アクセシビリティ機能の確認
        self.assertTrue(ux_optimization['accessibility_features'],
                       "アクセシビリティ機能が不足しています")


if __name__ == '__main__':
    unittest.main()