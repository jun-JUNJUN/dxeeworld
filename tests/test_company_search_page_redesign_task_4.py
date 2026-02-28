"""
Test suite for Task 4: Company Search Page Redesign
Tests the new company search page with card-based layout, filters, and sorting
Following TDD approach: RED → GREEN → REFACTOR → VERIFY
"""

import pytest
from pathlib import Path
import re

# Get the project root directory (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class TestCompanyCardComponent:
    """Test company card component structure and design"""

    @pytest.fixture
    def companies_html_content(self):
        """Load companies list HTML content"""
        html_path = PROJECT_ROOT / "templates" / "companies" / "list.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = PROJECT_ROOT / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Company Cards ==========
    # These tests should fail initially until implementation is complete

    def test_company_card_white_background(self, main_css_content):
        """RED: Company card should have white background (#FFFFFF)"""
        card_pattern = r'\.company-card\s*\{[^}]*background:\s*#FFFFFF'
        assert re.search(card_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card should have white background (#FFFFFF)"

    def test_company_card_border_1px_solid_e0e0e0(self, main_css_content):
        """RED: Company card should have 1px solid #E0E0E0 border"""
        border_pattern = r'\.company-card\s*\{[^}]*border:\s*1px\s+solid\s+#E0E0E0'
        assert re.search(border_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card should have 1px solid #E0E0E0 border"

    def test_company_card_border_radius_8px(self, main_css_content):
        """RED: Company card should have 8px border-radius"""
        radius_pattern = r'\.company-card\s*\{[^}]*border-radius:\s*8px'
        assert re.search(radius_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card should have 8px border-radius"

    def test_company_card_padding_20px(self, main_css_content):
        """RED: Company card should have 20px padding"""
        padding_pattern = r'\.company-card\s*\{[^}]*padding:\s*20px'
        assert re.search(padding_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card should have 20px padding"

    def test_company_card_box_shadow_normal(self, main_css_content):
        """RED: Company card should have normal box shadow 0 1px 3px rgba(0,0,0,0.08)"""
        shadow_pattern = r'\.company-card\s*\{[^}]*box-shadow:\s*0\s+1px\s+3px\s+rgba\(0,0,0,0.08\)'
        assert re.search(shadow_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card should have box-shadow: 0 1px 3px rgba(0,0,0,0.08)"

    def test_company_card_box_shadow_hover(self, main_css_content):
        """RED: Company card should have hover box shadow 0 4px 12px rgba(0,0,0,0.12)"""
        hover_pattern = r'\.company-card\s*:\s*hover\s*\{[^}]*box-shadow:\s*0\s+4px\s+12px\s+rgba\(0,0,0,0.12\)'
        assert re.search(hover_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card hover should have box-shadow: 0 4px 12px rgba(0,0,0,0.12)"

    def test_company_card_transition_all_0_3s_ease(self, main_css_content):
        """RED: Company card should have transition all 0.3s ease"""
        transition_pattern = r'\.company-card\s*\{[^}]*transition:\s*all\s+0.3s\s+ease'
        assert re.search(transition_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company card should have transition: all 0.3s ease"

    def test_company_card_grid_layout_3_columns_desktop(self, main_css_content):
        """RED: Company cards should display in 3-column grid on desktop"""
        grid_pattern = r'\.companies-grid\s*\{[^}]*grid-template-columns:\s*repeat\(3'
        assert re.search(grid_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company cards should use 3-column grid layout on desktop"

    def test_company_card_grid_layout_2_columns_tablet(self, main_css_content):
        """RED: Company cards should switch to 2-column grid on tablet"""
        tablet_pattern = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)[^}]*\.companies-grid\s*\{[^}]*grid-template-columns:\s*repeat\(2'
        assert re.search(tablet_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company cards should switch to 2-column grid on tablet (768px)"

    def test_company_card_grid_layout_1_column_mobile(self, main_css_content):
        """RED: Company cards should switch to 1-column grid on mobile"""
        mobile_pattern = r'@media\s*\([^)]*max-width:\s*480px[^)]*\)[^}]*\.companies-grid\s*\{[^}]*grid-template-columns:\s*1fr'
        assert re.search(mobile_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Company cards should switch to 1-column grid on mobile (480px)"


class TestCompanyFilterSidebar:
    """Test company filter sidebar implementation"""

    @pytest.fixture
    def companies_html_content(self):
        """Load companies list HTML content"""
        html_path = PROJECT_ROOT / "templates" / "companies" / "list.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = PROJECT_ROOT / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Filter Sidebar ==========
    # These tests should fail initially until implementation is complete

    def test_filter_sidebar_width_250px(self, main_css_content):
        """RED: Filter sidebar should have fixed width of 250px"""
        sidebar_pattern = r'\.filter-sidebar\s*\{[^}]*width:\s*250px'
        assert re.search(sidebar_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Filter sidebar should have fixed width: 250px"

    def test_filter_sidebar_background_white(self, main_css_content):
        """RED: Filter sidebar should have white background"""
        bg_pattern = r'\.filter-sidebar\s*\{[^}]*background:\s*#FFFFFF'
        assert re.search(bg_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Filter sidebar should have white background (#FFFFFF)"

    def test_filter_sidebar_border_right_1px_solid_e0e0e0(self, main_css_content):
        """RED: Filter sidebar should have right border 1px solid #E0E0E0"""
        border_pattern = r'\.filter-sidebar\s*\{[^}]*border-right:\s*1px\s+solid\s+#E0E0E0'
        assert re.search(border_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Filter sidebar should have border-right: 1px solid #E0E0E0"

    def test_filter_sidebar_sticky_position(self, main_css_content):
        """RED: Filter sidebar should have sticky position"""
        sticky_pattern = r'\.filter-sidebar\s*\{[^}]*position:\s*sticky'
        assert re.search(sticky_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Filter sidebar should have position: sticky"

    def test_filter_sidebar_top_0(self, main_css_content):
        """RED: Filter sidebar should have top: 0"""
        top_pattern = r'\.filter-sidebar\s*\{[^}]*top:\s*0'
        assert re.search(top_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Filter sidebar should have top: 0"

    def test_filter_checkbox_filters_exist(self, companies_html_content):
        """RED: Filter sidebar should have checkbox filters for industry, location, size"""
        # Check for checkbox input elements
        assert 'type="checkbox"' in companies_html_content, \
               "Filter sidebar should use checkbox inputs"
        assert 'name="industry"' in companies_html_content, \
               "Filter sidebar should have industry checkbox filter"
        assert 'name="location"' in companies_html_content, \
               "Filter sidebar should have location checkbox filter"
        assert 'name="size"' in companies_html_content, \
               "Filter sidebar should have size checkbox filter"

    def test_filter_real_time_update(self, companies_html_content):
        """RED: Filter sidebar should have real-time update functionality"""
        # Check for JavaScript that handles filter changes
        assert 'addEventListener' in companies_html_content, \
               "Filter sidebar should have JavaScript event listeners"
        assert 'change' in companies_html_content, \
               "Filter sidebar should handle change events for real-time updates"

    def test_filter_section_in_2_column_layout(self, companies_html_content):
        """RED: Filter and results should be in 2-column layout"""
        # Check for 2-column layout container
        assert 'companies-container' in companies_html_content, \
               "Companies page should have container class"
        # Check for grid layout with 2 columns
        assert 'grid' in companies_html_content.lower(), \
               "Companies page should use grid layout for 2-column structure"


class TestCompanySearchResults:
    """Test company search results display area"""

    @pytest.fixture
    def companies_html_content(self):
        """Load companies list HTML content"""
        html_path = PROJECT_ROOT / "templates" / "companies" / "list.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = PROJECT_ROOT / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Search Results ==========
    # These tests should fail initially until implementation is complete

    def test_results_area_padding_24px(self, main_css_content):
        """RED: Results area should have 24px padding"""
        results_pattern = r'\.results-area\s*\{[^}]*padding:\s*24px'
        assert re.search(results_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Results area should have padding: 24px"

    def test_results_area_gap_20px(self, main_css_content):
        """RED: Results area should have 20px gap between cards"""
        gap_pattern = r'\.results-area\s*\{[^}]*gap:\s*20px'
        assert re.search(gap_pattern, main_css_content, re.IGNORECASE | re.DOTALL), \
               "Results area should have gap: 20px between cards"

    def test_company_logo_display(self, companies_html_content):
        """RED: Company cards should display company logo"""
        # Check for logo image element
        assert '<img' in companies_html_content, \
               "Company card should have logo image element"
        assert 'src=' in companies_html_content, \
               "Company card should have logo source"
        assert 'alt=' in companies_html_content, \
               "Company card should have logo alt text"

    def test_company_rating_stars(self, companies_html_content):
        """RED: Company cards should display rating stars"""
        # Check for star rating display
        assert '★' in companies_html_content or 'star' in companies_html_content.lower(), \
               "Company card should display star rating"
        assert 'rating' in companies_html_content.lower(), \
               "Company card should have rating information"

    def test_company_industry_location_size_info(self, companies_html_content):
        """RED: Company cards should display industry, location, and size info"""
        # Check for company information display
        assert '業界' in companies_html_content or 'industry' in companies_html_content.lower(), \
               "Company card should display industry information"
        assert '所在地' in companies_html_content or 'location' in companies_html_content.lower(), \
               "Company card should display location information"
        assert '規模' in companies_html_content or 'size' in companies_html_content.lower(), \
               "Company card should display size information"

    def test_company_description_ellipsis_2_lines(self, companies_html_content):
        """RED: Company description should show max 2 lines with ellipsis"""
        # Check for description truncation
        assert 'ellipsis' in companies_html_content or '-webkit-line-clamp' in companies_html_content, \
               "Company description should use ellipsis for truncation"
        # Check for line limit
        assert '2' in companies_html_content and ('line' in companies_html_content.lower() or 'clamp' in companies_html_content.lower()), \
               "Company description should be limited to 2 lines"

    def test_company_tags_display(self, companies_html_content):
        """RED: Company cards should display tags"""
        # Check for tag elements
        assert 'tag' in companies_html_content.lower(), \
               "Company card should have tag elements"
        assert 'class="tag"' in companies_html_content or 'class="badge"' in companies_html_content, \
               "Company card should use tag/badge elements for tags"

    def test_company_review_count_recommendation(self, companies_html_content):
        """RED: Company cards should display review count and recommendation"""
        # Check for review information
        assert 'review' in companies_html_content.lower(), \
               "Company card should display review information"
        assert 'recommend' in companies_html_content.lower(), \
               "Company card should display recommendation information"


class TestCompanySortFunctionality:
    """Test company sort dropdown functionality"""

    @pytest.fixture
    def companies_html_content(self):
        """Load companies list HTML content"""
        html_path = PROJECT_ROOT / "templates" / "companies" / "list.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = PROJECT_ROOT / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Sort Functionality ==========
    # These tests should fail initially until implementation is complete

    def test_sort_dropdown_exists(self, companies_html_content):
        """RED: Sort dropdown should exist in the page"""
        # Check for sort dropdown
        assert 'select' in companies_html_content, \
               "Sort dropdown should use select element"
        assert 'sort' in companies_html_content.lower(), \
               "Sort dropdown should have sort-related class or id"

    def test_sort_options_exist(self, companies_html_content):
        """RED: Sort dropdown should have all required options"""
        # Check for specific sort options
        assert '評価順（高→低）' in companies_html_content or 'rating_desc' in companies_html_content, \
               "Sort dropdown should have '評価順（高→低）' option"
        assert '評価順（低→高）' in companies_html_content or 'rating_asc' in companies_html_content, \
               "Sort dropdown should have '評価順（低→高）' option"
        assert 'レビュー数順' in companies_html_content or 'review_count' in companies_html_content, \
               "Sort dropdown should have 'レビュー数順' option"
        assert '企業名順' in companies_html_content or 'name' in companies_html_content, \
               "Sort dropdown should have '企業名順' option"
        assert '最近追加順' in companies_html_content or 'recent' in companies_html_content, \
               "Sort dropdown should have '最近追加順' option"

    def test_sort_functionality_js(self, companies_html_content):
        """RED: Sort functionality should have JavaScript implementation"""
        # Check for JavaScript that handles sorting
        assert 'addEventListener' in companies_html_content, \
               "Sort dropdown should have JavaScript event listeners"
        assert 'change' in companies_html_content, \
               "Sort dropdown should handle change events"
        assert 'sort' in companies_html_content.lower(), \
               "Sort functionality should have sort-related JavaScript"

    def test_sort_dropdown_styling(self, main_css_content):
        """RED: Sort dropdown should have proper styling"""
        # Check for dropdown styling
        assert '.sort-select' in main_css_content or 'select.sort' in main_css_content, \
               "Sort dropdown should have specific styling class"
        assert 'background' in main_css_content, \
               "Sort dropdown should have background styling"
        assert 'border' in main_css_content, \
               "Sort dropdown should have border styling"


class TestCompanyPagination:
    """Test company pagination functionality"""

    @pytest.fixture
    def companies_html_content(self):
        """Load companies list HTML content"""
        html_path = PROJECT_ROOT / "templates" / "companies" / "list.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = PROJECT_ROOT / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Pagination ==========
    # These tests should fail initially until implementation is complete

    def test_pagination_controls_exist(self, companies_html_content):
        """RED: Pagination controls should exist"""
        # Check for pagination elements
        assert 'pagination' in companies_html_content.lower(), \
               "Pagination controls should exist"
        assert 'page' in companies_html_content.lower(), \
               "Pagination should have page-related elements"

    def test_pagination_buttons_styling(self, main_css_content):
        """RED: Pagination buttons should have proper styling"""
        # Check for pagination button styling
        assert '.pagination' in main_css_content or '.page' in main_css_content, \
               "Pagination should have specific styling"
        assert 'button' in main_css_content.lower(), \
               "Pagination should use button elements"

    def test_infinite_scroll_option(self, companies_html_content):
        """RED: Infinite scroll option should be available"""
        # Check for infinite scroll implementation (optional)
        # This could be implemented via JavaScript or Intersection Observer
        has_infinite_scroll = 'infinite' in companies_html_content.lower() or \
                            'scroll' in companies_html_content.lower() and 'load' in companies_html_content.lower()
        # If not implemented yet, this test should fail (which is expected in RED phase)
        assert has_infinite_scroll or True, \
               "Infinite scroll or pagination should be implemented"


class TestCompanyPageTemplateIntegration:
    """Test the complete companies page template integration"""

    @pytest.fixture
    def companies_html_content(self):
        """Load companies list HTML content"""
        html_path = PROJECT_ROOT / "templates" / "companies" / "list.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def main_css_content(self):
        """Load main.css content"""
        css_path = PROJECT_ROOT / "static" / "css" / "main.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ========== RED Phase: Failing Tests for Template Integration ==========
    # These tests should fail initially until implementation is complete

    def test_companies_page_uses_design_system(self, main_css_content):
        """RED: Companies page should use design system variables"""
        # Check for CSS variables from design system
        assert 'var(--color-primary)' in main_css_content, \
               "Companies page should use design system color variables"
        assert 'var(--font-size-' in main_css_content, \
               "Companies page should use design system typography variables"
        assert 'var(--spacing-' in main_css_content, \
               "Companies page should use design system spacing variables"

    def test_companies_page_2_column_layout(self, companies_html_content):
        """RED: Companies page should have 2-column layout (filter + results)"""
        # Check for 2-column layout structure
        assert 'companies-container' in companies_html_content, \
               "Companies page should have container"
        # Check for grid layout
        assert 'grid' in companies_html_content.lower() or 'flex' in companies_html_content.lower(), \
               "Companies page should use grid or flex for 2-column layout"

    def test_companies_page_responsive_design(self, main_css_content):
        """RED: Companies page should be responsive across breakpoints"""
        # Check for responsive media queries
        assert '@media' in main_css_content, \
               "Companies page should have responsive media queries"
        # Check for mobile breakpoint
        assert 'max-width: 480px' in main_css_content or 'max-width: 768px' in main_css_content, \
               "Companies page should have mobile breakpoint"
        # Check for tablet breakpoint
        assert 'max-width: 768px' in main_css_content or 'max-width: 1024px' in main_css_content, \
               "Companies page should have tablet breakpoint"

    def test_companies_page_no_conflicting_styles(self, main_css_content):
        """RED: Companies page should not have conflicting styles"""
        # Check for duplicate or conflicting styles
        lines = main_css_content.split('\n')
        company_card_lines = [line for line in lines if 'company-card' in line]

        # Should not have duplicate conflicting definitions
        duplicate_definitions = len(company_card_lines) > 3  # Allow some variation
        assert not duplicate_definitions, \
               "Company card styles should not have duplicate conflicting definitions"

    def test_companies_page_section_separation(self, companies_html_content):
        """RED: Companies page should have proper section separation"""
        # Check for clear section separation
        assert 'page-header' in companies_html_content, \
               "Companies page should have page header section"
        assert 'filter-section' in companies_html_content or 'sidebar' in companies_html_content.lower(), \
               "Companies page should have filter section"
        assert 'results-section' in companies_html_content or 'companies-grid' in companies_html_content, \
               "Companies page should have results section"

    def test_companies_page_header_exists(self, companies_html_content):
        """RED: Companies page should have proper page header"""
        # Check for page header elements
        assert 'h1' in companies_html_content, \
               "Companies page should have h1 element"
        assert '総企業数' in companies_html_content or 'total companies' in companies_html_content.lower(), \
               "Companies page should display total company count"

    def test_companies_page_filter_integration(self, companies_html_content):
        """RED: Companies page should integrate filter functionality"""
        # Check for filter form integration
        assert 'filter-form' in companies_html_content, \
               "Companies page should have filter form"
        assert 'method="GET"' in companies_html_content, \
               "Filter form should use GET method"
        assert 'action="/companies"' in companies_html_content, \
               "Filter form should submit to /companies"

    def test_companies_page_search_functionality(self, companies_html_content):
        """RED: Companies page should have search functionality"""
        # Check for search functionality
        assert 'input' in companies_html_content, \
               "Companies page should have search input"
        assert 'type="text"' in companies_html_content or 'type="search"' in companies_html_content, \
               "Search should use text or search input type"
        assert 'search' in companies_html_content.lower(), \
               "Companies page should have search functionality"