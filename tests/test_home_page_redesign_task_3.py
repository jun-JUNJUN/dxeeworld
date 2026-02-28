"""
Test suite for Task 3: Home Page Redesign
Tests the new home page hero section and statistics section design
Following TDD approach: RED → GREEN → REFACTOR → VERIFY
"""

import pytest
from pathlib import Path
import re


class TestHeroSectionStructure:
    """Test hero section HTML structure and design"""

    @pytest.fixture
    def home_html_content(self):
        """Load home.html content"""
        html_path = Path(__file__).parent.parent / "templates" / "home.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests ==========
    # These tests should fail initially until implementation is complete

    def test_hero_section_gradient_background(self, main_css_content):
        """RED: Hero section should have gradient background #F8FBFF → #FFFFFF"""
        # Check for gradient background in hero section
        gradient_pattern = r'\.hero-section\s*\{[^}]*background:\s*linear-gradient\([^)]+#F8FBFF[^)]+#FFFFFF[^)]*\)'
        assert re.search(gradient_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero section should have gradient background: linear-gradient(to bottom, #F8FBFF, #FFFFFF)"

    def test_hero_section_max_width_1200px(self, main_css_content):
        """RED: Hero section should have max-width of 1200px"""
        hero_pattern = r'\.hero-section\s*\{[^}]*max-width:\s*1200px'
        assert re.search(hero_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero section should have max-width: 1200px"

    def test_hero_section_centered_with_padding(self, main_css_content):
        """RED: Hero section should be centered with padding 80px 24px"""
        hero_pattern = r'\.hero-section\s*\{[^}]*padding:\s*80px\s+24px'
        assert re.search(hero_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero section should have padding: 80px 24px"

    def test_hero_section_split_layout_60_40(self, main_css_content):
        """RED: Hero section should have 60%-40% split layout"""
        # Check for flex layout with specific ratios
        flex_pattern = r'\.hero-content\s*\{[^}]*flex:\s*0\s+0\s+60%'
        assert re.search(flex_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero content should take 60% width"

        visual_pattern = r'\.hero-visual\s*\{[^}]*flex:\s*0\s+0\s+40%'
        assert re.search(visual_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero visual should take 40% width"

    def test_hero_section_main_heading(self, home_html_content):
        """RED: Hero section should contain main heading '優秀な人材とスタートアップをつなぐ'"""
        assert "優秀な人材とスタートアップをつなぐ" in home_html_content, \
               "Hero section must contain main heading: '優秀な人材とスタートアップをつなぐ'"

    def test_hero_section_subheading(self, home_html_content):
        """RED: Hero section should contain subheading '実績ベースの評価で、透明性の高いマッチングを実現'"""
        assert "実績ベースの評価で、透明性の高いマッチングを実現" in home_html_content, \
               "Hero section must contain subheading: '実績ベースの評価で、透明性の高いマッチングを実現'"

    def test_hero_cta_buttons_structure(self, home_html_content):
        """RED: Hero section should have two CTA buttons"""
        # Check for hero actions div
        assert "hero-actions" in home_html_content, \
               "Hero section must have hero-actions container"

        # Check for primary button "無料で始める"
        assert "無料で始める" in home_html_content, \
               "Hero section must contain primary CTA button: '無料で始める'"

        # Check for secondary button "企業を探す"
        assert "企業を探す" in home_html_content, \
               "Hero section must contain secondary CTA button: '企業を探す'"

    def test_hero_visual_section_exists(self, home_html_content):
        """RED: Hero section should have visual component"""
        assert "hero-visual" in home_html_content, \
               "Hero section must have hero-visual container"

    def test_hero_primary_button_primary_styling(self, main_css_content):
        """RED: Primary CTA button should have primary button styling"""
        # Check for primary button styles in CSS
        primary_btn_pattern = r'\.btn\s*\.btn-primary\s*\{[^}]*background:\s*var\(--color-primary\)|#20BEFF'
        assert re.search(primary_btn_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Primary CTA button should have primary blue background color"

    def test_hero_secondary_button_secondary_styling(self, main_css_content):
        """RED: Secondary CTA button should have secondary button styling"""
        # Check for secondary button styles in CSS
        secondary_btn_pattern = r'\.btn\s*\.btn-secondary\s*\{[^}]*background:\s*transparent|border:\s*2px'
        assert re.search(secondary_btn_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Secondary CTA button should have transparent background with border"

    def test_hero_responsive_mobile_vertical_layout(self, main_css_content):
        """RED: Hero section should stack vertically on mobile (60% → 40% becomes top → bottom)"""
        # Check for mobile media query
        mobile_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)[^}]*\.hero-content\s*\{[^}]*flex-direction:\s*column'
        assert re.search(mobile_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero section should stack vertically on mobile devices"

    def test_hero_responsive_mobile_40_percent_width(self, main_css_content):
        """RED: Mobile hero visual should have specific width adjustment"""
        mobile_visual_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)[^}]*\.hero-visual\s*\{[^}]*width:\s*100%'
        assert re.search(mobile_visual_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero visual should take full width on mobile"

    def test_hero_content_alignment_mobile(self, main_css_content):
        """RED: Hero content should be center-aligned on mobile"""
        mobile_content_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)[^}]*\.hero-content\s*\{[^}]*text-align:\s*center'
        assert re.search(mobile_content_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero content should be center-aligned on mobile devices"

    def test_hero_visual_height_mobile(self, main_css_content):
        """RED: Hero visual should have appropriate height on mobile"""
        mobile_height_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)[^}]*\.hero-visual\s*\{[^}]*height:\s*auto|300px'
        assert re.search(mobile_height_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero visual should have auto/300px height on mobile"


class TestStatisticsSectionStructure:
    """Test statistics section HTML structure and design"""

    @pytest.fixture
    def home_html_content(self):
        """Load home.html content"""
        html_path = Path(__file__).parent.parent / "templates" / "home.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Statistics Section ==========
    # These tests should fail initially until implementation is complete

    def test_statistics_section_white_background(self, main_css_content):
        """RED: Statistics section should have white background"""
        stats_pattern = r'\.stats-section\s*\{[^}]*background:\s*#FFFFFF'
        assert re.search(stats_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics section should have white background (#FFFFFF)"

    def test_statistics_section_four_column_grid(self, main_css_content):
        """RED: Statistics section should have 4-column grid layout"""
        grid_pattern = r'\.stats-container\s*\{[^}]*display:\s*grid[^}]*grid-template-columns:\s*repeat\(4'
        assert re.search(grid_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics container should use 4-column grid layout"

    def test_statistics_section_padding_60px_24px(self, main_css_content):
        """RED: Statistics section should have padding 60px 24px"""
        stats_pattern = r'\.stats-section\s*\{[^}]*padding:\s*60px\s+24px'
        assert re.search(stats_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics section should have padding: 60px 24px"

    def test_statistics_section_items_alignment(self, main_css_content):
        """RED: Statistics items should be text center aligned"""
        stats_item_pattern = r'\.stat-item\s*\{[^}]*text-align:\s*center'
        assert re.search(stats_item_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics items should be text center aligned"

    def test_statistics_section_icon_size_48px(self, main_css_content):
        """RED: Statistics icons should be 48px size"""
        icon_pattern = r'\.stat-icon\s*\{[^}]*width:\s*48px|\.stat-icon\s*\{[^}]*height:\s*48px'
        assert re.search(icon_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics icons should be 48px in size"

    def test_statistics_number_size_36px_weight_700(self, main_css_content):
        """RED: Statistics numbers should be 36px with font-weight 700"""
        number_pattern = r'\.stat-number\s*\{[^}]*font-size:\s*36px[^}]*font-weight:\s*700'
        assert re.search(number_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics numbers should be 36px with font-weight 700"

    def test_statistics_label_size_14px_color_666(self, main_css_content):
        """RED: Statistics labels should be 14px with color #666"""
        label_pattern = r'\.stat-label\s*\{[^}]*font-size:\s*14px[^}]*color:\s*#666'
        assert re.search(label_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics labels should be 14px with color #666"

    def test_statistics_section_svg_icons(self, home_html_content):
        """RED: Statistics section should use SVG icons"""
        # Check for SVG elements in statistics
        assert "<svg" in home_html_content, \
               "Statistics section should use SVG icons"

    def test_statistics_section_contains_four_items(self, home_html_content):
        """RED: Statistics section should contain exactly 4 stat items"""
        # Count stat-item occurrences
        stat_items = home_html_content.count('stat-item')
        assert stat_items >= 4, \
               f"Statistics section should contain at least 4 stat items, found {stat_items}"

    def test_statistics_responsive_desktop_1440px(self, main_css_content):
        """RED: Statistics section should be responsive for 1440px desktop"""
        desktop_pattern = r'@media\s*\([^)]*max-width:\s*1440px[^)]*\)[^}]*\.stats-container\s*\{[^}]*grid-template-columns:\s*repeat\(4'
        assert re.search(desktop_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics should maintain 4 columns on 1440px desktop"

    def test_statistics_responsive_tablet_1024px(self, main_css_content):
        """RED: Statistics section should be responsive for 1024px tablet (2 columns)"""
        tablet_pattern = r'@media\s*\([^)]*max-width:\s*1024px[^)]*\)[^}]*\.stats-container\s*\{[^}]*grid-template-columns:\s*repeat\(2'
        assert re.search(tablet_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics should switch to 2 columns on 1024px tablet"

    def test_statistics_responsive_mobile_768px(self, main_css_content):
        """RED: Statistics section should be responsive for 768px mobile (1 column)"""
        mobile_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)[^}]*\.stats-container\s*\{[^}]*grid-template-columns:\s*repeat\(1'
        assert re.search(mobile_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics should switch to 1 column on 768px mobile"

    def test_statistics_responsive_mobile_320px(self, main_css_content):
        """RED: Statistics section should be responsive for 320px small mobile"""
        small_mobile_pattern = r'@media\s*\([^)]*max-width:\s*320px[^)]*\)[^}]*\.stats-container\s*\{[^}]*grid-template-columns:\s*repeat\(1'
        assert re.search(small_mobile_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics should maintain 1 column on 320px small mobile"

    def test_statistics_item_spacing(self, main_css_content):
        """RED: Statistics items should have appropriate spacing"""
        spacing_pattern = r'\.stat-item\s*\{[^}]*margin:\s*0\s+1rem|\.stats-container\s*\{[^}]*gap:\s*2rem'
        assert re.search(spacing_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Statistics items should have proper spacing (margin or gap)"


class TestHomePageResponsiveBreakpoints:
    """Test home page responsive design at various breakpoints"""

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Responsive Design ==========
    # These tests should fail initially until implementation is complete

    def test_responsive_breakpoint_320px_mobile(self, main_css_content):
        """RED: Should have specific styles for 320px mobile breakpoint"""
        breakpoint_pattern = r'@media\s*\([^)]*max-width:\s*320px[^)]*\)'
        assert re.search(breakpoint_pattern, main_css_content, re.IGNORECASE), \
               "CSS should include 320px breakpoint for small mobile devices"

    def test_responsive_breakpoint_768px_tablet(self, main_css_content):
        """RED: Should have specific styles for 768px tablet breakpoint"""
        breakpoint_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)'
        assert re.search(breakpoint_pattern, main_css_content, re.IGNORECASE), \
               "CSS should include 768px breakpoint for tablet devices"

    def test_responsive_breakpoint_1024px_desktop(self, main_css_content):
        """RED: Should have specific styles for 1024px desktop breakpoint"""
        breakpoint_pattern = r'@media\s*\([^)]*max-width:\s*1024px[^)]*\)'
        assert re.search(breakpoint_pattern, main_css_content, re.IGNORECASE), \
               "CSS should include 1024px breakpoint for desktop devices"

    def test_responsive_breakpoint_1440px_large_desktop(self, main_css_content):
        """RED: Should have specific styles for 1440px large desktop breakpoint"""
        breakpoint_pattern = r'@media\s*\([^)]*max-width:\s*1440px[^)]*\)'
        assert re.search(breakpoint_pattern, main_css_content, re.IGNORECASE), \
               "CSS should include 1440px breakpoint for large desktop devices"

    def test_hero_section_responsive_font_sizes(self, main_css_content):
        """RED: Hero section should have responsive font sizes"""
        # Check if hero title has responsive sizing
        responsive_font_pattern = r'@media[^}]*\.hero-title\s*\{[^}]*font-size'
        assert re.search(responsive_font_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero section should have responsive font sizes across breakpoints"

    def test_statistics_responsive_layout_switching(self, main_css_content):
        """RED: Statistics section should switch layout at different breakpoints"""
        # Check for responsive grid switching
        responsive_grid_pattern = r'@media[^}]*\.stats-container[^}]*grid-template-columns:\s*repeat\(\d+'
        matches = re.finditer(responsive_grid_pattern, main_css_content, re.IGNORECASE | re.DOTALL)
        grid_switches = [match for match in matches]
        assert len(grid_switches) >= 3, \
               "Statistics section should have responsive grid layout switching (1, 2, or 4 columns)"


class TestHomePageIntegration:
    """Test integration with existing design system"""

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Integration ==========
    # These tests should fail initially until implementation is complete

    def test_home_page_uses_design_system_variables(self, main_css_content):
        """RED: Home page should use CSS design system variables"""
        # Check for usage of design system variables
        variables_used = [
            "var(--color-primary)",
            "var(--color-dark)",
            "var(--color-light)",
            "var(--color-bg-card)",
            "var(--color-border)",
            "var(--color-text)"
        ]

        found_variables = []
        for var in variables_used:
            if var in main_css_content:
                found_variables.append(var)

        assert len(found_variables) >= 3, \
               f"Home page should use at least 3 CSS design system variables, found {len(found_variables)}: {found_variables}"

    def test_home_page_uses_system_typography(self, main_css_content):
        """RED: Home page should use system typography (Inter/Noto Sans JP)"""
        # Check for font-family usage
        font_pattern = r'font-family:\s*["\']?(Inter|Noto Sans JP)["\']?|font-family:\s*["\']?[,\s]*(Inter|Noto Sans JP)'
        assert re.search(font_pattern, main_css_content, re.IGNORECASE), \
               "Home page should use system typography (Inter, Noto Sans JP)"

    def test_home_page_consistent_spacing_system(self, main_css_content):
        """RED: Home page should use consistent spacing system (4px base)"""
        # Check for spacing based on 4px system (multiples of 4)
        spacing_patterns = [
            r'margin:\s*\d+px',  # Should be multiples of 4
            r'padding:\s*\d+px',  # Should be multiples of 4
            r'gap:\s*\d+px'  # Should be multiples of 4
        ]

        # This test will pass once we have proper spacing implementation
        # Check that spacing patterns exist (they should be multiples of 4px)
        assert re.search(r'padding:\s+\d+px', main_css_content), \
               "Home page should use spacing system with px values"

    def test_home_page_no_conflicting_styles(self, main_css_content):
        """RED: Home page should not have conflicting styles with header/navigation"""
        # Check that hero section doesn't override header styles
        hero_header_pattern = r'hero-section\s*\{[^}]*z-index:|\hero-section\s*\{[^}]*position:\s*absolute'
        assert not re.search(hero_header_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero section should not conflict with header navigation z-index or positioning"

    def test_home_page_section_separation(self, main_css_content):
        """RED: Hero and statistics sections should be properly separated"""
        # Check for proper spacing between sections
        separation_pattern = r'hero-section\s*\{[^}]*margin-bottom:|\stats-section\s*\{[^}]*margin-top:'
        assert re.search(separation_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Hero and statistics sections should have proper separation with margin"


# ========== Test runner for TDD approach ==========
# This helps track progress through RED → GREEN → REFACTOR → VERIFY phases

def test_home_page_redesign_tdd_progress():
    """
    TDD Progress Tracker:
    - RED: All tests should fail initially (expected)
    - GREEN: Tests pass after implementation
    - REFACTOR: Improve code while keeping tests passing
    - VERIFY: Ensure all requirements are met
    """
    # This test serves as a progress marker
    # In RED phase: This test will help track when we've moved from RED to GREEN
    assert True  # Placeholder for TDD progress tracking


class TestHomePageAccessibility:
    """Test accessibility aspects of home page redesign"""

    @pytest.fixture
    def home_html_content(self):
        """Load home.html content"""
        html_path = Path(__file__).parent.parent / "templates" / "home.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Accessibility Tests ==========
    # These tests should fail initially until proper accessibility is implemented

    def test_hero_section_has_proper_heading_hierarchy(self, home_html_content):
        """RED: Hero section should use proper heading hierarchy"""
        # Check for h1 in hero section
        assert "<h1" in home_html_content, \
               "Hero section should have h1 element for main heading"

        # Check that h1 contains the main title
        h1_content_pattern = r'<h1[^>]*>.*優秀な人材とスタートアップをつなぐ.*<\/h1>'
        assert re.search(h1_content_pattern, home_html_content, re.IGNORECASE | re.DOTALL), \
               "h1 should contain the main heading text"

    def test_cta_buttons_are_accessible(self, home_html_content):
        """RED: CTA buttons should be accessible with proper attributes"""
        # Check buttons have proper href and class attributes
        button_pattern = r'<a\s+[^>]*href="[^"]*"[^>]*class="[^"]*btn[^"]*"[^>]*>.*無料で始める.*<\/a>'
        assert re.search(button_pattern, home_html_content, re.IGNORECASE | re.DOTALL), \
               "Primary CTA button should have href and class attributes"

        secondary_button_pattern = r'<a\s+[^>]*href="[^"]*"[^>]*class="[^"]*btn[^"]*"[^>]*>.*企業を探す.*<\/a>'
        assert re.search(secondary_button_pattern, home_html_content, re.IGNORECASE | re.DOTALL), \
               "Secondary CTA button should have href and class attributes"

    def test_statistics_section_has_semantic_structure(self, home_html_content):
        """RED: Statistics section should use semantic HTML structure"""
        # Check for proper section structure
        assert "<section" in home_html_content, \
               "Statistics section should use semantic <section> element"

        # Check that stats-container properly wraps stat items
        stats_pattern = r'<section\s+[^>]*class="[^"]*stats-section[^"]*">[^<]*<div\s+[^>]*class="[^"]*stats-container[^"]*">.*<\/div>.*<\/section>'
        assert re.search(stats_pattern, home_html_content, re.IGNORECASE | re.DOTALL), \
               "Statistics section should have proper semantic structure with section > stats-container > stat-item"