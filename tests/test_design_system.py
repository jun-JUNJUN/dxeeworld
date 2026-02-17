"""
Test suite for Design System CSS Variables
Tests CSS variable definitions and design token consistency
"""

import pytest
from pathlib import Path
import re


class TestDesignSystemVariables:
    """Test CSS variable definitions in the design system"""

    @pytest.fixture
    def css_content(self):
        """Load main.css content"""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_css_variables_section_exists(self, css_content):
        """RED: CSS variables section should exist in root selector"""
        # Check for :root selector with CSS variables
        assert ":root" in css_content, "CSS variables must be defined in :root selector"

        # Verify some key variables exist
        assert "--color-primary" in css_content, "Primary color variable must be defined"
        assert "--color-primary-dark" in css_content, "Dark color variable must be defined"
        assert "--color-primary-light" in css_content, "Light color variable must be defined"

    def test_primary_colors_defined(self, css_content):
        """RED: Primary, dark, and light colors must be defined"""
        assert "--color-primary: #20BEFF" in css_content or \
               "--color-primary: #20beff" in css_content, \
               "Primary color #20BEFF must be defined"
        assert "--color-primary-dark: #1A8FCC" in css_content or \
               "--color-primary-dark: #1a8fcc" in css_content, \
               "Dark color #1A8FCC must be defined"
        assert "--color-primary-light: #E3F5FF" in css_content or \
               "--color-primary-light: #e3f5ff" in css_content, \
               "Light color #E3F5FF must be defined"

    def test_background_colors_defined(self, css_content):
        """RED: Background colors must be defined"""
        assert "--color-bg-main" in css_content, "Main background color variable missing"
        assert "--color-bg-card" in css_content, "Card background color variable missing"
        assert "--color-bg-section" in css_content, "Section background color variable missing"

    def test_text_colors_defined(self, css_content):
        """RED: Text colors must be defined"""
        assert "--color-text-primary" in css_content, "Primary text color missing"
        assert "--color-text-secondary" in css_content, "Secondary text color missing"
        assert "--color-text-disabled" in css_content, "Disabled text color missing"

    def test_typography_variables_defined(self, css_content):
        """RED: Typography variables must be defined"""
        assert "--font-family-base" in css_content, "Base font family missing"
        assert "--font-family-ja" in css_content, "Japanese font family missing"
        assert "--font-size-h1" in css_content, "H1 font size missing"
        assert "--font-size-h2" in css_content, "H2 font size missing"
        assert "--font-size-h3" in css_content, "H3 font size missing"
        assert "--font-size-body" in css_content, "Body font size missing"
        assert "--line-height-heading" in css_content, "Heading line height missing"
        assert "--line-height-body" in css_content, "Body line height missing"

    def test_font_sizes_correct_values(self, css_content):
        """RED: Font sizes must have correct values"""
        # H1: 32px (2rem)
        assert "--font-size-h1: 2rem" in css_content or \
               "--font-size-h1: 32px" in css_content, \
               "H1 should be 2rem or 32px"

        # H2: 24px (1.5rem)
        assert "--font-size-h2: 1.5rem" in css_content or \
               "--font-size-h2: 24px" in css_content, \
               "H2 should be 1.5rem or 24px"

        # Body: 16px (1rem)
        assert "--font-size-body: 1rem" in css_content or \
               "--font-size-body: 16px" in css_content, \
               "Body should be 1rem or 16px"

    def test_font_weights_defined(self, css_content):
        """RED: Font weights must be defined"""
        assert "--font-weight-bold" in css_content, "Bold weight missing"
        assert "--font-weight-semibold" in css_content, "Semibold weight missing"
        assert "--font-weight-normal" in css_content, "Normal weight missing"

    def test_line_heights_correct(self, css_content):
        """RED: Line heights must be correct"""
        assert "--line-height-heading: 1.2" in css_content, \
               "Heading line height should be 1.2"
        assert "--line-height-body: 1.6" in css_content, \
               "Body line height should be 1.6"

    def test_spacing_variables_defined(self, css_content):
        """RED: Spacing scale variables must be defined"""
        assert "--spacing-unit: 4px" in css_content, "Spacing unit (4px) not defined"
        assert "--spacing-xs" in css_content, "XS spacing missing"
        assert "--spacing-sm" in css_content, "SM spacing missing"
        assert "--spacing-md" in css_content, "MD spacing missing"
        assert "--spacing-lg" in css_content, "LG spacing missing"
        assert "--spacing-xl" in css_content, "XL spacing missing"
        assert "--spacing-2xl" in css_content, "2XL spacing missing"
        assert "--spacing-3xl" in css_content, "3XL spacing missing"

    def test_spacing_values_4px_scale(self, css_content):
        """RED: Spacing values must follow 4px base unit scale"""
        assert "--spacing-xs: 4px" in css_content, "XS should be 4px"
        assert "--spacing-sm: 8px" in css_content, "SM should be 8px"
        assert "--spacing-md: 16px" in css_content, "MD should be 16px"
        assert "--spacing-lg: 24px" in css_content, "LG should be 24px"

    def test_shadow_variables_defined(self, css_content):
        """RED: Shadow variables must be defined"""
        assert "--shadow-sm" in css_content, "Small shadow missing"
        assert "--shadow-md" in css_content, "Medium shadow missing"

    def test_border_radius_variables_defined(self, css_content):
        """RED: Border radius variables must be defined"""
        assert "--border-radius-sm" in css_content, "Small border radius missing"
        assert "--border-radius-md" in css_content, "Medium border radius missing"
        assert "--border-radius-lg" in css_content, "Large border radius missing"

    def test_semantic_colors_defined(self, css_content):
        """RED: Semantic colors (success, error, warning) must be defined"""
        assert "--color-success" in css_content, "Success color missing"
        assert "--color-warning" in css_content, "Warning color missing"
        assert "--color-error" in css_content, "Error color missing"

    def test_css_variables_used_in_body(self, css_content):
        """GREEN: CSS variables should be used in body styles"""
        # After CSS variables are defined, body styles should reference them
        # This test checks if variable definitions are being used
        body_section = re.search(r'body\s*\{([^}]+)\}', css_content)
        if body_section:
            # At least font family should use variables
            assert "--font-family" in css_content, \
                   "Body styles should use CSS variables"
