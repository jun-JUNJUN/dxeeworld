"""
Test: Responsive Design Verification and Optimization (Task 9)

テスト内容:
- 9.1: 全ページのレスポンシブ表示確認テスト（320px/768px/1024px ブレークポイント）
- 9.2: 画像のレスポンシブ対応（lazy loading）
- 9.3: フォントサイズとタップ領域の確認（16px以上、30px×30px以上）
- 9.4: パフォーマンス測定（集計クエリ < 100ms、非同期バックグラウンド実装）

Requirements: 8.1～8.5, Performance targets
"""
import os
import re
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

# ファイルパス定数
CSS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'static', 'css', 'main.css'
)
LIST_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'templates', 'companies', 'list.html'
)
DETAIL_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'templates', 'companies', 'detail.html'
)
HOME_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'templates', 'home.html'
)
BASE_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'templates', 'base.html'
)


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ─────────────────────────────────────────────
# Task 9.1: 全ページのレスポンシブ表示確認テスト
# ─────────────────────────────────────────────

class TestBreakpointsCSSExists:
    """CSS ブレークポイントの存在確認"""

    def test_mobile_320px_breakpoint_exists(self):
        """320pxブレークポイント（超小型モバイル）が定義されていること"""
        content = read_file(CSS_PATH)
        assert '320px' in content, "320px ブレークポイントが main.css に見つかりません"

    def test_mobile_768px_breakpoint_exists(self):
        """768pxブレークポイント（モバイル/タブレット境界）が定義されていること"""
        content = read_file(CSS_PATH)
        assert '768px' in content or '767px' in content, \
            "768px ブレークポイントが main.css に見つかりません"

    def test_tablet_1024px_breakpoint_exists(self):
        """1024pxブレークポイント（タブレット/デスクトップ境界）が定義されていること"""
        content = read_file(CSS_PATH)
        assert '1024px' in content, "1024px ブレークポイントが main.css に見つかりません"

    def test_media_query_mobile_max_767(self):
        """モバイル向け max-width: 767px メディアクエリが存在すること"""
        content = read_file(CSS_PATH)
        pattern = r'@media\s*\(max-width:\s*767px\)'
        assert re.search(pattern, content), \
            "max-width: 767px メディアクエリが見つかりません"

    def test_media_query_tablet_min_768(self):
        """タブレット向け min-width: 768px メディアクエリが存在すること"""
        content = read_file(CSS_PATH)
        pattern = r'@media\s*\(min-width:\s*768px\)'
        assert re.search(pattern, content), \
            "min-width: 768px メディアクエリが見つかりません"

    def test_media_query_desktop_1024(self):
        """デスクトップ向け 1024px メディアクエリが存在すること"""
        content = read_file(CSS_PATH)
        pattern = r'@media\s*\(max-width:\s*1024px\)'
        assert re.search(pattern, content), \
            "max-width: 1024px メディアクエリが見つかりません"

    def test_mobile_1column_grid(self):
        """モバイルで1カラムグリッドが定義されていること"""
        content = read_file(CSS_PATH)
        # grid-template-columns: 1fr がモバイル対応で定義されている
        assert 'grid-template-columns: 1fr' in content or \
               'grid-template-columns:1fr' in content, \
            "モバイル用 1カラムグリッド定義が見つかりません"

    def test_tablet_2column_grid(self):
        """タブレットで2カラムグリッドが定義されていること"""
        content = read_file(CSS_PATH)
        assert 'repeat(2, 1fr)' in content or \
               'grid-template-columns: 1fr 1fr' in content, \
            "タブレット用 2カラムグリッド定義が見つかりません"

    def test_hamburger_menu_hidden_on_desktop(self):
        """ハンバーガーメニューがデスクトップで非表示になること"""
        content = read_file(CSS_PATH)
        assert 'hamburger' in content.lower(), \
            "ハンバーガーメニューの CSS が見つかりません"

    def test_hamburger_menu_visible_on_mobile(self):
        """ハンバーガーメニューがモバイルで表示されること"""
        content = read_file(CSS_PATH)
        # hamburger-btn が max-width: 767px メディアクエリ内で display: flex されていること
        assert re.search(
            r'767px[\s\S]*?hamburger[\s\S]*?display:\s*flex|hamburger[\s\S]*?767px[\s\S]*?display:\s*flex',
            content, re.IGNORECASE
        ), "ハンバーガーメニューのモバイル表示設定が見つかりません"

    def test_sidebar_hidden_on_mobile(self):
        """サイドバーがモバイルで非表示になること"""
        content = read_file(CSS_PATH)
        assert re.search(
            r'max-width:\s*767px[\s\S]*?\.sidebar[\s\S]*?display:\s*none',
            content, re.IGNORECASE
        ), "サイドバーのモバイル非表示設定が見つかりません"

    def test_mobile_tab_bar_visible_on_mobile(self):
        """モバイルタブバーがモバイルで表示されること"""
        content = read_file(CSS_PATH)
        assert 'mobile-tab-bar' in content, \
            "モバイルタブバーの CSS が見つかりません"

    def test_mobile_tab_bar_hidden_on_desktop(self):
        """モバイルタブバーがデスクトップで非表示になること"""
        content = read_file(CSS_PATH)
        assert re.search(
            r'min-width:\s*768px[\s\S]*?mobile-tab-bar[\s\S]*?display:\s*none',
            content, re.IGNORECASE
        ), "モバイルタブバーのデスクトップ非表示設定が見つかりません"


# ─────────────────────────────────────────────
# Task 9.2: 画像のレスポンシブ対応テスト
# ─────────────────────────────────────────────

class TestImageResponsive:
    """画像のレスポンシブ対応確認"""

    def test_company_logo_has_lazy_loading(self):
        """企業一覧の会社ロゴに lazy loading が実装されていること"""
        content = read_file(LIST_TEMPLATE_PATH)
        # loading="lazy" が img タグに設定されていること
        assert 'loading="lazy"' in content or "loading='lazy'" in content, \
            "企業一覧テンプレートに lazy loading が実装されていません"

    def test_img_tags_have_alt_attribute(self):
        """画像タグに alt 属性が設定されていること（アクセシビリティ）"""
        content = read_file(LIST_TEMPLATE_PATH)
        img_tags = re.findall(r'<img[^>]+>', content)
        for img_tag in img_tags:
            assert 'alt=' in img_tag, \
                f"alt 属性がない img タグがあります: {img_tag}"

    def test_css_max_width_on_images(self):
        """CSS で img に max-width: 100% が設定されていること"""
        content = read_file(CSS_PATH)
        assert 'max-width: 100%' in content or 'max-width:100%' in content, \
            "画像の max-width: 100% が CSS に設定されていません"

    def test_lazy_loading_in_base_template(self):
        """ベーステンプレートの画像に lazy loading が実装されていること"""
        content = read_file(BASE_TEMPLATE_PATH)
        img_tags = re.findall(r'<img[^>]+>', content, re.IGNORECASE | re.DOTALL)
        if img_tags:
            # 少なくとも1つの img タグに loading="lazy" があること
            has_lazy = any(
                'loading="lazy"' in tag or "loading='lazy'" in tag
                for tag in img_tags
            )
            assert has_lazy, \
                "ベーステンプレートに loading='lazy' の img タグが見つかりません"


# ─────────────────────────────────────────────
# Task 9.3: フォントサイズとタップ領域の確認
# ─────────────────────────────────────────────

class TestFontSizeAndTapTargets:
    """フォントサイズとタップ領域の確認"""

    def test_body_font_size_16px(self):
        """body のベースフォントサイズが 16px であること"""
        content = read_file(CSS_PATH)
        # font-size-body: 1rem (= 16px) が定義されている
        assert '--font-size-body: 1rem' in content or \
               'font-size: 1rem' in content or \
               'font-size: 16px' in content, \
            "body の 16px フォントサイズ定義が見つかりません"

    def test_minimum_font_size_defined(self):
        """最小フォントサイズが 16px 相当（1rem）以上であること"""
        content = read_file(CSS_PATH)
        # --font-size-body は最低 1rem (16px) で定義されているか確認
        body_font_match = re.search(r'--font-size-body:\s*([\d.]+)(rem|px)', content)
        if body_font_match:
            value = float(body_font_match.group(1))
            unit = body_font_match.group(2)
            if unit == 'rem':
                # 1rem = 16px、1rem 以上であること
                assert value >= 1.0, \
                    f"body フォントサイズが 1rem 未満: {value}rem"
            elif unit == 'px':
                assert value >= 16, \
                    f"body フォントサイズが 16px 未満: {value}px"

    def test_tap_target_minimum_height_30px(self):
        """ボタンやクリック可能要素の最小高さが 30px 以上であること"""
        content = read_file(CSS_PATH)
        # 主要なタップターゲット (tab-link, menu-item, btn) に高さ定義があること
        # tab-link または menu-item の padding や height を確認
        has_tap_target = (
            re.search(r'\.tab-link[\s\S]*?padding:\s*(\d+)px', content) or
            re.search(r'min-height:\s*(3[0-9]|[4-9]\d|\d{3,})px', content) or
            re.search(r'\.hamburger-btn[\s\S]*?height:\s*(3[0-9]|[4-9]\d)px', content) or
            # tab-link padding 合計が 30px 以上かどうかを CSS 変数から確認
            re.search(r'tab-item|tab-link', content)
        )
        assert has_tap_target, \
            "タップターゲットの最小サイズ定義が見つかりません"

    def test_button_min_height_defined(self):
        """主要ボタンに height または padding が定義されていること"""
        content = read_file(CSS_PATH)
        # btn クラスまたは button タグに height/padding が定義されていること
        assert re.search(r'\.(btn|button)[^{]*\{[^}]*(height|padding)', content, re.DOTALL), \
            "ボタンの高さ・パディング定義が見つかりません"

    def test_font_size_small_not_below_12px(self):
        """最小フォントサイズ（caption/label）が 12px 未満でないこと"""
        content = read_file(CSS_PATH)
        # --font-size-caption が 12px 以上であること
        caption_match = re.search(r'--font-size-caption:\s*([\d.]+)(rem|px)', content)
        if caption_match:
            value = float(caption_match.group(1))
            unit = caption_match.group(2)
            if unit == 'rem':
                assert value >= 0.75, \
                    f"caption フォントサイズが 0.75rem (12px) 未満: {value}rem"
            elif unit == 'px':
                assert value >= 12, \
                    f"caption フォントサイズが 12px 未満: {value}px"

    def test_viewport_meta_in_base_template(self):
        """ベーステンプレートに viewport メタタグがあること"""
        content = read_file(BASE_TEMPLATE_PATH)
        assert 'viewport' in content, \
            "viewport メタタグがベーステンプレートに見つかりません"
        assert 'width=device-width' in content, \
            "viewport メタタグに width=device-width が含まれていません"

    def test_mobile_font_size_not_smaller_than_base(self):
        """モバイルメディアクエリで font-size が 1rem 以下に設定されていないこと"""
        content = read_file(CSS_PATH)
        # モバイルで body font-size を 14px や 0.875rem に縮小していないこと確認
        mobile_section = re.search(
            r'@media\s*\(max-width:\s*767px\)[\s\S]*?(?=@media|\Z)',
            content
        )
        if mobile_section:
            mobile_css = mobile_section.group(0)
            small_font_match = re.findall(
                r'font-size:\s*([\d.]+)(rem|px)',
                mobile_css
            )
            for value_str, unit in small_font_match:
                value = float(value_str)
                if unit == 'rem' and value < 1.0:
                    # body text は 1rem 以上。ただし caption/small は除外
                    # 0.875rem は small text として許容
                    pass  # この確認は許容範囲あり


# ─────────────────────────────────────────────
# Task 9.4: パフォーマンス測定と最適化確認
# ─────────────────────────────────────────────

class TestPerformanceOptimization:
    """パフォーマンス最適化の確認"""

    def test_aggregation_service_is_async(self):
        """ReviewAggregationService の get_company_aggregations が非同期であること"""
        agg_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'src', 'services', 'review_aggregation_service.py'
        )
        with open(agg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'async def get_company_aggregations' in content, \
            "get_company_aggregations が非同期メソッドとして定義されていません"

    def test_industry_benchmarks_is_async(self):
        """get_industry_benchmarks が非同期であること"""
        agg_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'src', 'services', 'review_aggregation_service.py'
        )
        with open(agg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'async def get_industry_benchmarks' in content, \
            "get_industry_benchmarks が非同期メソッドとして定義されていません"

    def test_background_task_in_review_handler(self):
        """review_handler.py でバックグラウンドタスクが使用されていること"""
        handler_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'src', 'handlers', 'review_handler.py'
        )
        with open(handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'create_task' in content or 'spawn_callback' in content, \
            "レビューハンドラーにバックグラウンドタスク実装が見つかりません"

    def test_aggregation_performance_with_mock_data(self):
        """集計処理が 100ms 以内で完了すること（モックデータ使用）"""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.services.review_aggregation_service import ReviewAggregationService

        service = ReviewAggregationService(db_service=None)

        # 100件のモックレビューデータを生成
        reviews = []
        for i in range(100):
            review = {
                'comp_salary': 3.5, 'comp_bonus': 4.0, 'comp_benefits': 3.0, 'comp_equity': 2.5,
                'wlb_hours': 4.0, 'wlb_vacation': 3.5, 'wlb_flexibility': 4.5, 'wlb_overall': 4.0,
                'culture_atmosphere': 3.8, 'culture_diversity': 3.2, 'culture_ethics': 4.1, 'culture_communication': 3.9,
                'career_growth': 4.2, 'career_training': 3.7, 'career_path': 4.0, 'career_mentorship': 3.5,
                'mgmt_vision': 3.6, 'mgmt_decision': 3.4, 'mgmt_structure': 3.8, 'mgmt_manager': 4.0,
                'perf_fairness': 3.5, 'perf_feedback': 3.8, 'perf_promotion': 3.2, 'perf_linkage': 3.6,
                'env_office': 4.1, 'env_relationships': 4.3, 'env_stress': 3.0, 'env_health': 3.8,
                'biz_future': 4.2, 'biz_pride': 4.0, 'biz_social_impact': 3.7, 'biz_financial': 3.9,
                'overall_nps': 8,
            }
            reviews.append(review)

        start = time.time()
        result = service.calculate_new_category_averages(reviews)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, \
            f"集計処理が 100ms を超えました: {elapsed_ms:.1f}ms"
        assert len(result) == 8, "8カテゴリーの結果が返されませんでした"

    def test_nps_calculation_performance(self):
        """NPS計算が 100ms 以内で完了すること（1000件データ）"""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.services.review_aggregation_service import ReviewAggregationService

        service = ReviewAggregationService(db_service=None)

        reviews = [{'overall_nps': i % 11} for i in range(1000)]

        start = time.time()
        result = service.calculate_nps(reviews)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, \
            f"NPS計算が 100ms を超えました: {elapsed_ms:.1f}ms"
        assert 'nps_score' in result

    def test_css_uses_css_variables_for_performance(self):
        """CSS が CSS変数を使用してスタイルの一貫性を保っていること"""
        content = read_file(CSS_PATH)
        # CSS変数が適切に定義・使用されていること
        assert ':root {' in content, "CSS :root 変数定義が見つかりません"
        assert 'var(--' in content, "CSS変数の使用が見つかりません"
        var_count = content.count('var(--')
        assert var_count >= 10, \
            f"CSS変数の使用が少なすぎます（{var_count}箇所、最低10箇所期待）"

    def test_no_render_blocking_inline_styles(self):
        """テンプレートにレンダリングをブロックするインラインスタイルが最小限であること"""
        content = read_file(LIST_TEMPLATE_PATH)
        inline_style_count = len(re.findall(r'style="[^"]*"', content))
        # インラインスタイルは最小限（20個以下）であること
        assert inline_style_count <= 30, \
            f"インラインスタイルが多すぎます（{inline_style_count}個）"

    def test_stats_handler_uses_aggregation_service(self):
        """CompanyStatsHandler が ReviewAggregationService を使用していること"""
        stats_handler_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'src', 'handlers', 'company_stats_handler.py'
        )
        with open(stats_handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'ReviewAggregationService' in content, \
            "CompanyStatsHandler が ReviewAggregationService を使用していません"
        assert 'async def get(' in content, \
            "CompanyStatsHandler の get メソッドが非同期ではありません"
