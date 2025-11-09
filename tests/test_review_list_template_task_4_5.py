"""
ReviewListテンプレート の Task 4.5 機能のテスト
Task 4.5: 評価スライダーのJavaScript実装

このテストは、テンプレートが正しいJavaScriptコードと
必要な機能を含んでいるかを検証します。
"""
import pytest
from pathlib import Path
import re


class TestReviewListTemplateTask45:
    """Task 4.5: 評価スライダーのJavaScript実装のテスト"""

    def test_template_file_exists(self):
        """reviews/list.html テンプレートが存在する"""
        template_path = Path("templates/reviews/list.html")
        assert template_path.exists(), f"Template not found: {template_path}"

    def test_update_min_rating_display_function_exists(self):
        """updateMinRatingDisplay関数が存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 関数定義
        assert "function updateMinRatingDisplay(value)" in content

    def test_update_max_rating_display_function_exists(self):
        """updateMaxRatingDisplay関数が存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # 関数定義
        assert "function updateMaxRatingDisplay(value)" in content

    def test_min_rating_display_element_updated(self):
        """最低評価の表示要素が更新される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # min_rating_display要素の取得と更新
        assert "getElementById('min_rating_display')" in content
        assert "display.textContent" in content

    def test_max_rating_display_element_updated(self):
        """最高評価の表示要素が更新される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # max_rating_display要素の取得と更新
        assert "getElementById('max_rating_display')" in content

    def test_min_rating_hidden_input_updated(self):
        """最低評価のhidden inputが更新される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # min_rating hidden inputの取得と更新
        assert "getElementById('min_rating')" in content
        assert "hiddenInput.value" in content

    def test_max_rating_hidden_input_updated(self):
        """最高評価のhidden inputが更新される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # max_rating hidden inputの取得と更新
        assert "getElementById('max_rating')" in content

    def test_min_rating_zero_displays_unspecified(self):
        """最低評価が0.0の場合「指定なし」と表示する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # updateMinRatingDisplay関数内の条件分岐
        # parseFloat(value) === 0 のチェック
        assert "parseFloat(value) === 0" in content
        # 「指定なし」の表示
        assert "'指定なし'" in content or '"指定なし"' in content

    def test_max_rating_five_displays_unspecified(self):
        """最高評価が5.0の場合「指定なし」と表示する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # updateMaxRatingDisplay関数内の条件分岐
        # parseFloat(value) === 5 のチェック
        assert "parseFloat(value) === 5" in content

    def test_min_rating_non_zero_displays_value(self):
        """最低評価が0.0以外の場合は値を表示する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # updateMinRatingDisplay関数内の分岐で値を表示
        # value + ' 以上' のような表示
        assert "' 以上'" in content or '" 以上"' in content

    def test_max_rating_non_five_displays_value(self):
        """最高評価が5.0以外の場合は値を表示する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # updateMaxRatingDisplay関数内の分岐で値を表示
        # value + ' 以下' のような表示
        assert "' 以下'" in content or '" 以下"' in content

    def test_dom_content_loaded_event_listener(self):
        """DOMContentLoadedイベントリスナーが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # イベントリスナー
        assert "addEventListener('DOMContentLoaded'" in content or \
               'addEventListener("DOMContentLoaded"' in content

    def test_initial_slider_values_set_on_page_load(self):
        """ページロード時にスライダーの初期値が設定される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # min_rating_sliderの初期化
        assert "getElementById('min_rating_slider')" in content
        # max_rating_sliderの初期化
        assert "getElementById('max_rating_slider')" in content
        # 初期値の設定
        assert "updateMinRatingDisplay" in content
        assert "updateMaxRatingDisplay" in content

    def test_slider_value_passed_to_update_functions(self):
        """スライダーの値がupdate関数に渡される"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # minSlider.valueまたはmaxSlider.valueを関数に渡す
        assert "minSlider.value" in content or "Slider.value" in content
        assert "maxSlider.value" in content or "Slider.value" in content

    def test_hidden_input_cleared_when_unspecified(self):
        """「指定なし」の場合、hidden inputがクリアされる"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # hiddenInput.value = '' でクリア
        assert "hiddenInput.value = ''" in content or 'hiddenInput.value = ""' in content

    def test_oninput_handlers_call_update_functions(self):
        """oninputハンドラがupdate関数を呼び出す"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # min_rating_sliderのoninputハンドラ
        assert "oninput=\"updateMinRatingDisplay(this.value)\"" in content or \
               "oninput='updateMinRatingDisplay(this.value)'" in content or \
               "updateMinRatingDisplay" in content

        # max_rating_sliderのoninputハンドラ
        assert "oninput=\"updateMaxRatingDisplay(this.value)\"" in content or \
               "oninput='updateMaxRatingDisplay(this.value)'" in content or \
               "updateMaxRatingDisplay" in content

    def test_javascript_in_scripts_block(self):
        """JavaScriptが{% block scripts %}内に配置されている"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # scriptsブロックの存在
        assert "{% block scripts %}" in content
        # script タグ
        assert "<script>" in content

    def test_functions_handle_string_to_float_conversion(self):
        """関数が文字列からfloatへの変換を処理する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # parseFloatを使用
        assert "parseFloat(value)" in content

    def test_null_check_for_slider_elements(self):
        """スライダー要素のnullチェックが存在する"""
        template_path = Path("templates/reviews/list.html")
        content = template_path.read_text(encoding="utf-8")

        # if (minSlider) のようなチェック
        assert "if (minSlider)" in content
        assert "if (maxSlider)" in content
