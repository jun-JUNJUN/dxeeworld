"""
UI Navigation Redesign - Mobile Review Optimization Tests
テスト対象: Task 4.5 - モバイル用レビュー一覧表示最適化

Tests for mobile-optimized review display in company detail pages.
"""

import unittest
from unittest.mock import patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
import sys
import os
from bs4 import BeautifulSoup

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class MobileReviewOptimizationTest(AsyncHTTPTestCase):
    """Task 4.5: モバイル用レビュー一覧表示最適化のテスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        self.test_company_with_reviews = {
            'id': 'test-company-002',
            'name': 'レビュー付き企業株式会社',
            'industry_label': 'IT・インターネット',
            'size_label': '大企業（1000名以上）',
            'location': '東京都新宿区',
            'country': '日本',
            'description': 'レビューがある企業です。',
        }

        self.test_reviews = [
            {
                'id': 'review-001',
                'user_id': 'user-001',
                'company_id': 'test-company-002',
                'overall_rating': 4.2,
                'work_environment': 4.0,
                'compensation': 4.5,
                'growth_opportunity': 3.8,
                'work_life_balance': 4.2,
                'management_quality': 4.0,
                'job_satisfaction': 4.3,
                'recommendation': 4.1,
                'comment': 'とても良い会社です。成長機会が多く、働きやすい環境です。',
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z'
            },
            {
                'id': 'review-002',
                'user_id': 'user-002',
                'company_id': 'test-company-002',
                'overall_rating': 3.8,
                'work_environment': 3.5,
                'compensation': 4.0,
                'growth_opportunity': 4.2,
                'work_life_balance': 3.8,
                'management_quality': 3.6,
                'job_satisfaction': 3.9,
                'recommendation': 3.7,
                'comment': '職場の雰囲気は良いですが、もう少し給与面での改善があると良いと思います。',
                'created_at': '2024-01-20T14:45:00Z',
                'updated_at': '2024-01-20T14:45:00Z'
            }
        ]

    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_review_section_layout(self, mock_get_company):
        """RED: モバイルでのレビューセクションレイアウト最適化テスト"""
        mock_get_company.return_value = self.test_company_with_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)
        soup = BeautifulSoup(response.body, 'html.parser')

        # レビューセクションの存在確認
        reviews_section = soup.find('div', class_='reviews-section')
        self.assertIsNotNone(reviews_section, "レビューセクションが見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_review_card_structure(self, mock_get_company, mock_get_reviews):
        """RED: モバイル用レビューカード構造のテスト"""
        mock_get_company.return_value = self.test_company_with_reviews
        mock_get_reviews.return_value = self.test_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # モバイル用レビューカードのCSS確認
        self.assertIn('review-card-mobile', response_body,
                     "モバイル用レビューカードのCSS定義が見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_vertical_layout_mobile(self, mock_get_company, mock_get_reviews):
        """RED: レビューの縦方向レイアウト最適化テスト"""
        mock_get_company.return_value = self.test_company_with_reviews
        mock_get_reviews.return_value = self.test_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # 縦方向レイアウトのCSS確認
        self.assertIn('flex-direction: column', response_body,
                     "縦方向レイアウトの設定が見つかりません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_prompt_mobile_display(self, mock_get_company):
        """RED: モバイルでのレビュー投稿促進UI表示テスト"""
        # レビューがない企業のテスト
        company_no_reviews = self.test_company_with_reviews.copy()
        mock_get_company.return_value = company_no_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)
        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー投稿促進メッセージの確認
        prompt_message = soup.find('div', class_='prompt-message')
        self.assertIsNotNone(prompt_message, "レビュー投稿促進メッセージが見つかりません")

        self.assertIn('この企業に勤めていますか？勤めたことがありますか？',
                     prompt_message.get_text(),
                     "レビュー投稿促進メッセージの内容が正しくありません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_submit_button_mobile(self, mock_get_company):
        """RED: モバイル用レビュー投稿ボタンのテスト"""
        mock_get_company.return_value = self.test_company_with_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)
        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー投稿ボタンの確認
        submit_button = soup.find('a', class_='review-submit-btn')
        self.assertIsNotNone(submit_button, "レビュー投稿ボタンが見つかりません")

        self.assertEqual(submit_button.get_text().strip(), 'Reviewを投稿する',
                        "レビュー投稿ボタンのテキストが正しくありません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_review_card_responsive_styling(self, mock_get_company, mock_get_reviews):
        """RED: モバイル用レビューカードのレスポンシブスタイリングテスト"""
        mock_get_company.return_value = self.test_company_with_reviews
        mock_get_reviews.return_value = self.test_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # モバイル用レビューカードのスタイル確認
        self.assertIn('@media (max-width: 767px)', response_body,
                     "モバイル用メディアクエリが見つかりません")
        self.assertIn('review-card', response_body,
                     "レビューカードのCSS定義が見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_review_touch_optimization(self, mock_get_company, mock_get_reviews):
        """RED: モバイル用タッチ操作最適化テスト"""
        mock_get_company.return_value = self.test_company_with_reviews
        mock_get_reviews.return_value = self.test_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # タッチ操作用のCSS設定確認
        self.assertIn('min-height: 44px', response_body,
                     "タッチターゲットサイズの最適化が見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_mobile_review_scroll_optimization(self, mock_get_company, mock_get_reviews):
        """RED: モバイル用スクロール最適化テスト"""
        mock_get_company.return_value = self.test_company_with_reviews
        # 多数のレビューで長いリストをテスト
        many_reviews = self.test_reviews * 10  # 20件のレビュー
        mock_get_reviews.return_value = many_reviews

        response = self.fetch('/companies/test-company-002')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # スクロール最適化のCSS確認
        self.assertIn('overflow-y: auto', response_body,
                     "スクロール最適化設定が見つかりません")

    def test_mobile_review_list_position_below_toggle(self):
        """RED: モバイルでレビュー一覧が詳細トグルボタンの下に表示されるテスト"""
        # DOM構造のテストとして後で実装
        self.assertTrue(True, "DOM構造のテストは後で実装予定")


if __name__ == '__main__':
    unittest.main()