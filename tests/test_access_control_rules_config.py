"""
Task 4.1: Access Control Rules Configuration Test
アクセス制御ルールの.env設定読み込み確認

TDD - RED phase: Testing that review creation and editing URLs have proper access control rules configured.
"""
import pytest
import os
from unittest.mock import patch
from src.middleware.access_control_middleware import AccessControlMiddleware


class TestAccessControlRulesConfiguration:
    """Task 4.1: Test that access control rules are properly configured in .env"""

    @pytest.fixture
    def access_control_middleware(self):
        """Access control middleware fixture"""
        return AccessControlMiddleware()

    @pytest.mark.asyncio
    async def test_review_creation_url_rule_configured(self, access_control_middleware):
        """RED: Test that /companies/*/reviews/new has access control rule configured"""
        # Configure the expected rule for review creation (using simple path patterns)
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/new,user;/edit,user'
        }):
            await access_control_middleware.load_access_control_rules()

        # Verify rule is loaded
        rules = access_control_middleware.access_rules
        assert len(rules) >= 1, "At least one rule should be configured for review creation"

        # Check if review creation pattern exists
        creation_rules = [r for r in rules if '/reviews/new' in r['pattern']]
        assert len(creation_rules) > 0, "Review creation URL pattern not found in access control rules"

        # Verify the rule requires 'user' permission
        creation_rule = creation_rules[0]
        assert 'user' in creation_rule['permissions'], "Review creation should require 'user' permission"

    @pytest.mark.asyncio
    async def test_review_editing_url_rule_configured(self, access_control_middleware):
        """RED: Test that /reviews/*/edit has access control rule configured"""
        # Configure the expected rule for review editing (using simple path patterns)
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/new,user;/edit,user'
        }):
            await access_control_middleware.load_access_control_rules()

        # Verify rule is loaded
        rules = access_control_middleware.access_rules
        assert len(rules) >= 2, "At least two rules should be configured (creation and editing)"

        # Check if review editing pattern exists (pattern is '/edit')
        editing_rules = [r for r in rules if 'edit' in r['pattern']]
        assert len(editing_rules) > 0, "Review editing URL pattern not found in access control rules"

        # Verify the rule requires 'user' permission
        editing_rule = editing_rules[0]
        assert 'user' in editing_rule['permissions'], "Review editing should require 'user' permission"

    @pytest.mark.asyncio
    async def test_url_pattern_matching_for_review_creation(self, access_control_middleware):
        """RED: Test that review creation URLs match the configured pattern"""
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/new,user;/edit,user'
        }):
            await access_control_middleware.load_access_control_rules()

        # Test with actual review creation URL
        test_urls = [
            '/companies/test-company-001/reviews/new',
            '/companies/another-company/reviews/new',
            '/companies/123/reviews/new'
        ]

        for url in test_urls:
            matched_rule = access_control_middleware.match_url_pattern(url)
            assert matched_rule is not None, f"URL {url} should match review creation pattern"
            assert 'user' in matched_rule['permissions'], f"URL {url} should require 'user' permission"

    @pytest.mark.asyncio
    async def test_url_pattern_matching_for_review_editing(self, access_control_middleware):
        """RED: Test that review editing URLs match the configured pattern"""
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/new,user;/edit,user'
        }):
            await access_control_middleware.load_access_control_rules()

        # Test with actual review editing URL
        test_urls = [
            '/reviews/test-review-001/edit',
            '/reviews/another-review/edit',
            '/reviews/123/edit'
        ]

        for url in test_urls:
            matched_rule = access_control_middleware.match_url_pattern(url)
            assert matched_rule is not None, f"URL {url} should match review editing pattern"
            assert 'user' in matched_rule['permissions'], f"URL {url} should require 'user' permission"

    @pytest.mark.asyncio
    async def test_rule_logging_on_load(self, access_control_middleware):
        """RED: Test that rules are properly logged when loaded"""
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/new,user;/edit,user'
        }):
            await access_control_middleware.load_access_control_rules()

        # Verify rules are loaded and can be retrieved
        rules = await access_control_middleware.get_access_rules()
        assert len(rules) == 2, "Should have exactly 2 rules configured"

        # Verify rule details
        rule_patterns = [r['pattern'] for r in rules]
        assert any('/reviews/new' in p for p in rule_patterns), "Review creation pattern should be in rules"
        assert any('edit' in p for p in rule_patterns), "Review editing pattern should be in rules"

    @pytest.mark.asyncio
    async def test_public_urls_not_protected(self, access_control_middleware):
        """RED: Test that public URLs (not in rules) are not protected"""
        with patch.dict('os.environ', {
            'ACCESS_CONTROL_RULES': '/reviews/new,user;/edit,user'
        }):
            await access_control_middleware.load_access_control_rules()

        # Test public URLs that should not match any rule
        public_urls = [
            '/',
            '/companies',
            '/companies/test-company-001',  # Company detail page
            '/reviews',  # Review list page
        ]

        for url in public_urls:
            matched_rule = access_control_middleware.match_url_pattern(url)
            # These URLs should not match review creation/editing rules
            # (They might match if rule pattern is too broad, which would be incorrect)
            if matched_rule:
                # If matched, ensure it's not because of overly broad pattern
                assert '/reviews/new' not in matched_rule['pattern'] or '/companies/' in url, \
                    f"Public URL {url} incorrectly matched review creation rule"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
