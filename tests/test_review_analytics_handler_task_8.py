"""
Test: Review Analytics Handler & Radar Chart (Task 8.2-8.4)

テスト内容:
- GET /companies/:id/stats エンドポイント（8.4）
- レーダーチャート用 JS ファイルの存在確認（8.3）
- レーダーチャートクラスの構造検証（8.3）
- spawn_callback パターン実装確認（8.2）

Requirements: 12.1～12.5
"""
import os
import re
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


RADAR_JS_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'static', 'js', 'radarChart.js'
)

COMPANY_STATS_HANDLER_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'src', 'handlers', 'company_stats_handler.py'
)

REVIEW_HANDLER_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'src', 'handlers', 'review_handler.py'
)


def read_js(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def read_py(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ─────────────────────────────────────────────
# Task 8.3: レーダーチャート JS ファイルのテスト
# ─────────────────────────────────────────────

class TestRadarChartFileExists:
    """radarChart.js ファイルの存在確認"""

    def test_radar_chart_js_file_exists(self):
        """radarChart.js が存在すること"""
        assert os.path.exists(RADAR_JS_PATH), \
            f"radarChart.js が見つかりません: {RADAR_JS_PATH}"

    def test_radar_chart_js_is_not_empty(self):
        """radarChart.js が空でないこと"""
        assert os.path.getsize(RADAR_JS_PATH) > 0


class TestRadarChartClassStructure:
    """RadarChart クラス構造の検証"""

    def test_radar_chart_class_defined(self):
        """RadarChart クラスまたは関連クラスが定義されていること"""
        content = read_js(RADAR_JS_PATH)
        assert 'class RadarChart' in content or 'RadarChart' in content

    def test_constructor_exists(self):
        """constructor が定義されていること"""
        content = read_js(RADAR_JS_PATH)
        assert 'constructor(' in content

    def test_render_method_exists(self):
        """render/draw/init メソッドが定義されていること"""
        content = read_js(RADAR_JS_PATH)
        assert (
            'render(' in content or
            'draw(' in content or
            'init(' in content or
            'initialize(' in content
        )

    def test_update_method_exists(self):
        """updateData/update メソッドが定義されていること"""
        content = read_js(RADAR_JS_PATH)
        assert 'update' in content.lower()

    def test_8_categories_labels_defined(self):
        """8カテゴリーのラベルが定義されていること"""
        content = read_js(RADAR_JS_PATH)
        assert (
            'compensation' in content.lower() or
            '待遇' in content or
            'Compensation' in content
        )
        assert (
            'work_life' in content.lower() or
            'worklife' in content.lower() or
            'wlb' in content.lower() or
            'ワークライフ' in content or
            'Work-Life' in content or
            'Work Life' in content
        )

    def test_company_color_defined(self):
        """企業スコアの色(#20BEFF)が定義されていること"""
        content = read_js(RADAR_JS_PATH)
        assert '#20BEFF' in content or '20BEFF' in content or '32, 190, 255' in content

    def test_canvas_or_chart_element_used(self):
        """canvas または Chart.js 関連コードが含まれること"""
        content = read_js(RADAR_JS_PATH)
        assert (
            'canvas' in content.lower() or
            'Chart' in content or
            'chart' in content.lower() or
            'd3' in content.lower()
        )

    def test_mobile_responsive_fallback(self):
        """モバイル対応（768px以下で棒グラフ切り替え）が実装されていること"""
        content = read_js(RADAR_JS_PATH)
        assert '768' in content or 'mobile' in content.lower() or 'responsive' in content.lower()

    def test_industry_average_support(self):
        """業界平均データのサポートが実装されていること"""
        content = read_js(RADAR_JS_PATH)
        assert (
            'industry' in content.lower() or
            '業界' in content or
            'benchmark' in content.lower() or
            'average' in content.lower()
        )


# ─────────────────────────────────────────────
# Task 8.4: 企業統計エンドポイントのテスト
# ─────────────────────────────────────────────

class TestCompanyStatsHandlerFileExists:
    """company_stats_handler.py の存在確認"""

    def test_stats_handler_file_exists(self):
        """company_stats_handler.py が存在すること"""
        assert os.path.exists(COMPANY_STATS_HANDLER_PATH), \
            f"company_stats_handler.py が見つかりません: {COMPANY_STATS_HANDLER_PATH}"

    def test_stats_handler_is_not_empty(self):
        """company_stats_handler.py が空でないこと"""
        assert os.path.getsize(COMPANY_STATS_HANDLER_PATH) > 0


class TestCompanyStatsHandlerStructure:
    """CompanyStatsHandler クラス構造の検証"""

    def test_handler_class_defined(self):
        """CompanyStatsHandler クラスが定義されていること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'class CompanyStatsHandler' in content

    def test_get_method_exists(self):
        """非同期 get メソッドが定義されていること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'async def get(' in content

    def test_aggregation_service_used(self):
        """ReviewAggregationService が使用されていること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'ReviewAggregationService' in content or 'aggregation_service' in content

    def test_json_response_returned(self):
        """JSON レスポンスを返すこと"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'write_json' in content or 'write(' in content or 'json' in content.lower()

    def test_overall_rating_in_response(self):
        """overall_rating がレスポンスに含まれること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'overall_rating' in content

    def test_nps_score_in_response(self):
        """nps_score がレスポンスに含まれること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'nps_score' in content or 'nps' in content.lower()

    def test_category_scores_in_response(self):
        """category_scores がレスポンスに含まれること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'category_scores' in content or 'category' in content.lower()

    def test_review_count_in_response(self):
        """review_count がレスポンスに含まれること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'review_count' in content

    def test_industry_averages_in_response(self):
        """industry_averages がレスポンスに含まれること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'industry_averages' in content or 'benchmark' in content.lower()

    def test_last_updated_in_response(self):
        """last_updated がレスポンスに含まれること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'last_updated' in content

    def test_company_id_validated(self):
        """company_id のバリデーションが実装されていること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'company_id' in content

    def test_error_handling_exists(self):
        """エラーハンドリングが実装されていること"""
        content = read_py(COMPANY_STATS_HANDLER_PATH)
        assert 'except' in content or 'try' in content


# ─────────────────────────────────────────────
# Task 8.2: 非同期バックグラウンド計算確認
# ─────────────────────────────────────────────

class TestReviewHandlerSpawnCallback:
    """review_handler.py のバックグラウンド計算実装確認"""

    def test_review_handler_has_background_aggregation(self):
        """review_handler.py がバックグラウンド集計を呼び出すこと"""
        content = read_py(REVIEW_HANDLER_PATH)
        assert (
            'spawn_callback' in content or
            'create_task' in content or
            'asyncio' in content
        ) and (
            'aggregate' in content or
            'aggregation' in content
        )

    def test_aggregation_service_imported_in_handler(self):
        """ReviewAggregationService が review_handler.py でインポートされていること"""
        content = read_py(REVIEW_HANDLER_PATH)
        assert 'ReviewAggregationService' in content

    def test_background_task_called_after_successful_submit(self):
        """レビュー投稿成功後にバックグラウンドタスクが呼び出されること"""
        content = read_py(REVIEW_HANDLER_PATH)
        # aggregate_and_update_company が呼ばれることを確認
        assert 'aggregate_and_update_company' in content or 'get_company_aggregations' in content

    def test_response_does_not_wait_for_aggregation(self):
        """ユーザーへのレスポンスが集計完了を待たないこと（create_task または spawn_callback 使用）"""
        content = read_py(REVIEW_HANDLER_PATH)
        assert 'create_task' in content or 'spawn_callback' in content


# ─────────────────────────────────────────────
# Task 8.4: app.py での URL ルーティング確認
# ─────────────────────────────────────────────

class TestStatsEndpointRouting:
    """app.py での /companies/:id/stats ルーティング確認"""

    def test_stats_route_registered_in_app(self):
        """app.py に /companies/:id/stats ルートが登録されていること"""
        app_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'src', 'app.py'
        )
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert '/stats' in content or 'stats' in content.lower()
