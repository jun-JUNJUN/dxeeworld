"""
UI Navigation Redesign - Mobile Detail Toggle Tests
テスト対象: Task 4.4 - モバイル用詳細情報トグル機能

Tests for mobile-specific detail toggle functionality in company detail pages.
"""

import unittest
from unittest.mock import patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
import sys
import os
from bs4 import BeautifulSoup

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class MobileDetailToggleTest(AsyncHTTPTestCase):
    """Task 4.4: モバイル用詳細情報トグル機能のテスト"""

    def get_app(self):
        """テスト用アプリケーションの作成"""
        return create_app()

    def setUp(self):
        super().setUp()
        # テスト用企業データ
        self.test_company = {
            'id': 'test-company-001',
            'name': 'テスト企業株式会社',
            'industry_label': 'IT・インターネット',
            'size_label': '中規模企業（100-999名）',
            'location': '東京都渋谷区',
            'country': '日本',
            'founded_year': 2010,
            'employee_count': 250,
            'description': 'テスト企業の説明文です。',
            'website': 'https://example.com',
            'source_files': ['test_data.csv'],
            'foreign_company_data': {
                'region': 'アジア',
                'country': '日本',
                'market_cap': '10億円'
            },
            'construction_data': None
        }

    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_detail_toggle_button_exists(self, mock_get_company):
        """RED: モバイル用詳細トグルボタンが存在するかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001',
                            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'})

        self.assertEqual(response.code, 200)
        soup = BeautifulSoup(response.body, 'html.parser')

        # モバイル用詳細トグルボタンの存在確認
        toggle_button = soup.find('button', class_='details-toggle')
        self.assertIsNotNone(toggle_button, "モバイル用詳細トグルボタンが見つかりません")

        # ボタンのテキスト確認
        self.assertIn('企業詳細情報を表示', toggle_button.get_text())
        self.assertIn('▼', toggle_button.get_text())

    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_detail_toggle_javascript_function(self, mock_get_company):
        """RED: JavaScript toggleCompanyDetails 関数が存在するかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        # JavaScript関数の存在確認
        response_body = response.body.decode('utf-8')
        self.assertIn('toggleCompanyDetails', response_body,
                     "toggleCompanyDetails JavaScript関数が見つかりません")
        self.assertIn('company-attributes', response_body,
                     "company-attributes要素のJavaScript操作が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_company_attributes_hidden_by_default_mobile(self, mock_get_company):
        """RED: モバイルでは企業属性が初期状態で非表示かテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)
        soup = BeautifulSoup(response.body, 'html.parser')

        # company-attributes要素の確認
        attributes_section = soup.find('div', id='company-attributes')
        self.assertIsNotNone(attributes_section, "company-attributes要素が見つかりません")

        # CSS確認: モバイル用のスタイルが定義されているか
        response_body = response.body.decode('utf-8')
        self.assertIn('.company-attributes', response_body, "company-attributesのCSS定義が見つかりません")
        self.assertIn('display: none', response_body, "初期非表示のCSS設定が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_toggle_button_visibility_responsive(self, mock_get_company):
        """RED: レスポンシブ表示制御のテスト（PC時は非表示、モバイル時は表示）"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # レスポンシブ表示制御のJavaScriptが存在することを確認
        self.assertIn('updateToggleButtonVisibility', response_body,
                     "updateToggleButtonVisibility関数が見つかりません")
        self.assertIn('window.innerWidth < 768', response_body,
                     "768pxブレークポイント判定が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_toggle_icon_state_management(self, mock_get_company):
        """RED: トグルアイコンの状態管理テスト（▼ ⇄ ▲）"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # アイコン切り替えロジックの確認
        self.assertIn('toggle-icon', response_body, "toggle-icon要素が見つかりません")
        self.assertIn('▼', response_body, "初期状態の▼アイコンが見つかりません")
        self.assertIn('▲', response_body, "展開状態の▲アイコンが見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_company_attributes_content_structure(self, mock_get_company):
        """RED: 企業属性コンテンツの構造テスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)
        soup = BeautifulSoup(response.body, 'html.parser')

        # 基本情報セクションの存在確認
        basic_info_section = soup.find('div', class_='detail-section')
        self.assertIsNotNone(basic_info_section, "基本情報セクションが見つかりません")

        # 基本情報の項目確認
        detail_labels = soup.find_all('div', class_='detail-label')
        expected_labels = ['企業名', '業界', '企業規模', '国', '所在地', '設立年', '従業員数']

        actual_labels = [label.get_text().strip() for label in detail_labels]
        for expected_label in expected_labels:
            self.assertIn(expected_label, actual_labels,
                         f"基本情報項目 '{expected_label}' が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_responsive_css_media_queries(self, mock_get_company):
        """RED: レスポンシブCSS Media Queriesのテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # メディアクエリの存在確認
        self.assertIn('@media (max-width: 767px)', response_body,
                     "モバイル用メディアクエリが見つかりません")
        self.assertIn('.company-attributes.expanded', response_body,
                     "expanded状態のCSS定義が見つかりません")


if __name__ == '__main__':
    unittest.main()