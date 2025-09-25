"""
Task 5.3: Review Submission Navigation Tests
レビュー投稿画面への遷移機能実装のテスト

Tests for navigation to review creation screen and proper error handling.
"""

import unittest
from unittest.mock import patch, MagicMock
from tornado.testing import AsyncHTTPTestCase
from tornado.web import HTTPError
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class ReviewSubmissionNavigationTest(AsyncHTTPTestCase):
    """Task 5.3: レビュー投稿画面への遷移機能のテスト"""

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        self.test_company_id = 'test-company-001'

    def test_review_creation_url_exists(self):
        """RED: レビュー作成URLのルーティングが存在するかテスト"""
        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new',
                            follow_redirects=False)

        # 404以外のレスポンスが返ることを期待（404の場合は実装が必要）
        # このテストは実装前なので失敗することが期待される
        self.assertNotEqual(response.code, 404,
                           "レビュー作成URLのルーティングが実装されていません")

    def test_review_creation_with_company_id_parameter(self):
        """RED: レビュー作成画面で企業IDパラメータが正しく渡されるかテスト"""
        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new')

        if response.code == 200:
            # レスポンスボディに企業IDが含まれていることを確認
            response_body = response.body.decode('utf-8')
            self.assertIn(self.test_company_id, response_body,
                         "レビュー作成画面に企業IDが含まれていません")

    def test_invalid_company_id_error_handling(self):
        """RED: 無効な企業IDでのエラーハンドリングテスト"""
        invalid_company_id = 'non-existent-company'
        response = self.fetch(f'/companies/{invalid_company_id}/reviews/new')

        # 404エラーまたは適切なエラーハンドリングが期待される
        self.assertIn(response.code, [404, 400, 422],
                     f"無効な企業IDに対して適切なエラーが返されていません。レスポンスコード: {response.code}")

    def test_review_creation_form_elements(self):
        """RED: レビュー作成フォームの基本要素が存在するかテスト"""
        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new')

        if response.code == 200:
            response_body = response.body.decode('utf-8')

            # フォーム要素の存在確認
            form_elements = [
                'overall_rating',
                'work_environment',
                'compensation',
                'growth_opportunity',
                'work_life_balance',
                'management_quality',
                'job_satisfaction',
                'recommendation',
                'comment'
            ]

            for element in form_elements:
                self.assertIn(element, response_body,
                             f"レビューフォームに{element}フィールドが見つかりません")

    def test_review_submission_post_handling(self):
        """RED: レビュー投稿のPOSTリクエスト処理テスト"""
        review_data = {
            'overall_rating': '4.5',
            'work_environment': '4.0',
            'compensation': '4.5',
            'growth_opportunity': '3.8',
            'work_life_balance': '4.2',
            'management_quality': '4.0',
            'job_satisfaction': '4.3',
            'recommendation': '4.1',
            'comment': 'とても良い職場でした。成長機会が多くあります。'
        }

        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new',
                            method='POST',
                            body=self._encode_form_data(review_data),
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        # 正常処理（200, 201, 302など）またはバリデーションエラー（422）が期待される
        self.assertIn(response.code, [200, 201, 302, 422],
                     f"レビュー投稿POSTリクエストに対する適切な応答が返されていません。レスポンスコード: {response.code}")

    def test_review_submission_success_redirect(self):
        """RED: レビュー投稿成功時のリダイレクト処理テスト"""
        review_data = {
            'overall_rating': '4.0',
            'comment': 'テストレビューです。'
        }

        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new',
                            method='POST',
                            body=self._encode_form_data(review_data),
                            headers={'Content-Type': 'application/x-www-form-urlencoded'},
                            follow_redirects=False)

        # 投稿成功時は企業詳細ページにリダイレクトされることを期待
        if response.code == 302:
            location = response.headers.get('Location', '')
            expected_redirect = f'/companies/{self.test_company_id}'
            self.assertIn(expected_redirect, location,
                         f"投稿成功時のリダイレクト先が正しくありません。期待値: {expected_redirect}, 実際: {location}")

    def test_authentication_required_for_review_creation(self):
        """RED: レビュー作成に認証が必要かどうかのテスト"""
        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new')

        # 認証が必要な場合は401または302（ログイン画面へリダイレクト）が期待される
        # 認証が不要な場合は200が返される
        valid_responses = [200, 302, 401]
        self.assertIn(response.code, valid_responses,
                     f"レビュー作成画面のアクセス制御が適切ではありません。レスポンスコード: {response.code}")

    def test_review_creation_error_handling(self):
        """RED: レビュー作成時のエラーハンドリングテスト"""
        # 不正なデータでPOSTリクエスト
        invalid_data = {
            'overall_rating': 'invalid',  # 不正な評価値
            'comment': ''  # 空のコメント
        }

        response = self.fetch(f'/companies/{self.test_company_id}/reviews/new',
                            method='POST',
                            body=self._encode_form_data(invalid_data),
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        # バリデーションエラーまたは適切なエラーレスポンスが期待される
        self.assertIn(response.code, [400, 422],
                     f"不正データに対する適切なエラーが返されていません。レスポンスコード: {response.code}")

    def _encode_form_data(self, data):
        """フォームデータをURL エンコード形式に変換"""
        import urllib.parse
        return urllib.parse.urlencode(data).encode('utf-8')


if __name__ == '__main__':
    unittest.main()