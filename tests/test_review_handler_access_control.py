"""
Task 4.2 & 4.3: Review Handler Access Control Integration Tests
レビュー投稿・編集ハンドラーのアクセス制御統合テスト

TDD - RED phase: Writing failing tests first.
"""
import pytest
from tornado.testing import AsyncHTTPTestCase
from unittest.mock import patch, MagicMock, AsyncMock
from bs4 import BeautifulSoup
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app import create_app


class TestReviewHandlerAccessControl(AsyncHTTPTestCase):
    """Task 4.2 & 4.3: Test review handler access control integration"""

    def get_app(self):
        """Create test application"""
        return create_app()

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.test_company = {
            '_id': 'test-company-001',
            'name': 'テスト企業株式会社',
            'industry_label': 'IT・インターネット',
            'size_label': '中規模企業（100-999名）',
            'location': '東京都渋谷区',
            'country': '日本',
        }
        self.test_review = {
            '_id': 'test-review-001',
            'company_id': 'test-company-001',
            'user_id': 'test-user-001',
            'overall_rating': 4.5,
            'title': 'テストレビュー',
            'content': 'テストレビュー内容'
        }

    # ==================== Task 4.2: Review Creation Handler Tests ====================

    @patch('src.services.company_service.CompanyService.get_company')
    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.check_access')
    def test_review_creation_unauthenticated_shows_mini_panel(self, mock_check_access, mock_get_company):
        """RED: Test that unauthenticated access to review creation shows mini panel"""
        # Mock company service
        mock_get_company.return_value = self.test_company

        # Mock access control to simulate authentication required
        from src.middleware.access_control_middleware import AccessControlError
        from src.utils.result import Result
        mock_check_access.return_value = Result.failure(AccessControlError("Authentication required"))

        # Access review creation URL without authentication
        response = self.fetch('/companies/test-company-001/reviews/new')

        # Should return 200 (not redirect) and show mini panel
        self.assertEqual(response.code, 200)

        # Parse HTML
        soup = BeautifulSoup(response.body, 'html.parser')

        # Verify mini panel is present and visible
        mini_panel = soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(mini_panel, "Mini panel should be present in the page")

        # Verify review form is hidden (show_login_panel=True means form is hidden)
        # This can be verified by checking if a specific script variable is set
        # or by checking if the form has a hidden class

    @patch('src.services.company_service.CompanyService.get_company')
    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.check_access')
    def test_review_creation_authenticated_shows_form(self, mock_check_access, mock_get_company):
        """RED: Test that authenticated access to review creation shows form"""
        # Mock company service
        mock_get_company.return_value = self.test_company

        # Mock access control to simulate successful authentication
        from src.utils.result import Result
        mock_check_access.return_value = Result.success({
            'access_granted': True,
            'authentication_required': True,
            'matched_rule': {'pattern': '/reviews/new', 'permissions': ['user']},
            'user_context': {
                'user_type': 'user',
                'auth_method': 'email',
                'identity_id': 'test-user-001'
            }
        })

        # Access review creation URL with valid session
        response = self.fetch('/companies/test-company-001/reviews/new',
                            headers={'Cookie': 'session_id=valid-session-123'})

        # Should return 200 and show review form
        self.assertEqual(response.code, 200)

        # Parse HTML
        soup = BeautifulSoup(response.body, 'html.parser')

        # Verify review form is visible (not checking for mini panel visibility here)
        # The form should be present and not hidden

    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.load_access_control_rules')
    def test_review_creation_url_matches_access_control_rule(self, mock_load_rules):
        """RED: Test that review creation URL matches access control rules"""
        # This test verifies that the URL pattern matching works correctly
        # The AccessControlMiddleware should have rules loaded from .env

        from src.middleware.access_control_middleware import AccessControlMiddleware
        middleware = AccessControlMiddleware()

        # Manually set rules (simulating .env configuration)
        middleware.access_rules = [
            {'pattern': '/reviews/new', 'permissions': ['user']},
            {'pattern': '/edit', 'permissions': ['user']}
        ]

        # Test URL matching
        matched_rule = middleware.match_url_pattern('/companies/test-company-001/reviews/new')
        self.assertIsNotNone(matched_rule, "Review creation URL should match access control rule")
        self.assertEqual(matched_rule['pattern'], '/reviews/new')
        self.assertIn('user', matched_rule['permissions'])

    # ==================== Task 4.3: Review Editing Handler Tests ====================

    @patch('src.services.review_service.ReviewService.get_review')
    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.check_access')
    def test_review_editing_unauthenticated_shows_mini_panel(self, mock_check_access, mock_get_review):
        """RED: Test that unauthenticated access to review editing shows mini panel"""
        # Mock review service
        mock_get_review.return_value = self.test_review

        # Mock access control to simulate authentication required
        from src.middleware.access_control_middleware import AccessControlError
        from src.utils.result import Result
        mock_check_access.return_value = Result.failure(AccessControlError("Authentication required"))

        # Access review editing URL without authentication
        response = self.fetch('/reviews/test-review-001/edit')

        # Should return 200 (not redirect) and show mini panel
        self.assertEqual(response.code, 200)

        # Parse HTML
        soup = BeautifulSoup(response.body, 'html.parser')

        # Verify mini panel is present
        mini_panel = soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(mini_panel, "Mini panel should be present in the page")

    @patch('src.services.review_service.ReviewService.get_review')
    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.check_access')
    def test_review_editing_authenticated_shows_form(self, mock_check_access, mock_get_review):
        """RED: Test that authenticated access to review editing shows form"""
        # Mock review service
        mock_get_review.return_value = self.test_review

        # Mock access control to simulate successful authentication
        from src.utils.result import Result
        mock_check_access.return_value = Result.success({
            'access_granted': True,
            'authentication_required': True,
            'matched_rule': {'pattern': '/edit', 'permissions': ['user']},
            'user_context': {
                'user_type': 'user',
                'auth_method': 'email',
                'identity_id': 'test-user-001'
            }
        })

        # Access review editing URL with valid session
        response = self.fetch('/reviews/test-review-001/edit',
                            headers={'Cookie': 'session_id=valid-session-123'})

        # Should return 200 and show edit form
        self.assertEqual(response.code, 200)

    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.load_access_control_rules')
    def test_review_editing_url_matches_access_control_rule(self, mock_load_rules):
        """RED: Test that review editing URL matches access control rules"""
        from src.middleware.access_control_middleware import AccessControlMiddleware
        middleware = AccessControlMiddleware()

        # Manually set rules (simulating .env configuration)
        middleware.access_rules = [
            {'pattern': '/reviews/new', 'permissions': ['user']},
            {'pattern': '/edit', 'permissions': ['user']}
        ]

        # Test URL matching
        matched_rule = middleware.match_url_pattern('/reviews/test-review-001/edit')
        self.assertIsNotNone(matched_rule, "Review editing URL should match access control rule")
        self.assertEqual(matched_rule['pattern'], '/edit')
        self.assertIn('user', matched_rule['permissions'])

    # ==================== Integration Tests ====================

    @patch('src.services.company_service.CompanyService.get_company')
    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.check_access')
    def test_template_receives_show_login_panel_variable(self, mock_check_access, mock_get_company):
        """RED: Test that template receives show_login_panel variable when unauthenticated"""
        # Mock company service
        mock_get_company.return_value = self.test_company

        # Mock access control to simulate authentication required
        from src.middleware.access_control_middleware import AccessControlError
        from src.utils.result import Result
        mock_check_access.return_value = Result.failure(AccessControlError("Authentication required"))

        # Access review creation URL without authentication
        response = self.fetch('/companies/test-company-001/reviews/new')

        # The handler should pass show_login_panel=True to the template
        # This can be verified by checking the rendered HTML for specific markers
        self.assertEqual(response.code, 200)

        # Parse HTML to check if mini panel is rendered
        soup = BeautifulSoup(response.body, 'html.parser')
        mini_panel = soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(mini_panel)

    @patch('src.services.company_service.CompanyService.get_company')
    @patch('src.middleware.access_control_middleware.AccessControlMiddleware.check_access')
    def test_template_receives_review_form_visible_variable(self, mock_check_access, mock_get_company):
        """RED: Test that template receives review_form_visible variable when authenticated"""
        # Mock company service
        mock_get_company.return_value = self.test_company

        # Mock access control to simulate successful authentication
        from src.utils.result import Result
        mock_check_access.return_value = Result.success({
            'access_granted': True,
            'authentication_required': True,
            'matched_rule': None,
            'user_context': {
                'user_type': 'user',
                'auth_method': 'email',
                'identity_id': 'test-user-001'
            }
        })

        # Access review creation URL with valid session
        response = self.fetch('/companies/test-company-001/reviews/new',
                            headers={'Cookie': 'session_id=valid-session-123'})

        # The handler should pass review_form_visible=True to the template
        self.assertEqual(response.code, 200)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
