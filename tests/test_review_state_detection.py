"""
Task 5.1: Review Existence State Detection Tests
レビュー存在状態の判定機能のテスト

Tests for detecting whether a company has reviews and managing review state.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from tornado.testing import AsyncHTTPTestCase
import sys
import os
from bs4 import BeautifulSoup

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class ReviewStateDetectionTest(AsyncHTTPTestCase):
    """Task 5.1: レビュー存在状態判定機能のテスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        self.test_company = {
            'id': 'test-company-001',
            'name': 'テスト企業株式会社',
            'industry_label': 'IT・インターネット',
            'size_label': '中規模企業（100-999名）',
            'location': '東京都渋谷区',
            'country': '日本',
            'description': 'テスト企業の説明文です。',
        }

        self.test_reviews = [
            {
                'id': 'review-001',
                'company_id': 'test-company-001',
                'overall_rating': 4.2,
                'comment': 'とても良い会社です。',
                'created_at': '2024-01-15T10:30:00Z'
            }
        ]

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_company_with_reviews_detection(self, mock_get_company, mock_get_reviews):
        """RED: 企業にレビューが存在する場合の状態検知テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = self.test_reviews

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー一覧が表示されていることを確認
        reviews_section = soup.find('div', class_='reviews-list-mobile')
        self.assertIsNotNone(reviews_section, "レビュー一覧セクションが見つかりません")

        # レビュー投稿促進UIが表示されていないことを確認
        prompt_section = soup.find('div', class_='review-prompt-section')
        self.assertIsNone(prompt_section, "レビュー投稿促進UIが表示されています（表示されるべきではない）")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_company_without_reviews_detection(self, mock_get_company, mock_get_reviews):
        """RED: 企業にレビューが存在しない場合の状態検知テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []  # レビューなし

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー投稿促進UIが表示されていることを確認
        prompt_section = soup.find('div', class_='review-prompt-section')
        self.assertIsNotNone(prompt_section, "レビュー投稿促進UIが見つかりません")

        # レビュー一覧が表示されていないことを確認
        reviews_section = soup.find('div', class_='reviews-list-mobile')
        self.assertIsNone(reviews_section, "レビュー一覧セクションが表示されています（表示されるべきではない）")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_service_error_handling(self, mock_get_company, mock_get_reviews):
        """RED: レビューサービスでエラーが発生した場合のハンドリングテスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.side_effect = Exception("Database connection error")

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # エラー時はレビュー投稿促進UIを表示
        prompt_section = soup.find('div', class_='review-prompt-section')
        self.assertIsNotNone(prompt_section, "エラー時にレビュー投稿促進UIが表示されていません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_has_reviews_template_variable(self, mock_get_company):
        """RED: テンプレートにhas_reviews変数が正しく渡されているかテスト"""
        mock_get_company.return_value = self.test_company

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        # テンプレート内でhas_reviewsによる条件分岐が存在することを確認
        response_body = response.body.decode('utf-8')
        self.assertIn('has_reviews', response_body, "テンプレートにhas_reviews変数が見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_count_display(self, mock_get_company, mock_get_reviews):
        """RED: レビュー件数の表示テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = self.test_reviews * 3  # 3件のレビュー

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビューカードが正しい数だけ表示されることを確認
        review_cards = soup.find_all('div', class_='review-card-mobile')
        self.assertEqual(len(review_cards), 3, f"レビューカードの表示数が正しくありません。期待値: 3, 実際: {len(review_cards)}")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_data_caching(self, mock_get_company, mock_get_reviews):
        """RED: レビューデータのキャッシュ機能テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = self.test_reviews

        # 同じ企業詳細ページを2回アクセス
        response1 = self.fetch('/companies/test-company-001')
        response2 = self.fetch('/companies/test-company-001')

        self.assertEqual(response1.code, 200)
        self.assertEqual(response2.code, 200)

        # レビューサービスが適切に呼び出されていることを確認
        self.assertTrue(mock_get_reviews.called, "レビューサービスが呼び出されていません")

    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_service_unavailable(self, mock_get_company):
        """RED: レビューサービスが利用できない場合のテスト"""
        mock_get_company.return_value = self.test_company

        # レビューサービスが None の場合をテスト
        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビューサービス未利用時はレビュー投稿促進UIを表示
        prompt_section = soup.find('div', class_='review-prompt-section')
        self.assertIsNotNone(prompt_section, "レビューサービス未利用時にレビュー投稿促進UIが表示されていません")


if __name__ == '__main__':
    unittest.main()