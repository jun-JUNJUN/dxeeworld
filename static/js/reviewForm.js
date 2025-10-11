/**
 * ReviewForm - レビュー投稿フォームの多言語対応と雇用期間バリデーション
 *
 * 機能:
 * - 多言語フォーム切り替え (英語・日本語・中国語)
 * - 雇用状態選択時の自動入力サポート
 * - 雇用期間バリデーション
 * - バリデーションエラー表示
 *
 * Requirements: 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
 */

class ReviewForm {
    /**
     * ReviewForm のコンストラクタ
     * @param {Object} translations - 多言語翻訳辞書
     */
    constructor(translations) {
        this.translations = translations;
        this.currentLanguage = 'ja'; // デフォルト言語
        this.errors = [];
    }

    /**
     * ブラウザ言語からデフォルト言語を検出
     * Requirements: 2.5
     * @returns {string} 言語コード ("en", "ja", "zh")
     */
    detectBrowserLanguage() {
        const browserLang = navigator.language || navigator.userLanguage;
        const langCode = browserLang.split('-')[0].toLowerCase();

        if (langCode === 'ja') return 'ja';
        if (langCode === 'zh') return 'zh';
        return 'en'; // デフォルトは英語
    }

    /**
     * フォーム言語を切り替え
     * Requirements: 2.3, 2.6, 2.7, 2.8
     * @param {string} languageCode - 言語コード ("en", "ja", "zh")
     */
    switchLanguage(languageCode) {
        if (!['en', 'ja', 'zh'].includes(languageCode)) {
            throw new Error(`Unsupported language: ${languageCode}`);
        }

        this.currentLanguage = languageCode;

        // ラベルを更新
        this._updateLabels(languageCode);

        // プレースホルダーを更新
        this._updatePlaceholders(languageCode);

        // ボタンを更新
        this._updateButtons(languageCode);
    }

    /**
     * ラベルを更新
     * @param {string} languageCode - 言語コード
     * @private
     */
    _updateLabels(languageCode) {
        const labels = this.translations.labels;
        document.querySelectorAll('[data-i18n-label]').forEach(element => {
            const key = element.getAttribute('data-i18n-label');
            if (labels[key] && labels[key][languageCode]) {
                element.textContent = labels[key][languageCode];
            }
        });
    }

    /**
     * プレースホルダーを更新
     * @param {string} languageCode - 言語コード
     * @private
     */
    _updatePlaceholders(languageCode) {
        const placeholders = this.translations.placeholders;
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            if (placeholders[key] && placeholders[key][languageCode]) {
                element.setAttribute('placeholder', placeholders[key][languageCode]);
            }
        });
    }

    /**
     * ボタンを更新
     * @param {string} languageCode - 言語コード
     * @private
     */
    _updateButtons(languageCode) {
        const buttons = this.translations.buttons;
        document.querySelectorAll('[data-i18n-button]').forEach(element => {
            const key = element.getAttribute('data-i18n-button');
            if (buttons[key] && buttons[key][languageCode]) {
                element.textContent = buttons[key][languageCode];
            }
        });
    }

    /**
     * 雇用状態選択時の自動入力サポート
     * Requirements: 6.1, 6.2, 6.3, 6.4
     * @param {string} employmentStatus - "current" または "former"
     * @param {HTMLSelectElement} endYearSelect - 終了年セレクト要素
     */
    handleEmploymentStatusChange(employmentStatus, endYearSelect) {
        if (employmentStatus === 'current') {
            // 現従業員: 終了年を「現在」に設定して無効化
            endYearSelect.value = 'present';
            endYearSelect.disabled = true;
        } else if (employmentStatus === 'former') {
            // 元従業員: 終了年フィールドを有効化
            if (endYearSelect.value === 'present') {
                endYearSelect.value = '';
            }
            endYearSelect.disabled = false;
        }
    }

    /**
     * 雇用期間のバリデーション
     * Requirements: 7.1, 7.2, 7.3, 7.6, 7.7
     * @param {Object} data - フォームデータ
     * @param {string} data.employmentStatus - "current" または "former"
     * @param {number|null} data.startYear - 開始年
     * @param {number|string|null} data.endYear - 終了年（"present" または数値）
     * @returns {Array<string>} バリデーションエラーの配列
     */
    validateEmploymentPeriod(data) {
        const errors = [];
        const currentYear = new Date().getFullYear();

        // 開始年の必須チェック
        if (!data.startYear) {
            errors.push('雇用開始年を入力してください');
        } else {
            // 開始年の範囲チェック
            const startYearInt = parseInt(data.startYear, 10);
            if (startYearInt < 1970) {
                errors.push('1970年以降の年を入力してください');
            } else if (startYearInt > currentYear) {
                errors.push('未来の年は入力できません');
            }
        }

        // 終了年のバリデーション
        if (data.employmentStatus === 'former') {
            // 元従業員の場合、終了年は必須
            if (!data.endYear || data.endYear === '') {
                errors.push('雇用終了年を入力してください');
            } else if (data.endYear !== 'present') {
                const endYearInt = parseInt(data.endYear, 10);

                // 終了年の範囲チェック
                if (endYearInt < 1970) {
                    errors.push('1970年以降の年を入力してください');
                } else if (endYearInt > currentYear) {
                    errors.push('未来の年は入力できません');
                }

                // 開始年と終了年の論理チェック
                const startYearInt = parseInt(data.startYear, 10);
                if (data.startYear && startYearInt > endYearInt) {
                    errors.push('開始年は終了年より前である必要があります');
                }
            }
        }

        return errors;
    }

    /**
     * バリデーションエラーを表示
     * Requirements: 7.4, 7.5
     * @param {Array<string>} errors - エラーメッセージの配列
     * @param {HTMLElement} container - エラー表示コンテナ
     */
    displayValidationErrors(errors, container) {
        // 既存のエラーをクリア
        container.innerHTML = '';

        if (errors.length === 0) {
            container.style.display = 'none';
            return;
        }

        // エラーメッセージを表示
        container.style.display = 'block';
        container.style.color = 'red';
        container.style.marginTop = '10px';

        const errorList = document.createElement('ul');
        errorList.style.paddingLeft = '20px';
        errorList.style.marginBottom = '0';

        errors.forEach(error => {
            const errorItem = document.createElement('li');
            errorItem.textContent = error;
            errorList.appendChild(errorItem);
        });

        container.appendChild(errorList);
    }

    /**
     * バリデーションエラーをクリア
     * @param {HTMLElement} container - エラー表示コンテナ
     */
    clearValidationErrors(container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }

    /**
     * フォーム送信時のバリデーション
     * Requirements: 7.4
     * @param {HTMLFormElement} form - フォーム要素
     * @param {HTMLElement} errorContainer - エラー表示コンテナ
     * @returns {boolean} バリデーション成功時true、失敗時false
     */
    validateOnSubmit(form, errorContainer) {
        const formData = new FormData(form);

        const data = {
            employmentStatus: formData.get('employment_status'),
            startYear: formData.get('employment_start_year'),
            endYear: formData.get('employment_end_year'),
        };

        const errors = this.validateEmploymentPeriod(data);

        if (errors.length > 0) {
            this.displayValidationErrors(errors, errorContainer);
            // エラーコンテナまでスクロール
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
        }

        this.clearValidationErrors(errorContainer);
        return true;
    }
}

// グローバルスコープに公開（テスト用）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReviewForm;
}
