"""
Test suite for Header Navigation Component
Tests the horizontal header navigation system replacing the old sidebar
"""

import pytest
from pathlib import Path
import re


class TestHeaderNavigationStructure:
    """Test header navigation HTML structure"""

    @pytest.fixture
    def base_html_content(self):
        """Load base.html content"""
        html_path = Path(__file__).parent.parent / "templates" / "base.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_js_content(self):
        """Load main.js content"""
        js_path = Path(__file__).parent.parent / "static" / "js" / "main.js"
        with open(js_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== HTML Structure Tests ==========

    def test_header_exists(self, base_html_content):
        """RED: Header navigation should exist in HTML"""
        # Check for header element
        assert "<header" in base_html_content or "class=\"header" in base_html_content, \
               "Header element must exist"

    def test_header_height_64px(self, main_css_content):
        """RED: Header should have height of 64px"""
        # Check for header height in CSS
        header_pattern = r'header\s*\{[^}]*height:\s*64px'
        assert re.search(header_pattern, main_css_content, re.DOTALL), \
               "Header should have height: 64px"

    def test_header_background_white(self, main_css_content):
        """RED: Header background should be white"""
        header_pattern = r'\.header\s*\{[^}]*(background|background-color):\s*(var\(--color-bg-card\)|#FFFFFF|#fff|white)'
        assert re.search(header_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Header should have white background (using var(--color-bg-card))"

    def test_header_sticky_position(self, main_css_content):
        """RED: Header should be sticky positioned"""
        header_pattern = r'header\s*\{[^}]*position:\s*sticky'
        assert re.search(header_pattern, main_css_content, re.DOTALL), \
               "Header should have position: sticky"

    def test_header_border_bottom(self, main_css_content):
        """RED: Header should have bottom border"""
        border_pattern = r'header\s*\{[^}]*border-bottom:\s*1px\s+solid'
        assert re.search(border_pattern, main_css_content, re.DOTALL), \
               "Header should have border-bottom"

    def test_header_contains_logo(self, base_html_content):
        """RED: Header should contain logo"""
        assert "logo" in base_html_content.lower(), \
               "Header must contain a logo element"

    def test_header_contains_nav_menu(self, base_html_content):
        """RED: Header should contain navigation menu items"""
        # Check for nav links
        nav_links = ["home", "review", "companies"]
        for link in nav_links:
            assert link in base_html_content.lower(), \
                   f"Header must contain {link} navigation link"

    def test_header_responsive_hamburger(self, main_css_content):
        """RED: Header should have hamburger menu for mobile"""
        assert "hamburger" in main_css_content.lower(), \
               "CSS should contain hamburger menu styles for mobile"

    def test_sidebar_removed_from_layout(self, base_html_content):
        """RED: Sidebar should be removed from main layout"""
        # The app-container should no longer use fixed sidebar layout
        # Check that sidebar is not in main app-container
        assert "class=\"sidebar\"" not in base_html_content or \
               "display: none" in base_html_content or \
               "display:none" in base_html_content, \
               "Sidebar should be removed or hidden from main layout"

    # ========== JavaScript Tests ==========

    def test_header_navigation_class_exists(self, main_js_content):
        """RED: HeaderNavigation JavaScript class should exist"""
        assert "HeaderNavigation" in main_js_content, \
               "HeaderNavigation class must be defined in main.js"

    def test_header_toggle_hamburger_method(self, main_js_content):
        """RED: HeaderNavigation should have toggleHamburger method"""
        assert "toggleHamburger" in main_js_content, \
               "HeaderNavigation must have toggleHamburger method"

    def test_header_responsive_handler_method(self, main_js_content):
        """RED: HeaderNavigation should handle responsive behavior"""
        assert "handleWindowResize" in main_js_content or \
               "handleMobileMenuClick" in main_js_content, \
               "HeaderNavigation must have responsive event handlers"

    def test_header_existing_functionality_preserved(self, main_js_content):
        """RED: Existing functions should still be available"""
        # Check that existing functions are still present
        assert "openLoginPanel" in main_js_content, \
               "openLoginPanel function must be preserved"
        assert "logout" in main_js_content, \
               "logout function must be preserved"

    # ========== Layout Tests ==========

    def test_main_content_full_width_after_header(self, main_css_content):
        """RED: Main content should use full width below header"""
        # Check that main-content is adjusted for new header layout
        main_content_pattern = r'\.main-content\s*\{[^}]*margin-left:\s*0|margin-top:\s*64px'
        # After refactor, should not have fixed left margin for sidebar
        assert re.search(main_content_pattern, main_css_content, re.DOTALL) or \
               "margin-left: 0" in main_css_content, \
               "Main content should adjust to full width after header implementation"

    def test_responsive_breakpoint_768px(self, main_css_content):
        """RED: Responsive design should handle 768px breakpoint"""
        assert "768px" in main_css_content, \
               "CSS should include 768px responsive breakpoint for header"

    def test_hamburger_menu_visible_mobile(self, main_css_content):
        """RED: Hamburger menu should be visible on mobile"""
        # Check for media query handling hamburger visibility
        assert "@media" in main_css_content, \
               "CSS should include media queries for mobile responsiveness"


class TestHeaderNavigation:
    """Integration tests for header navigation"""

    def test_header_navigation_consistency(self):
        """GREEN: Header navigation items should be consistent"""
        # This test will be implemented after header is created
        # Verify navigation structure is consistent across pages
        pass

    def test_header_accessibility(self):
        """GREEN: Header should meet accessibility standards"""
        # This test will be implemented after header is created
        # Verify aria labels, role attributes, etc.
        pass
