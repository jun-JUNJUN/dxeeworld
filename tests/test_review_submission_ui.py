"""
Task 5.2: Review Submission UI Tests
レビュー投稿促進UI実装のテスト

Tests for review submission promotion UI when companies have no reviews.
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


class ReviewSubmissionUITest(AsyncHTTPTestCase):
    """Task 5.2: レビュー投稿促進UI実装のテスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        self.test_company = {
            'id': 'test-company-001',
            'name': 'レビューなし企業株式会社',
            'industry_label': 'IT・インターネット',
            'size_label': '中規模企業（100-999名）',
            'location': '東京都渋谷区',
            'country': '日本',
        }

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_prompt_message_display(self, mock_get_company, mock_get_reviews):
        """RED: レビュー投稿促進メッセージが正しく表示されるかテスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []  # レビューなし

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー投稿促進メッセージの確認
        prompt_message = soup.find('div', class_='prompt-message')
        self.assertIsNotNone(prompt_message, "レビュー投稿促進メッセージが見つかりません")

        expected_message = "この企業に勤めていますか？勤めたことがありますか？"
        self.assertIn(expected_message, prompt_message.get_text(),
                      f"促進メッセージが正しくありません。期待値: '{expected_message}'")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_submit_button_display(self, mock_get_company, mock_get_reviews):
        """RED: レビュー投稿ボタンが正しく表示されるかテスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        # レビュー投稿ボタンの確認
        submit_button = soup.find('a', class_='review-submit-btn')
        self.assertIsNotNone(submit_button, "レビュー投稿ボタンが見つかりません")

        # ボタンテキストの確認
        expected_text = "Reviewを投稿する"
        self.assertEqual(submit_button.get_text().strip(), expected_text,
                        f"ボタンテキストが正しくありません。期待値: '{expected_text}'")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_submit_button_url(self, mock_get_company, mock_get_reviews):
        """RED: レビュー投稿ボタンのリンク先が正しく設定されているかテスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        submit_button = soup.find('a', class_='review-submit-btn')
        self.assertIsNotNone(submit_button, "レビュー投稿ボタンが見つかりません")

        # リンク先の確認
        expected_url = "/companies/test-company-001/reviews/new"
        actual_url = submit_button.get('href')
        self.assertEqual(actual_url, expected_url,
                        f"リンク先が正しくありません。期待値: '{expected_url}', 実際: '{actual_url}'")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_pc_mobile_consistent_ui_display(self, mock_get_company, mock_get_reviews):
        """RED: PC・モバイル両環境で一貫したUI表示テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []

        # PC環境での表示確認
        response_pc = self.fetch('/companies/test-company-001',
                                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

        # モバイル環境での表示確認
        response_mobile = self.fetch('/companies/test-company-001',
                                   headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'})

        self.assertEqual(response_pc.code, 200)
        self.assertEqual(response_mobile.code, 200)

        # PC・モバイル共通でレビュー投稿UIが表示されることを確認
        for response in [response_pc, response_mobile]:
            soup = BeautifulSoup(response.body, 'html.parser')

            prompt_section = soup.find('div', class_='review-prompt-section')
            self.assertIsNotNone(prompt_section, "レビュー投稿促進セクションが見つかりません")

            submit_button = soup.find('a', class_='review-submit-btn')
            self.assertIsNotNone(submit_button, "レビュー投稿ボタンが見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_review_prompt_section_styling(self, mock_get_company, mock_get_reviews):
        """RED: レビュー投稿促進セクションのスタイリング確認テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        response_body = response.body.decode('utf-8')

        # レビュー投稿促進セクションのCSSクラスが存在することを確認
        self.assertIn('review-prompt-section', response_body,
                     "review-prompt-sectionクラスが見つかりません")
        self.assertIn('prompt-message', response_body,
                     "prompt-messageクラスが見つかりません")
        self.assertIn('review-submit-btn', response_body,
                     "review-submit-btnクラスが見つかりません")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_no_reviews_condition_ui_display(self, mock_get_company, mock_get_reviews):
        """RED: レビューがない条件でのUI表示確認テスト"""
        mock_get_company.return_value = self.test_company

        # 様々なレビューなし状態をテスト
        test_cases = [
            [],  # 空のリスト
            None,  # Noneの場合
        ]

        for review_data in test_cases:
            with self.subTest(review_data=review_data):
                mock_get_reviews.return_value = review_data

                response = self.fetch('/companies/test-company-001')
                self.assertEqual(response.code, 200)

                soup = BeautifulSoup(response.body, 'html.parser')

                # レビュー投稿促進UIが表示されることを確認
                prompt_section = soup.find('div', class_='review-prompt-section')
                self.assertIsNotNone(prompt_section,
                                   f"レビューデータ {review_data} でレビュー投稿促進UIが表示されていません")

                # レビュー一覧は表示されないことを確認
                reviews_list = soup.find('div', class_='reviews-list-mobile')
                self.assertIsNone(reviews_list,
                                f"レビューデータ {review_data} でレビュー一覧が表示されています")

    @patch('src.services.review_submission_service.ReviewSubmissionService.get_company_reviews')
    @patch('src.services.company_service.CompanyService.get_company')
    def test_button_accessibility_attributes(self, mock_get_company, mock_get_reviews):
        """RED: レビュー投稿ボタンのアクセシビリティ属性テスト"""
        mock_get_company.return_value = self.test_company
        mock_get_reviews.return_value = []

        response = self.fetch('/companies/test-company-001')
        self.assertEqual(response.code, 200)

        soup = BeautifulSoup(response.body, 'html.parser')

        submit_button = soup.find('a', class_='review-submit-btn')
        self.assertIsNotNone(submit_button, "レビュー投稿ボタンが見つかりません")

        # アクセシビリティ属性の確認
        aria_label = submit_button.get('aria-label')
        title = submit_button.get('title')

        # aria-labelまたはtitleが設定されていることを確認
        self.assertTrue(aria_label or title,
                       "レビュー投稿ボタンにアクセシビリティ属性が設定されていません")


if __name__ == '__main__':
    unittest.main()