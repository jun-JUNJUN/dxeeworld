// ============================================
// Wizard Review Form - Multi-step Review Form
// Task 7: 8カテゴリー + 総合評価のウィザードフォーム
// ============================================

/**
 * スターレーティングコンポーネント
 * サイズ32px、5段階スター、ホバー/クリック対応
 */
class StarRating {
  constructor(container, fieldName, options = {}) {
    this.container = container;
    this.fieldName = fieldName;
    this.value = options.initialValue || null;
    this.maxStars = 5;
    this.onChange = options.onChange || null;

    this.render();
    this.bindEvents();
  }

  render() {
    this.container.innerHTML = '';
    this.container.classList.add('star-rating');

    const preview = document.createElement('span');
    preview.className = 'star-rating-preview';
    preview.style.cssText = 'margin-left: 8px; color: var(--color-text-secondary); font-size: 14px;';
    this.previewEl = preview;

    for (let i = 1; i <= this.maxStars; i++) {
      const star = document.createElement('span');
      star.className = 'star';
      star.dataset.value = i;
      star.setAttribute('role', 'button');
      star.setAttribute('tabindex', '0');
      star.setAttribute('aria-label', `${i}点`);
      star.style.cssText = `
        display: inline-block;
        width: 32px;
        height: 32px;
        font-size: 32px;
        cursor: pointer;
        color: ${this.value >= i ? '#FFB400' : '#D0D0D0'};
        transition: transform 0.2s;
        user-select: none;
        line-height: 1;
      `;
      star.textContent = '★';
      this.container.appendChild(star);
    }

    this.container.appendChild(preview);
    this.updatePreview(this.value);
  }

  updatePreview(hoverValue) {
    if (this.previewEl) {
      if (hoverValue !== null && hoverValue !== undefined) {
        this.previewEl.textContent = `${hoverValue} / ${this.maxStars}`;
      } else {
        this.previewEl.textContent = '';
      }
    }
  }

  updateStars(activeValue) {
    const stars = this.container.querySelectorAll('.star');
    stars.forEach((star, index) => {
      const starValue = index + 1;
      star.style.color = activeValue >= starValue ? '#FFB400' : '#D0D0D0';
    });
  }

  bindEvents() {
    const stars = this.container.querySelectorAll('.star');

    stars.forEach((star) => {
      // ホバーイベント
      star.addEventListener('mouseenter', () => {
        const hoverValue = parseInt(star.dataset.value);
        this.updateStars(hoverValue);
        this.updatePreview(hoverValue);
        star.style.transform = 'scale(1.1)';
      });

      star.addEventListener('mouseleave', () => {
        this.updateStars(this.value);
        this.updatePreview(this.value);
        star.style.transform = '';
      });

      // クリックで評価確定
      star.addEventListener('click', () => {
        this.value = parseInt(star.dataset.value);
        this.updateStars(this.value);
        this.updatePreview(this.value);
        if (this.onChange) {
          this.onChange(this.fieldName, this.value);
        }
      });

      // キーボード対応（矢印キー）
      star.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
          const newValue = Math.min(this.maxStars, (this.value || 0) + 1);
          this.value = newValue;
          this.updateStars(newValue);
          this.updatePreview(newValue);
          if (this.onChange) this.onChange(this.fieldName, newValue);
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
          const newValue = Math.max(1, (this.value || 1) - 1);
          this.value = newValue;
          this.updateStars(newValue);
          this.updatePreview(newValue);
          if (this.onChange) this.onChange(this.fieldName, newValue);
        } else if (e.key === 'Enter' || e.key === ' ') {
          this.value = parseInt(star.dataset.value);
          this.updateStars(this.value);
          this.updatePreview(this.value);
          if (this.onChange) this.onChange(this.fieldName, this.value);
        }
      });
    });
  }

  getValue() {
    return this.value;
  }

  setValue(val) {
    this.value = val;
    this.updateStars(val);
    this.updatePreview(val);
  }
}

/**
 * ReviewWizardForm クラス
 * 9ステップウィザードフォームの状態管理とUI制御
 */
class ReviewWizardForm {
  static TOTAL_STEPS = 9;
  static STORAGE_KEY = 'dxeeworld_review_wizard_data';

  // 8カテゴリー定義（ステップ1〜8）+ 総合評価（ステップ9）
  static STEPS = [
    {
      step: 1,
      category: 'comp',
      label: '待遇・報酬',
      fields: ['comp_salary', 'comp_bonus', 'comp_benefits'],
      ratingFields: ['comp_salary', 'comp_bonus', 'comp_benefits'],
      commentField: 'comp_comment',
      descriptions: {
        comp_salary: '給与水準',
        comp_bonus: '賞与・インセンティブ',
        comp_benefits: '福利厚生',
      }
    },
    {
      step: 2,
      category: 'wlb',
      label: 'ワークライフバランス',
      fields: ['wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall'],
      ratingFields: ['wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall'],
      commentField: 'wlb_comment',
      descriptions: {
        wlb_hours: '労働時間',
        wlb_vacation: '休暇取得',
        wlb_flexibility: '柔軟な働き方',
        wlb_overall: '総合評価',
      }
    },
    {
      step: 3,
      category: 'culture',
      label: '企業文化・風土',
      fields: ['culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication'],
      ratingFields: ['culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication'],
      commentField: 'culture_comment',
      descriptions: {
        culture_atmosphere: '社風・雰囲気',
        culture_diversity: '多様性・インクルージョン',
        culture_ethics: '倫理・コンプライアンス',
        culture_communication: '社内コミュニケーション',
      }
    },
    {
      step: 4,
      category: 'career',
      label: 'キャリア・成長',
      fields: ['career_growth', 'career_training', 'career_path', 'career_mentorship'],
      ratingFields: ['career_growth', 'career_training', 'career_path', 'career_mentorship'],
      commentField: 'career_comment',
      descriptions: {
        career_growth: '成長機会',
        career_training: '研修・教育制度',
        career_path: 'キャリアパス',
        career_mentorship: 'メンター制度',
      }
    },
    {
      step: 5,
      category: 'mgmt',
      label: 'マネジメント・組織',
      fields: ['mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager'],
      ratingFields: ['mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager'],
      commentField: 'mgmt_comment',
      descriptions: {
        mgmt_vision: '経営陣のビジョン',
        mgmt_decision: '意思決定プロセス',
        mgmt_structure: '組織体制',
        mgmt_manager: '直属上司の評価',
      }
    },
    {
      step: 6,
      category: 'perf',
      label: '評価・処遇制度',
      fields: ['perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage'],
      ratingFields: ['perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage'],
      commentField: 'perf_comment',
      descriptions: {
        perf_fairness: '評価制度の公平性',
        perf_feedback: '評価とフィードバック',
        perf_promotion: '昇進・昇格',
        perf_linkage: '報酬と評価の連動性',
      }
    },
    {
      step: 7,
      category: 'env',
      label: '職場環境',
      fields: ['env_office', 'env_relationships', 'env_stress', 'env_health'],
      ratingFields: ['env_office', 'env_relationships', 'env_stress', 'env_health'],
      commentField: 'env_comment',
      descriptions: {
        env_office: 'オフィス環境',
        env_relationships: '人間関係',
        env_stress: 'ストレスレベル',
        env_health: '健康管理・安全衛生',
      }
    },
    {
      step: 8,
      category: 'biz',
      label: '事業・製品',
      fields: ['biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial'],
      ratingFields: ['biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial'],
      commentField: 'biz_comment',
      descriptions: {
        biz_future: '事業の将来性',
        biz_pride: '製品・サービスへの誇り',
        biz_social_impact: '社会貢献度',
        biz_financial: '財務健全性',
      }
    },
    {
      step: 9,
      category: 'overall',
      label: '総合評価',
      fields: ['overall_satisfaction', 'overall_nps', 'employment_status', 'tenure', 'job_category'],
      ratingFields: ['overall_satisfaction'],
      commentField: 'overall_comment',
      descriptions: {
        overall_satisfaction: '総合満足度',
        overall_nps: '推薦意向（0-10）',
        employment_status: '在職状況',
        tenure: '在籍期間',
        job_category: '職種',
      }
    }
  ];

  constructor(formContainerId, companyId) {
    this.formContainer = document.getElementById(formContainerId);
    this.companyId = companyId;
    this.currentStep = 1;
    this.totalSteps = ReviewWizardForm.TOTAL_STEPS;
    this.formData = this._initFormData();
    this.starRatings = {};
    this.onStepChange = null;
    this.onValidationError = null;

    // localStorage から復元試行
    this.loadFromLocalStorage();
    // UI レンダリング
    this._render();
  }

  /**
   * フォームデータの初期化
   */
  _initFormData() {
    const data = {};
    ReviewWizardForm.STEPS.forEach(stepDef => {
      stepDef.ratingFields.forEach(field => {
        data[field] = null;
      });
      data[stepDef.commentField] = null;
    });
    // 総合評価の追加フィールド
    data['overall_nps'] = null;
    data['employment_status'] = null;
    data['tenure'] = null;
    data['job_category'] = null;
    return data;
  }

  /**
   * localStorage からデータを復元
   * @returns {boolean} 復元成功したかどうか
   */
  loadFromLocalStorage() {
    try {
      const saved = localStorage.getItem(ReviewWizardForm.STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.companyId === this.companyId) {
          this.formData = { ...this._initFormData(), ...parsed.formData };
          this.currentStep = parsed.currentStep || 1;
          return true;
        }
      }
    } catch (e) {
      console.warn('localStorage からの復元に失敗しました:', e);
    }
    return false;
  }

  /**
   * フォームデータを localStorage に保存
   */
  saveToLocalStorage() {
    try {
      const data = {
        companyId: this.companyId,
        currentStep: this.currentStep,
        formData: this.formData,
        savedAt: new Date().toISOString()
      };
      localStorage.setItem(ReviewWizardForm.STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      console.warn('localStorage への保存に失敗しました:', e);
    }
  }

  /**
   * localStorage のデータをクリア
   */
  clearLocalStorage() {
    localStorage.removeItem(ReviewWizardForm.STORAGE_KEY);
  }

  /**
   * 指定ステップのバリデーション
   * @param {number} step - 検証するステップ番号（1-9）
   * @returns {{valid: boolean, errors: Array<{field: string, message: string}>}}
   */
  validateStep(step) {
    const errors = [];
    const stepDef = ReviewWizardForm.STEPS.find(s => s.step === step);

    if (!stepDef) {
      return { valid: false, errors: [{ field: 'step', message: '無効なステップです' }] };
    }

    // レーティングフィールドのバリデーション
    stepDef.ratingFields.forEach(field => {
      const value = this.formData[field];
      if (value === null || value === undefined) {
        // オプショナルなので必須エラーはなし（overall_satisfaction は必須）
        if (field === 'overall_satisfaction') {
          errors.push({ field, message: `${stepDef.descriptions[field] || field}は必須です` });
        }
      } else {
        if (!Number.isInteger(value) || value < 1 || value > 5) {
          errors.push({ field, message: `${stepDef.descriptions[field] || field}は1から5の間で入力してください` });
        }
      }
    });

    // NPS バリデーション（ステップ9）
    if (step === 9) {
      const nps = this.formData['overall_nps'];
      if (nps !== null && nps !== undefined) {
        if (!Number.isInteger(nps) || nps < 0 || nps > 10) {
          errors.push({ field: 'overall_nps', message: 'NPS推薦意向は0から10の間で入力してください' });
        }
      }
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * 次のステップ番号を取得
   * @returns {number|null} 次のステップ番号（最終ステップの場合はnull）
   */
  getNextStep() {
    if (this.currentStep < this.totalSteps) {
      return this.currentStep + 1;
    }
    return null;
  }

  /**
   * 前のステップ番号を取得
   * @returns {number|null} 前のステップ番号（最初のステップの場合はnull）
   */
  getPreviousStep() {
    if (this.currentStep > 1) {
      return this.currentStep - 1;
    }
    return null;
  }

  /**
   * 次のステップへ進む
   */
  goToNextStep() {
    const validation = this.validateStep(this.currentStep);
    if (!validation.valid) {
      if (this.onValidationError) {
        this.onValidationError(validation.errors);
      }
      this._showValidationErrors(validation.errors);
      return false;
    }

    const next = this.getNextStep();
    if (next !== null) {
      this._collectCurrentStepData();
      this.currentStep = next;
      this.saveToLocalStorage();
      this._renderStep(this.currentStep);
      if (this.onStepChange) {
        this.onStepChange(this.currentStep);
      }
      return true;
    }
    return false;
  }

  /**
   * 前のステップに戻る
   */
  goToPreviousStep() {
    const prev = this.getPreviousStep();
    if (prev !== null) {
      this._collectCurrentStepData();
      this.currentStep = prev;
      this.saveToLocalStorage();
      this._renderStep(this.currentStep);
      if (this.onStepChange) {
        this.onStepChange(this.currentStep);
      }
      return true;
    }
    return false;
  }

  /**
   * 特定のステップに移動（確認画面からの編集用）
   * @param {number} targetStep
   */
  goToStep(targetStep) {
    if (targetStep >= 1 && targetStep <= this.totalSteps) {
      this.currentStep = targetStep;
      this._renderStep(this.currentStep);
      if (this.onStepChange) {
        this.onStepChange(this.currentStep);
      }
    }
  }

  /**
   * フォームを送信する
   * @returns {Promise<{success: boolean, reviewId?: string, error?: string}>}
   */
  async submitForm() {
    // 全ステップのバリデーション
    for (let step = 1; step <= this.totalSteps; step++) {
      const validation = this.validateStep(step);
      if (!validation.valid) {
        return {
          success: false,
          error: `ステップ${step}にエラーがあります: ${validation.errors.map(e => e.message).join(', ')}`
        };
      }
    }

    try {
      const response = await fetch(`/companies/${this.companyId}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this._getCsrfToken()
        },
        body: JSON.stringify(this.formData)
      });

      if (response.ok) {
        const data = await response.json();
        this.clearLocalStorage();
        return { success: true, reviewId: data.review_id };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.message || '送信に失敗しました' };
      }
    } catch (e) {
      return { success: false, error: 'ネットワークエラーが発生しました' };
    }
  }

  /**
   * CSRF トークンを取得
   * @returns {string}
   */
  _getCsrfToken() {
    const meta = document.querySelector('meta[name="_xsrf"]');
    return meta ? meta.getAttribute('content') : '';
  }

  /**
   * 現在のステップのデータをフォームから収集
   */
  _collectCurrentStepData() {
    const stepDef = ReviewWizardForm.STEPS.find(s => s.step === this.currentStep);
    if (!stepDef) return;

    // スターレーティングの値を収集
    stepDef.ratingFields.forEach(field => {
      if (this.starRatings[field]) {
        this.formData[field] = this.starRatings[field].getValue();
      }
    });

    // コメントフィールドの値を収集
    const commentEl = this.formContainer.querySelector(`[name="${stepDef.commentField}"]`);
    if (commentEl) {
      this.formData[stepDef.commentField] = commentEl.value || null;
    }

    // 総合評価ステップの特別フィールド
    if (this.currentStep === 9) {
      ['overall_nps', 'employment_status', 'tenure', 'job_category'].forEach(field => {
        const el = this.formContainer.querySelector(`[name="${field}"]`);
        if (el) {
          this.formData[field] = el.value || null;
          // NPS は数値に変換
          if (field === 'overall_nps' && el.value) {
            this.formData[field] = parseInt(el.value, 10);
          }
        }
      });
    }
  }

  /**
   * フォーム全体をレンダリング
   */
  _render() {
    if (!this.formContainer) return;

    this.formContainer.innerHTML = `
      <div class="wizard-form">
        <div class="wizard-progress" id="wizard-progress">
          ${this._renderProgressBar()}
        </div>
        <div class="wizard-step-content" id="wizard-step-content">
        </div>
        <div class="wizard-navigation" id="wizard-navigation">
        </div>
        <div class="wizard-errors" id="wizard-errors" style="display:none;">
        </div>
      </div>
    `;

    this._renderStep(this.currentStep);
  }

  /**
   * 進捗バーをレンダリング
   */
  _renderProgressBar() {
    const percent = Math.round((this.currentStep / this.totalSteps) * 100);
    return `
      <div class="progress-bar-container">
        <div class="progress-bar" style="width: ${percent}%; background: var(--color-primary, #20BEFF); height: 4px; transition: width 0.3s;"></div>
      </div>
      <div class="progress-steps">
        ${ReviewWizardForm.STEPS.map(s => `
          <span class="progress-step ${s.step === this.currentStep ? 'active' : s.step < this.currentStep ? 'completed' : ''}"
                data-step="${s.step}" title="${s.label}">
            ${s.step < this.currentStep ? '✓' : s.step}
          </span>
        `).join('')}
      </div>
      <div class="progress-label">ステップ ${this.currentStep} / ${this.totalSteps}: ${ReviewWizardForm.STEPS[this.currentStep - 1].label}</div>
    `;
  }

  /**
   * 指定ステップをレンダリング
   * @param {number} step
   */
  _renderStep(step) {
    if (!this.formContainer) return;

    // 進捗バー更新
    const progressEl = this.formContainer.querySelector('#wizard-progress');
    if (progressEl) {
      progressEl.innerHTML = this._renderProgressBar();
    }

    const contentEl = this.formContainer.querySelector('#wizard-step-content');
    const navEl = this.formContainer.querySelector('#wizard-navigation');
    if (!contentEl || !navEl) return;

    const stepDef = ReviewWizardForm.STEPS.find(s => s.step === step);
    if (!stepDef) return;

    // コンテンツレンダリング
    contentEl.innerHTML = this._renderStepContent(stepDef);

    // スターレーティングの初期化
    this.starRatings = {};
    stepDef.ratingFields.forEach(field => {
      const container = contentEl.querySelector(`[data-rating-field="${field}"]`);
      if (container) {
        this.starRatings[field] = new StarRating(container, field, {
          initialValue: this.formData[field],
          onChange: (fieldName, value) => {
            this.formData[fieldName] = value;
          }
        });
      }
    });

    // ナビゲーションボタンレンダリング
    navEl.innerHTML = this._renderNavigation(step);
    this._bindNavEvents();

    // エラーをクリア
    this._clearErrors();
  }

  /**
   * ステップのコンテンツHTML生成
   * @param {Object} stepDef
   * @returns {string}
   */
  _renderStepContent(stepDef) {
    if (stepDef.step === 9) {
      return this._renderOverallStep(stepDef);
    }
    return this._renderCategoryStep(stepDef);
  }

  /**
   * カテゴリーステップのHTML生成（ステップ1〜8）
   * @param {Object} stepDef
   * @returns {string}
   */
  _renderCategoryStep(stepDef) {
    const ratings = stepDef.ratingFields.map(field => `
      <div class="rating-item" style="margin-bottom: 20px;">
        <label style="display: block; margin-bottom: 8px; font-weight: 500;">
          ${stepDef.descriptions[field] || field}
        </label>
        <div data-rating-field="${field}" class="star-rating-container"></div>
      </div>
    `).join('');

    const commentValue = this.formData[stepDef.commentField] || '';

    return `
      <div class="step-content">
        <h3 style="margin-bottom: 24px; font-size: 20px; font-weight: 600; color: var(--color-text-primary);">
          ${stepDef.label}
        </h3>
        ${ratings}
        <div class="comment-item" style="margin-top: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;" for="comment-${stepDef.category}">
            コメント（任意、最大500文字）
          </label>
          <textarea
            id="comment-${stepDef.category}"
            name="${stepDef.commentField}"
            maxlength="500"
            rows="4"
            placeholder="${stepDef.label}についての詳細なコメントをご記入ください"
            style="width: 100%; padding: 12px; border: 1px solid var(--color-border); border-radius: 4px; font-size: 14px; resize: vertical;"
          >${commentValue}</textarea>
          <small style="color: var(--color-text-secondary);">
            <span id="comment-count-${stepDef.category}">${commentValue.length}</span>/500
          </small>
        </div>
      </div>
    `;
  }

  /**
   * 総合評価ステップのHTML生成（ステップ9）
   * @param {Object} stepDef
   * @returns {string}
   */
  _renderOverallStep(stepDef) {
    const npsValue = this.formData['overall_nps'];
    const statusValue = this.formData['employment_status'] || '';
    const tenureValue = this.formData['tenure'] || '';
    const jobCatValue = this.formData['job_category'] || '';
    const overallCommentValue = this.formData['overall_comment'] || '';

    const npsOptions = Array.from({ length: 11 }, (_, i) => `
      <option value="${i}" ${npsValue === i ? 'selected' : ''}>${i}</option>
    `).join('');

    return `
      <div class="step-content">
        <h3 style="margin-bottom: 24px; font-size: 20px; font-weight: 600; color: var(--color-text-primary);">
          総合評価
        </h3>

        <div class="rating-item" style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">
            総合満足度 <span style="color: #e00; font-size: 12px;">（必須）</span>
          </label>
          <div data-rating-field="overall_satisfaction" class="star-rating-container"></div>
        </div>

        <div class="form-item" style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;" for="overall-nps">
            推薦意向 NPS（0〜10） - この会社を友人や同僚に推薦しますか？
          </label>
          <select id="overall-nps" name="overall_nps"
            style="width: 100%; padding: 10px; border: 1px solid var(--color-border); border-radius: 4px;">
            <option value="">選択してください</option>
            ${npsOptions}
          </select>
        </div>

        <div class="form-item" style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;" for="employment-status">
            在職状況
          </label>
          <select id="employment-status" name="employment_status"
            style="width: 100%; padding: 10px; border: 1px solid var(--color-border); border-radius: 4px;">
            <option value="">選択してください</option>
            <option value="current" ${statusValue === 'current' ? 'selected' : ''}>現在在籍中</option>
            <option value="former" ${statusValue === 'former' ? 'selected' : ''}>退職済み</option>
          </select>
        </div>

        <div class="form-item" style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;" for="tenure">
            在籍期間
          </label>
          <select id="tenure" name="tenure"
            style="width: 100%; padding: 10px; border: 1px solid var(--color-border); border-radius: 4px;">
            <option value="">選択してください</option>
            <option value="6m_under" ${tenureValue === '6m_under' ? 'selected' : ''}>6ヶ月未満</option>
            <option value="6m_1y" ${tenureValue === '6m_1y' ? 'selected' : ''}>6ヶ月〜1年</option>
            <option value="1y_3y" ${tenureValue === '1y_3y' ? 'selected' : ''}>1〜3年</option>
            <option value="3y_5y" ${tenureValue === '3y_5y' ? 'selected' : ''}>3〜5年</option>
            <option value="5y_over" ${tenureValue === '5y_over' ? 'selected' : ''}>5年以上</option>
          </select>
        </div>

        <div class="form-item" style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;" for="job-category">
            職種
          </label>
          <select id="job-category" name="job_category"
            style="width: 100%; padding: 10px; border: 1px solid var(--color-border); border-radius: 4px;">
            <option value="">選択してください</option>
            <option value="engineer" ${jobCatValue === 'engineer' ? 'selected' : ''}>エンジニア</option>
            <option value="designer" ${jobCatValue === 'designer' ? 'selected' : ''}>デザイナー</option>
            <option value="pm" ${jobCatValue === 'pm' ? 'selected' : ''}>プロダクトマネージャー</option>
            <option value="marketing" ${jobCatValue === 'marketing' ? 'selected' : ''}>マーケティング</option>
            <option value="sales" ${jobCatValue === 'sales' ? 'selected' : ''}>営業</option>
            <option value="corporate" ${jobCatValue === 'corporate' ? 'selected' : ''}>コーポレート</option>
            <option value="other" ${jobCatValue === 'other' ? 'selected' : ''}>その他</option>
          </select>
        </div>

        <div class="comment-item" style="margin-top: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;" for="overall-comment">
            総合コメント（任意、最大1000文字）
          </label>
          <textarea
            id="overall-comment"
            name="overall_comment"
            maxlength="1000"
            rows="6"
            placeholder="総合的な感想をご記入ください"
            style="width: 100%; padding: 12px; border: 1px solid var(--color-border); border-radius: 4px; font-size: 14px; resize: vertical;"
          >${overallCommentValue}</textarea>
          <small style="color: var(--color-text-secondary);">
            <span id="overall-comment-count">${overallCommentValue.length}</span>/1000
          </small>
        </div>
      </div>
    `;
  }

  /**
   * ナビゲーションボタンのHTML生成
   * @param {number} step
   * @returns {string}
   */
  _renderNavigation(step) {
    const isFirst = step === 1;
    const isLast = step === this.totalSteps;

    return `
      <div class="nav-buttons" style="display: flex; justify-content: space-between; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--color-border);">
        <button type="button" id="btn-prev"
          class="btn btn-secondary"
          style="padding: 12px 24px; border: 1px solid var(--color-border); border-radius: 4px; background: white; cursor: pointer; ${isFirst ? 'visibility: hidden;' : ''}"
          ${isFirst ? 'disabled' : ''}
        >
          ← 戻る
        </button>
        <button type="button" id="btn-next"
          class="btn btn-primary"
          style="padding: 12px 32px; background: var(--color-primary, #20BEFF); color: white; border: none; border-radius: 4px; font-weight: 600; cursor: pointer;"
        >
          ${isLast ? '送信' : '次へ →'}
        </button>
      </div>
    `;
  }

  /**
   * ナビゲーションボタンのイベントをバインド
   */
  _bindNavEvents() {
    const btnPrev = this.formContainer.querySelector('#btn-prev');
    const btnNext = this.formContainer.querySelector('#btn-next');

    if (btnPrev) {
      btnPrev.addEventListener('click', () => this.goToPreviousStep());
    }

    if (btnNext) {
      if (this.currentStep === this.totalSteps) {
        btnNext.addEventListener('click', async () => {
          this._collectCurrentStepData();
          const result = await this.submitForm();
          if (result.success) {
            window.location.href = `/companies/${this.companyId}?review_submitted=1`;
          } else {
            this._showError(result.error || '送信に失敗しました');
          }
        });
      } else {
        btnNext.addEventListener('click', () => this.goToNextStep());
      }
    }
  }

  /**
   * バリデーションエラーを表示
   * @param {Array} errors
   */
  _showValidationErrors(errors) {
    const errorsEl = this.formContainer.querySelector('#wizard-errors');
    if (errorsEl) {
      errorsEl.innerHTML = errors.map(e => `
        <div class="error-item" style="color: #e00; padding: 8px; background: #fff5f5; border-radius: 4px; margin-bottom: 4px;">
          ⚠ ${e.message}
        </div>
      `).join('');
      errorsEl.style.display = 'block';
    }
  }

  /**
   * エラーメッセージを表示
   * @param {string} message
   */
  _showError(message) {
    const errorsEl = this.formContainer.querySelector('#wizard-errors');
    if (errorsEl) {
      errorsEl.innerHTML = `
        <div class="error-item" style="color: #e00; padding: 8px; background: #fff5f5; border-radius: 4px;">
          ⚠ ${message}
        </div>
      `;
      errorsEl.style.display = 'block';
    }
  }

  /**
   * エラー表示をクリア
   */
  _clearErrors() {
    const errorsEl = this.formContainer.querySelector('#wizard-errors');
    if (errorsEl) {
      errorsEl.innerHTML = '';
      errorsEl.style.display = 'none';
    }
  }
}

// DOMContentLoaded 後にウィザードを初期化
document.addEventListener('DOMContentLoaded', () => {
  const wizardContainer = document.getElementById('review-wizard-form');
  if (wizardContainer) {
    const companyId = wizardContainer.dataset.companyId;
    if (companyId) {
      window.reviewWizard = new ReviewWizardForm('review-wizard-form', companyId);
    }
  }
});
