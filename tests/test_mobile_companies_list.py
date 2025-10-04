"""
モバイル端末での企業一覧表示のテスト
Requirements: 1.1, 1.2, 1.3, 1.5
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class TestMobileCompaniesListDisplay:
    """モバイル端末での企業一覧表示テスト"""

    @pytest.fixture
    def mobile_driver(self):
        """モバイル端末シミュレーション用ドライバー"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # モバイル端末サイズ設定 (iPhone 12 Pro相当)
        chrome_options.add_argument("--window-size=390,844")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(390, 844)
        yield driver
        driver.quit()

    def test_filter_form_mobile_layout(self, mobile_driver):
        """
        Requirement 1.1: モバイル端末でフィルターフォームが画面幅内に収まること
        """
        # 企業一覧ページにアクセス
        mobile_driver.get("http://localhost:8202/companies")

        # フィルターセクションの要素を取得
        filters_section = mobile_driver.find_element(By.CLASS_NAME, "filters-section")
        filters_grid = mobile_driver.find_element(By.CLASS_NAME, "filters-grid")

        # 画面幅取得
        viewport_width = mobile_driver.execute_script("return window.innerWidth;")

        # フィルターセクションが画面幅内に収まっているかチェック
        filters_width = filters_section.size['width']
        assert filters_width <= viewport_width, f"フィルターセクション幅 {filters_width}px が画面幅 {viewport_width}px を超えています"

        # フィルターグリッドが単列表示になっているかチェック
        grid_style = mobile_driver.execute_script(
            "return window.getComputedStyle(arguments[0]).getPropertyValue('grid-template-columns');",
            filters_grid
        )
        # 768px以下では単列表示 (1fr) になるべき
        assert "1fr" in grid_style, f"フィルターグリッドが単列表示になっていません: {grid_style}"

    def test_dropdown_filters_mobile_display(self, mobile_driver):
        """
        Requirement 1.2, 1.3: 業界・企業規模フィルターが画面幅内に表示されること
        """
        mobile_driver.get("http://localhost:8202/companies")

        # 業界ドロップダウンをテスト
        industry_select = mobile_driver.find_element(By.ID, "industry")
        industry_width = industry_select.size['width']
        viewport_width = mobile_driver.execute_script("return window.innerWidth;")

        assert industry_width <= viewport_width, f"業界ドロップダウン幅 {industry_width}px が画面幅を超えています"

        # 企業規模ドロップダウンをテスト
        size_select = mobile_driver.find_element(By.ID, "size")
        size_width = size_select.size['width']

        assert size_width <= viewport_width, f"企業規模ドロップダウン幅 {size_width}px が画面幅を超えています"

    def test_form_elements_vertical_layout(self, mobile_driver):
        """
        Requirement 1.5: 768px以下で全フォーム要素が垂直配置されること
        """
        mobile_driver.get("http://localhost:8202/companies")

        # フィルターグリッド内の要素が垂直配置されているかチェック
        filter_groups = mobile_driver.find_elements(By.CLASS_NAME, "filter-group")

        # 少なくとも2つのフィルターグループが存在することを確認
        assert len(filter_groups) >= 2, "フィルターグループが不足しています"

        # 最初の2つの要素の位置を比較（垂直配置なら2番目の要素のtopが1番目より大きい）
        if len(filter_groups) >= 2:
            first_rect = filter_groups[0].rect
            second_rect = filter_groups[1].rect

            assert second_rect['y'] > first_rect['y'], "フィルター要素が垂直配置されていません"

    def test_page_reload_layout_persistence(self, mobile_driver):
        """
        Requirement 1.4: ページリロード時にフォームレイアウトが維持されること
        """
        mobile_driver.get("http://localhost:8202/companies")

        # 初期状態のレイアウト情報を取得
        filters_section = mobile_driver.find_element(By.CLASS_NAME, "filters-section")
        initial_width = filters_section.size['width']

        # ページをリロード
        mobile_driver.refresh()
        time.sleep(1)  # レンダリング待機

        # リロード後のレイアウト情報を取得
        filters_section_after = mobile_driver.find_element(By.CLASS_NAME, "filters-section")
        width_after_reload = filters_section_after.size['width']

        # レイアウトが維持されているかチェック
        assert abs(initial_width - width_after_reload) <= 5, "リロード後にレイアウトが変化しました"

    def test_form_elements_padding_margin_mobile(self, mobile_driver):
        """
        フォーム要素のパディングとマージンがモバイル向けに調整されていること
        """
        mobile_driver.get("http://localhost:8202/companies")

        # フィルターグループ要素のスタイルをチェック
        filter_group = mobile_driver.find_element(By.CLASS_NAME, "filter-group")

        # 計算されたスタイルを取得
        computed_style = mobile_driver.execute_script("""
            var element = arguments[0];
            var style = window.getComputedStyle(element);
            return {
                marginBottom: style.getPropertyValue('margin-bottom'),
                padding: style.getPropertyValue('padding')
            };
        """, filter_group)

        # モバイル向けのマージンが適用されていることを確認
        # 具体的な値は実装後に調整
        assert computed_style['marginBottom'] != '0px', "フィルターグループにマージンが設定されていません"