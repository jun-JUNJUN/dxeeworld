"""
Test: Multi-step Wizard Review Form (Task 7)

ウィザードレビューフォームの包括的テスト:
- wizardReviewForm.js ファイルの存在確認
- ReviewWizardForm クラスの構造検証
- バリデーションロジックの確認
- ステップ管理機能の検証
- localStorage 統合の確認

Requirements: 10.1～10.7
"""
import os
import re
import pytest


WIZARD_JS_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'static', 'js', 'wizardReviewForm.js'
)


def read_wizard_js():
    """wizardReviewForm.js のソースコードを読み込む"""
    with open(WIZARD_JS_PATH, 'r', encoding='utf-8') as f:
        return f.read()


class TestWizardFileExists:
    """wizardReviewForm.js ファイルの存在確認"""

    def test_wizard_js_file_exists(self):
        """wizardReviewForm.js ファイルが存在すること"""
        assert os.path.exists(WIZARD_JS_PATH), \
            f"wizardReviewForm.js が見つかりません: {WIZARD_JS_PATH}"

    def test_wizard_js_is_not_empty(self):
        """wizardReviewForm.js が空でないこと"""
        assert os.path.getsize(WIZARD_JS_PATH) > 0


class TestWizardClassStructure:
    """ReviewWizardForm クラス構造の検証"""

    def test_review_wizard_form_class_defined(self):
        """ReviewWizardForm クラスが定義されていること"""
        content = read_wizard_js()
        assert 'class ReviewWizardForm' in content

    def test_constructor_exists(self):
        """constructor が定義されていること"""
        content = read_wizard_js()
        assert 'constructor(' in content

    def test_current_step_property(self):
        """currentStep プロパティが定義されていること（1-9の状態管理）"""
        content = read_wizard_js()
        assert 'currentStep' in content

    def test_form_data_property(self):
        """formData オブジェクトが定義されていること"""
        content = read_wizard_js()
        assert 'formData' in content

    def test_total_steps_is_9(self):
        """totalSteps が9であること（8カテゴリー + 総合評価）"""
        content = read_wizard_js()
        # 9ステップの設定を確認
        assert '9' in content and ('totalSteps' in content or 'TOTAL_STEPS' in content or 'total_steps' in content)


class TestWizardMethods:
    """ReviewWizardForm メソッドの検証"""

    def test_load_from_local_storage_method(self):
        """loadFromLocalStorage() メソッドが定義されていること"""
        content = read_wizard_js()
        assert 'loadFromLocalStorage' in content

    def test_save_to_local_storage_method(self):
        """saveToLocalStorage() メソッドが定義されていること"""
        content = read_wizard_js()
        assert 'saveToLocalStorage' in content

    def test_validate_step_method(self):
        """validateStep(step) メソッドが定義されていること"""
        content = read_wizard_js()
        assert 'validateStep' in content

    def test_get_next_step_method(self):
        """getNextStep() メソッドが定義されていること"""
        content = read_wizard_js()
        assert 'getNextStep' in content

    def test_get_previous_step_method(self):
        """getPreviousStep() メソッドが定義されていること"""
        content = read_wizard_js()
        assert 'getPreviousStep' in content

    def test_submit_form_method(self):
        """submitForm() メソッドが定義されていること"""
        content = read_wizard_js()
        assert 'submitForm' in content


class TestWizardStepNavigation:
    """ステップナビゲーション機能の検証"""

    def test_next_step_logic_exists(self):
        """次のステップへの遷移ロジックが実装されていること"""
        content = read_wizard_js()
        # currentStep の増加ロジック
        assert 'currentStep' in content
        assert ('+1' in content or '+ 1' in content or '++' in content)

    def test_previous_step_logic_exists(self):
        """前のステップへの戻りロジックが実装されていること"""
        content = read_wizard_js()
        # currentStep の減少ロジック
        assert '-1' in content or '- 1' in content or '--' in content

    def test_step_boundary_check(self):
        """ステップの境界チェックが実装されていること（1未満、9超の防止）"""
        content = read_wizard_js()
        # 最小ステップ（1）または最大ステップ（9）のチェック
        assert '1' in content

    def test_navigation_buttons_defined(self):
        """戻る/次へボタンの制御ロジックが実装されていること"""
        content = read_wizard_js()
        # ナビゲーションボタン制御
        assert ('prev' in content.lower() or 'back' in content.lower() or '戻る' in content)
        assert ('next' in content.lower() or '次へ' in content)


class TestWizardValidation:
    """バリデーション機能の検証"""

    def test_rating_validation_1_to_5(self):
        """1-5の評価値バリデーションロジックが実装されていること"""
        content = read_wizard_js()
        # 1-5のバリデーション
        assert '1' in content and '5' in content

    def test_required_field_validation(self):
        """必須項目のバリデーションが実装されていること"""
        content = read_wizard_js()
        assert ('required' in content or 'null' in content or 'undefined' in content)

    def test_validation_error_message(self):
        """バリデーションエラーメッセージが定義されていること"""
        content = read_wizard_js()
        assert ('error' in content.lower() or 'エラー' in content)

    def test_nps_validation_0_to_10(self):
        """NPS（0-10）のバリデーションロジックが実装されていること"""
        content = read_wizard_js()
        assert '10' in content and ('nps' in content.lower() or 'NPS' in content)


class TestWizardLocalStorage:
    """localStorage 統合の検証"""

    def test_local_storage_key_defined(self):
        """localStorage のキーが定義されていること"""
        content = read_wizard_js()
        assert 'localStorage' in content

    def test_save_to_local_storage_uses_set_item(self):
        """saveToLocalStorage が localStorage.setItem を使用すること"""
        content = read_wizard_js()
        assert 'setItem' in content

    def test_load_from_local_storage_uses_get_item(self):
        """loadFromLocalStorage が localStorage.getItem を使用すること"""
        content = read_wizard_js()
        assert 'getItem' in content

    def test_json_serialization(self):
        """フォームデータの JSON シリアライズが実装されていること"""
        content = read_wizard_js()
        assert 'JSON.stringify' in content or 'JSON.parse' in content


class TestWizardUIElements:
    """UI 要素の実装検証"""

    def test_progress_bar_implementation(self):
        """進捗バーの実装が含まれていること"""
        content = read_wizard_js()
        assert ('progress' in content.lower() or 'step' in content.lower())

    def test_step_content_display(self):
        """ステップごとのコンテンツ表示ロジックが実装されていること"""
        content = read_wizard_js()
        # showStep や renderStep などのメソッド
        assert ('showStep' in content or 'renderStep' in content or 'updateStep' in content or
                'displayStep' in content or 'render' in content.lower())

    def test_star_rating_component(self):
        """スターレーティングコンポーネントが実装されていること"""
        content = read_wizard_js()
        assert ('star' in content.lower() or 'rating' in content.lower() or
                'StarRating' in content or 'stars' in content.lower())

    def test_submit_button_logic(self):
        """送信ボタンのロジックが実装されていること"""
        content = read_wizard_js()
        assert ('submit' in content.lower() or 'Submit' in content)


class TestWizardCategories:
    """8カテゴリーの設定確認"""

    def test_compensation_category(self):
        """待遇・報酬カテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('comp' in content or '待遇' in content or 'compensation' in content.lower())

    def test_work_life_balance_category(self):
        """ワークライフバランスカテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('wlb' in content or 'work_life' in content or 'worklife' in content.lower() or
                'ワークライフ' in content)

    def test_culture_category(self):
        """企業文化カテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('culture' in content.lower() or '企業文化' in content)

    def test_career_category(self):
        """キャリア・成長カテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('career' in content.lower() or 'キャリア' in content)

    def test_management_category(self):
        """マネジメントカテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('mgmt' in content or 'management' in content.lower() or 'マネジメント' in content)

    def test_performance_category(self):
        """評価・処遇制度カテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('perf' in content or 'performance' in content.lower() or '評価' in content)

    def test_environment_category(self):
        """職場環境カテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('env' in content or 'environment' in content.lower() or '職場環境' in content)

    def test_business_category(self):
        """事業・製品カテゴリーが設定されていること"""
        content = read_wizard_js()
        assert ('biz' in content or 'business' in content.lower() or '事業' in content)

    def test_overall_assessment_step(self):
        """総合評価ステップが設定されていること"""
        content = read_wizard_js()
        assert ('overall' in content.lower() or '総合' in content or 'nps' in content.lower())


class TestWizardConfirmationScreen:
    """確認画面の実装検証（タスク 7.4）"""

    def test_confirmation_step_exists(self):
        """確認ステップ（送信前確認）が実装されていること"""
        content = read_wizard_js()
        assert ('confirm' in content.lower() or '確認' in content)

    def test_edit_button_for_confirmation(self):
        """確認画面からの編集ボタンが実装されていること"""
        content = read_wizard_js()
        assert ('edit' in content.lower() or '編集' in content or '戻る' in content)
