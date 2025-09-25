"""
Task 6.1: Device Detection and Layout Switching Tests
デバイス検知とレイアウト自動切り替え機能実装のテスト

Tests for automatic PC/Mobile layout switching at 768px breakpoint.
"""

import unittest
from unittest.mock import patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
import sys
import os
from bs4 import BeautifulSoup
import re

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class ResponsiveLayoutSwitchingTest(AsyncHTTPTestCase):
    """Task 6.1: デバイス検知とレイアウト自動切り替え機能のテスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        from unittest.mock import MagicMock

        # オブジェクトライクなモックデータを作成
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

    @patch('src.services.company_service.CompanyService.get_company')
    def test_pc_layout_media_query_exists(self, mock_get_company):
        """RED: PC向けメディアクエリ（768px以上）が存在するかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # 768px以上のメディアクエリが存在することを確認
        pc_media_query_pattern = r'@media\s*\([^)]*min-width:\s*768px[^)]*\)'
        self.assertRegex(response_body, pc_media_query_pattern,
                        "PC向けメディアクエリ（min-width: 768px）が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_layout_media_query_exists(self, mock_get_company):
        """RED: モバイル向けメディアクエリ（768px未満）が存在するかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # 768px未満のメディアクエリが存在することを確認
        mobile_media_query_pattern = r'@media\s*\([^)]*max-width:\s*767px[^)]*\)'
        self.assertRegex(response_body, mobile_media_query_pattern,
                        "モバイル向けメディアクエリ（max-width: 767px）が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_grid_layout_pc_configuration(self, mock_get_company):
        """RED: PC環境でCSS Gridレイアウトが適用されるかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # PC向けGridレイアウトのCSS設定が存在することを確認
        grid_layout_patterns = [
            r'display:\s*grid',
            r'grid-template-columns',
            r'grid-gap|gap'
        ]

        for pattern in grid_layout_patterns:
            self.assertRegex(response_body, pattern,
                           f"CSS Gridレイアウトの設定 '{pattern}' が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_vertical_layout_configuration(self, mock_get_company):
        """RED: モバイル環境で縦方向レイアウトが適用されるかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # モバイル向け縦方向レイアウトのCSS設定確認
        mobile_layout_patterns = [
            r'flex-direction:\s*column',
            r'display:\s*block',
            r'width:\s*100%'
        ]

        has_mobile_layout = any(
            re.search(pattern, response_body, re.IGNORECASE)
            for pattern in mobile_layout_patterns
        )

        self.assertTrue(has_mobile_layout,
                       "モバイル向け縦方向レイアウトの設定が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_sidebar_visibility_responsive_behavior(self, mock_get_company):
        """RED: サイドバーのレスポンシブ表示制御が実装されているかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # サイドバー要素の存在確認
        sidebar = soup.find(['aside', 'nav'], class_=re.compile(r'sidebar|navigation'))
        self.assertIsNotNone(sidebar, "サイドバー要素が見つかりません")

        response_body = response.body.decode('utf-8')

        # サイドバーのレスポンシブ制御CSS確認
        sidebar_responsive_patterns = [
            r'@media\s*\([^)]*max-width:\s*767px[^)]*\)[\s\S]*?display:\s*none',
            r'sidebar[\s\S]*?@media[\s\S]*?display:\s*none'
        ]

        has_sidebar_control = any(
            re.search(pattern, response_body, re.IGNORECASE | re.MULTILINE)
            for pattern in sidebar_responsive_patterns
        )

        self.assertTrue(has_sidebar_control,
                       "サイドバーのレスポンシブ表示制御が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_bottom_tab_bar_mobile_visibility(self, mock_get_company):
        """RED: 下部タブバーのモバイル環境での表示制御テスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # 下部タブバー要素の存在確認
        tab_bar = soup.find(['nav', 'div'], class_=re.compile(r'tab-bar|bottom-nav|mobile-nav'))
        self.assertIsNotNone(tab_bar, "下部タブバー要素が見つかりません")

        response_body = response.body.decode('utf-8')

        # タブバーのモバイル表示制御CSS確認
        tab_bar_patterns = [
            r'position:\s*fixed',
            r'bottom:\s*0',
            r'@media\s*\([^)]*max-width:\s*767px[^)]*\)[\s\S]*?display:\s*(block|flex)'
        ]

        for pattern in tab_bar_patterns:
            self.assertRegex(response_body, pattern,
                           f"タブバーのモバイル表示制御 '{pattern}' が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_main_content_margin_adjustments(self, mock_get_company):
        """RED: メインコンテンツのマージン調整がレスポンシブに対応しているかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # メインコンテンツのマージン調整CSS確認
        margin_adjustment_patterns = [
            r'margin-left:\s*0',  # サイドバー分のマージン削除
            r'padding-bottom:\s*\d+px',  # タブバー分のパディング追加
            r'@media\s*\([^)]*max-width:\s*767px[^)]*\)[\s\S]*?margin'
        ]

        has_margin_adjustments = any(
            re.search(pattern, response_body, re.IGNORECASE)
            for pattern in margin_adjustment_patterns
        )

        self.assertTrue(has_margin_adjustments,
                       "メインコンテンツのマージン調整が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_breakpoint_consistency_across_styles(self, mock_get_company):
        """RED: 768pxブレークポイントの一貫性テスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # 768pxブレークポイントの一貫した使用を確認
        breakpoint_patterns = [
            r'768px',  # ブレークポイント値の存在
            r'min-width:\s*768px',  # PC向け
            r'max-width:\s*767px'   # モバイル向け
        ]

        breakpoint_matches = []
        for pattern in breakpoint_patterns:
            matches = re.findall(pattern, response_body, re.IGNORECASE)
            breakpoint_matches.extend(matches)

        # 少なくとも両方向のブレークポイントが存在することを確認
        self.assertGreaterEqual(len(breakpoint_matches), 2,
                               "768pxブレークポイントが十分に定義されていません")

    def test_viewport_meta_tag_exists(self):
        """RED: レスポンシブデザインに必要なviewportメタタグの存在確認"""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # viewportメタタグの存在確認
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        self.assertIsNotNone(viewport_meta, "viewportメタタグが見つかりません")

        # viewportの内容確認
        content = viewport_meta.get('content', '')
        required_viewport_settings = ['width=device-width', 'initial-scale=1']

        for setting in required_viewport_settings:
            self.assertIn(setting, content,
                         f"viewport設定に '{setting}' が含まれていません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_css_grid_fallback_support(self, mock_get_company):
        """RED: CSS Gridのフォールバック機能テスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # Grid未対応ブラウザ向けのフォールバックCSS確認
        fallback_patterns = [
            r'display:\s*flex',  # Flexboxフォールバック
            r'display:\s*block',  # ブロックレイアウトフォールバック
            r'float:\s*(left|right)'  # フロートレイアウトフォールバック
        ]

        has_fallback = any(
            re.search(pattern, response_body, re.IGNORECASE)
            for pattern in fallback_patterns
        )

        self.assertTrue(has_fallback,
                       "CSS Gridのフォールバック機能が見つかりません")


if __name__ == '__main__':
    unittest.main()