/**
 * RadarChart - 企業評価レーダーチャートコンポーネント（Task 8.3）
 *
 * 8カテゴリーの評価データをレーダーチャートで可視化。
 * Chart.js を使用し、モバイル（768px以下）では棒グラフに切り替え。
 *
 * Usage:
 *   const chart = new RadarChart('canvas-id', {
 *     companyScores: [4.0, 4.5, 3.8, 4.2, 3.9, 3.5, 4.1, 4.3],
 *     industryAverages: [3.8, 4.0, 3.6, 4.0, 3.7, 3.4, 3.9, 4.0],
 *     labels: [...],
 *   });
 *   chart.render();
 */

class RadarChart {
  /** 8カテゴリーのデフォルトラベル */
  static DEFAULT_LABELS = [
    'Compensation\n待遇・報酬',
    'Work-Life Balance\nワークライフ',
    'Culture\n企業文化',
    'Career\nキャリア',
    'Management\nマネジメント',
    'Performance\n評価制度',
    'Environment\n職場環境',
    'Business\n事業・製品',
  ];

  /** 企業スコアの色: プライマリカラー */
  static COLOR_COMPANY = '#20BEFF';
  static COLOR_COMPANY_FILL = 'rgba(32, 190, 255, 0.2)';

  /** 業界平均の色: グレー */
  static COLOR_INDUSTRY = 'rgba(160, 160, 160, 0.8)';
  static COLOR_INDUSTRY_FILL = 'rgba(160, 160, 160, 0.1)';

  /** モバイルブレークポイント */
  static MOBILE_BREAKPOINT = 768;

  /**
   * @param {string} containerId  - チャートを描画するコンテナ要素のID
   * @param {Object} options
   * @param {number[]} options.companyScores     - 企業スコア（8要素, 1-5）
   * @param {number[]} [options.industryAverages] - 業界平均（8要素, optional）
   * @param {string[]} [options.labels]           - カテゴリーラベル（8要素）
   * @param {string}   [options.companyName]      - 企業名（凡例表示用）
   */
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.companyScores = options.companyScores || [];
    this.industryAverages = options.industryAverages || null;
    this.labels = options.labels || RadarChart.DEFAULT_LABELS;
    this.companyName = options.companyName || '企業スコア';
    this._chartInstance = null;
    this._isMobile = window.innerWidth < RadarChart.MOBILE_BREAKPOINT;

    // responsive: リサイズ時にチャートタイプを切り替え
    this._resizeHandler = this._handleResize.bind(this);
    window.addEventListener('resize', this._resizeHandler);
  }

  /**
   * コンテナにチャートを描画する
   */
  render() {
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.warn(`RadarChart: container #${this.containerId} not found`);
      return;
    }

    this._isMobile = window.innerWidth < RadarChart.MOBILE_BREAKPOINT;
    container.innerHTML = '';

    if (this._isMobile) {
      this._renderBarChart(container);
    } else {
      this._renderRadarChart(container);
    }
  }

  /**
   * データを更新してチャートを再描画する
   * @param {Object} data - { companyScores, industryAverages }
   */
  updateData(data) {
    if (data.companyScores !== undefined) {
      this.companyScores = data.companyScores;
    }
    if (data.industryAverages !== undefined) {
      this.industryAverages = data.industryAverages;
    }
    this.render();
  }

  /**
   * APIからデータを取得してチャートを初期化する
   * @param {string} companyId - 企業ID
   * @returns {Promise<void>}
   */
  async initialize(companyId) {
    try {
      const response = await fetch(`/companies/${companyId}/stats`);
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      const data = await response.json();

      const categoryKeys = [
        'compensation', 'work_life_balance', 'culture', 'career_development',
        'management', 'performance_system', 'work_environment', 'business_product',
      ];

      this.companyScores = categoryKeys.map(k => data.category_scores?.[k] ?? 0);

      if (data.industry_averages) {
        this.industryAverages = categoryKeys.map(k => data.industry_averages?.[k] ?? 0);
      }

      this.render();
    } catch (err) {
      console.error('RadarChart: Failed to fetch stats', err);
    }
  }

  /** チャートを破棄してイベントリスナーを削除 */
  destroy() {
    window.removeEventListener('resize', this._resizeHandler);
    if (this._chartInstance) {
      this._chartInstance.destroy();
      this._chartInstance = null;
    }
  }

  // ──────────────────────────────────────────
  // Private helpers
  // ──────────────────────────────────────────

  _renderRadarChart(container) {
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-label', '企業評価レーダーチャート');
    container.appendChild(canvas);

    const datasets = [
      {
        label: this.companyName,
        data: this.companyScores,
        borderColor: RadarChart.COLOR_COMPANY,
        backgroundColor: RadarChart.COLOR_COMPANY_FILL,
        borderWidth: 2,
        pointBackgroundColor: RadarChart.COLOR_COMPANY,
        pointRadius: 4,
      },
    ];

    if (this.industryAverages) {
      datasets.push({
        label: '業界平均 (average)',
        data: this.industryAverages,
        borderColor: RadarChart.COLOR_INDUSTRY,
        backgroundColor: RadarChart.COLOR_INDUSTRY_FILL,
        borderWidth: 1.5,
        borderDash: [5, 5],
        pointBackgroundColor: RadarChart.COLOR_INDUSTRY,
        pointRadius: 3,
      });
    }

    if (typeof Chart !== 'undefined') {
      this._chartInstance = new Chart(canvas, {
        type: 'radar',
        data: {
          labels: this.labels,
          datasets,
        },
        options: {
          responsive: true,
          scales: {
            r: {
              min: 0,
              max: 5,
              ticks: { stepSize: 1, font: { size: 11 } },
              pointLabels: { font: { size: 12 } },
            },
          },
          plugins: {
            legend: { position: 'bottom' },
          },
        },
      });
    } else {
      // Chart.js が未ロードの場合のフォールバック（テスト・SSR環境）
      this._renderFallbackTable(container);
    }
  }

  _renderBarChart(container) {
    // モバイル用棒グラフ（横棒）
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-label', '企業評価棒グラフ');
    container.appendChild(canvas);

    const shortLabels = [
      '待遇', 'WLB', '文化', 'キャリア',
      'マネジメント', '評価', '環境', '事業',
    ];

    const datasets = [
      {
        label: this.companyName,
        data: this.companyScores,
        backgroundColor: RadarChart.COLOR_COMPANY_FILL,
        borderColor: RadarChart.COLOR_COMPANY,
        borderWidth: 2,
      },
    ];

    if (this.industryAverages) {
      datasets.push({
        label: '業界平均',
        data: this.industryAverages,
        backgroundColor: RadarChart.COLOR_INDUSTRY_FILL,
        borderColor: RadarChart.COLOR_INDUSTRY,
        borderWidth: 1.5,
      });
    }

    if (typeof Chart !== 'undefined') {
      this._chartInstance = new Chart(canvas, {
        type: 'bar',
        data: { labels: shortLabels, datasets },
        options: {
          indexAxis: 'y',
          responsive: true,
          scales: { x: { min: 0, max: 5 } },
          plugins: { legend: { position: 'bottom' } },
        },
      });
    } else {
      this._renderFallbackTable(container);
    }
  }

  _renderFallbackTable(container) {
    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';

    const shortLabels = [
      '待遇・報酬', 'ワークライフ', '企業文化', 'キャリア',
      'マネジメント', '評価制度', '職場環境', '事業・製品',
    ];

    shortLabels.forEach((label, i) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="padding:4px 8px;font-size:13px">${label}</td>
        <td style="padding:4px 8px;font-size:13px;font-weight:bold">
          ${(this.companyScores[i] || 0).toFixed(1)}
        </td>
      `;
      table.appendChild(tr);
    });

    container.appendChild(table);
  }

  _handleResize() {
    const nowMobile = window.innerWidth < RadarChart.MOBILE_BREAKPOINT;
    if (nowMobile !== this._isMobile) {
      this._isMobile = nowMobile;
      this.render();
    }
  }
}

// ──────────────────────────────────────────
// Auto-init: data-radar-chart 属性があるコンテナを自動初期化
// ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-radar-chart]').forEach((el) => {
    const companyId = el.dataset.companyId;
    if (!companyId) return;

    const chart = new RadarChart(el.id, {
      companyName: el.dataset.companyName || '企業スコア',
    });
    chart.initialize(companyId);
  });
});
