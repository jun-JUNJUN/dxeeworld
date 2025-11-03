"""
TranslationService 統合テスト (Task 4: Integration Tests)

既存コンポーネントとの統合を検証:
- Task 4.1: ReviewHandlerとの統合
- Task 4.2: 環境変数読み込み統合
- Task 4.3: Result型互換性統合
"""

import pytest
import os
from unittest.mock import AsyncMock, patch, Mock
from src.services.translation_service import (
    TranslationService,
    TranslationError,
    APIRateLimitError,
)
from src.utils.result import Result


class TestReviewHandlerIntegration:
    """Task 4.1: ReviewHandlerとの統合テスト"""

    @pytest.mark.asyncio
    async def test_review_handler_can_initialize_translation_service(self):
        """
        ReviewHandlerがTranslationServiceを初期化できることを検証

        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            # ReviewHandlerのinitialize()メソッドと同様にインスタンス化
            translation_service = TranslationService()

            # TranslationServiceが正しく初期化されることを確認
            assert translation_service is not None
            assert translation_service.api_key == "test-key"
            assert hasattr(translation_service, "translate_text")
            assert hasattr(translation_service, "translate_batch")

    @pytest.mark.asyncio
    async def test_review_handler_translation_workflow(self):
        """
        ReviewHandlerの翻訳ワークフローをシミュレート

        レビュー投稿時の翻訳プロセス:
        1. ユーザーが日本語でレビューを入力
        2. 各カテゴリのコメントを英語と中国語に翻訳
        3. 翻訳結果をResult型で受け取る

        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            translation_service = TranslationService()

            # レビューコメント（複数カテゴリ）
            review_comments = {
                "salary": "給与水準は業界平均より高く、年次昇給もあります。",
                "benefits": "福利厚生が充実しており、リモートワークも可能です。",
                "career_growth": "キャリア成長の機会が豊富で、社内研修も充実しています。",
            }

            selected_language = "ja"  # ユーザーが選択した言語
            target_languages = ["en", "zh"]  # 翻訳先言語

            # モックレスポンス
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = Mock(
                return_value={
                    "translations": [
                        {"detected_source_language": "JA", "text": "Translated text"}
                    ]
                }
            )

            with patch.object(translation_service.client, "post", return_value=mock_response):
                # 各カテゴリのコメントを各言語に翻訳（ReviewHandlerのロジック）
                translated_comments_all = {}
                for target_lang in target_languages:
                    translated_comments_all[target_lang] = {}
                    for category, comment in review_comments.items():
                        if comment:
                            translation_result = await translation_service.translate_text(
                                text=comment,
                                source_lang=selected_language,
                                target_lang=target_lang,
                                context="company review",
                            )

                            # Result型の互換性を検証
                            assert hasattr(translation_result, "is_success")
                            assert hasattr(translation_result, "data")
                            assert hasattr(translation_result, "error")

                            if translation_result.is_success:
                                translated_comments_all[target_lang][category] = (
                                    translation_result.data
                                )
                            else:
                                translated_comments_all[target_lang][category] = None

            # 翻訳結果の構造を検証
            assert "en" in translated_comments_all
            assert "zh" in translated_comments_all
            assert "salary" in translated_comments_all["en"]
            assert "benefits" in translated_comments_all["en"]
            assert "career_growth" in translated_comments_all["en"]

    @pytest.mark.asyncio
    async def test_review_handler_graceful_degradation_on_translation_failure(self):
        """
        ReviewHandlerの翻訳失敗時のGraceful Degradationを検証

        一部の翻訳が失敗しても、他の翻訳は正常に処理される

        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            translation_service = TranslationService()

            review_comments = {
                "salary": "給与について",
                "benefits": "福利厚生について",
                "career_growth": "キャリアについて",
            }

            # 2番目の翻訳だけ失敗するようにモック設定
            mock_responses = [
                AsyncMock(
                    status_code=200,
                    json=Mock(
                        return_value={
                            "translations": [
                                {"detected_source_language": "JA", "text": "About salary"}
                            ]
                        }
                    ),
                ),
                AsyncMock(status_code=429),  # レート制限エラー
                AsyncMock(
                    status_code=200,
                    json=Mock(
                        return_value={
                            "translations": [
                                {"detected_source_language": "JA", "text": "About career"}
                            ]
                        }
                    ),
                ),
            ]

            with patch.object(translation_service.client, "post", side_effect=mock_responses):
                translated_comments = {}
                for category, comment in review_comments.items():
                    if comment:
                        translation_result = await translation_service.translate_text(
                            text=comment, source_lang="ja", target_lang="en"
                        )

                        if translation_result.is_success:
                            translated_comments[category] = translation_result.data
                        else:
                            # 翻訳失敗時は元のテキストを使用（Graceful Degradation）
                            translated_comments[category] = f"[翻訳失敗] {comment}"

            # 1番目と3番目は翻訳成功、2番目は失敗
            assert translated_comments["salary"] == "About salary"
            assert "[翻訳失敗]" in translated_comments["benefits"]
            assert translated_comments["career_growth"] == "About career"

    @pytest.mark.asyncio
    async def test_review_handler_batch_translation_workflow(self):
        """
        ReviewHandlerでのバッチ翻訳ワークフローを検証

        複数カテゴリのコメントを一度に翻訳

        Requirements: 6.1, 6.3, 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            translation_service = TranslationService()

            comment_texts = [
                "給与水準について",
                "福利厚生について",
                "キャリア成長について",
            ]

            # translate_textをモック（translate_batchが内部で使用）
            mock_results = [
                Mock(is_success=True, data="About salary"),
                Mock(is_success=True, data="About benefits"),
                Mock(is_success=True, data="About career"),
            ]

            with patch.object(translation_service, "translate_text", side_effect=mock_results):
                result = await translation_service.translate_batch(
                    comment_texts, source_lang="ja", target_lang="en"
                )

            # Result型の互換性を検証
            assert result.is_success
            assert isinstance(result.data, list)
            assert len(result.data) == 3
            assert result.data[0] == "About salary"
            assert result.data[1] == "About benefits"
            assert result.data[2] == "About career"


class TestEnvironmentVariableIntegration:
    """Task 4.2: 環境変数読み込み統合テスト"""

    def test_deepl_api_key_loads_from_env_file(self):
        """
        .envファイルからDEEPL_API_KEYが正しく読み込まれることを検証

        Requirements: 7.1, 7.4, 7.5
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "env-test-key-abc123"}):
            service = TranslationService()

            assert service.api_key == "env-test-key-abc123"

    def test_deepl_api_base_url_loads_from_env_file(self):
        """
        .envファイルからDEEPL_API_BASE_URLが正しく読み込まれることを検証

        Requirements: 7.4, 7.5
        """
        with patch.dict(
            os.environ,
            {
                "DEEPL_API_KEY": "test-key",
                "DEEPL_API_BASE_URL": "https://api.deepl.com/v2",
            },
        ):
            service = TranslationService()

            assert service.base_url == "https://api.deepl.com/v2"

    def test_default_base_url_when_env_not_set(self):
        """
        DEEPL_API_BASE_URLが未設定の場合、デフォルトURLを使用

        Requirements: 7.5
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            # DEEPL_API_BASE_URLが環境変数に存在しない場合
            if "DEEPL_API_BASE_URL" in os.environ:
                del os.environ["DEEPL_API_BASE_URL"]

            service = TranslationService()

            # デフォルトでフリープランのエンドポイントを使用
            assert service.base_url == "https://api-free.deepl.com/v2"

    def test_translation_service_initializes_with_env_config(self):
        """
        TranslationServiceが環境変数設定で正しく初期化される

        Requirements: 7.1, 7.4, 7.5
        """
        with patch.dict(
            os.environ,
            {
                "DEEPL_API_KEY": "production-key-xyz789",
                "DEEPL_API_BASE_URL": "https://api.deepl.com/v2",
            },
        ):
            service = TranslationService()

            # 初期化成功
            assert service.api_key == "production-key-xyz789"
            assert service.base_url == "https://api.deepl.com/v2"
            assert service.client is not None

            # 認証ヘッダーが正しく設定されている
            assert "Authorization" in service.client.headers
            assert service.client.headers["Authorization"] == "DeepL-Auth-Key production-key-xyz789"

    def test_api_key_missing_raises_value_error(self):
        """
        DEEPL_API_KEYが未設定の場合、ValueErrorが発生

        Requirements: 7.1
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DEEPL_API_KEY is required"):
                TranslationService()


class TestResultTypeCompatibility:
    """Task 4.3: Result型互換性統合テスト"""

    @pytest.mark.asyncio
    async def test_result_success_has_is_success_property(self):
        """
        Result.successオブジェクトがis_successプロパティを持つ

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # 同一言語翻訳（API呼び出しなし）でResult.successを返す
            result = await service.translate_text("Test", "en", "en")

            # Result型の互換性を検証
            assert hasattr(result, "is_success")
            assert result.is_success is True

    @pytest.mark.asyncio
    async def test_result_success_has_data_property(self):
        """
        Result.successオブジェクトがdataプロパティを持ち、翻訳結果を返す

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("Test", "en", "en")

            assert hasattr(result, "data")
            assert result.data == "Test"

    @pytest.mark.asyncio
    async def test_result_failure_has_is_success_property(self):
        """
        Result.failureオブジェクトがis_successプロパティを持つ

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # サポート外言語でResult.failureを返す
            result = await service.translate_text("Test", "ko", "en")

            assert hasattr(result, "is_success")
            assert result.is_success is False

    @pytest.mark.asyncio
    async def test_result_failure_has_error_property(self):
        """
        Result.failureオブジェクトがerrorプロパティを持ち、エラーオブジェクトを返す

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("Test", "ko", "en")

            assert hasattr(result, "error")
            assert isinstance(result.error, TranslationError)
            assert "Unsupported language" in str(result.error)

    @pytest.mark.asyncio
    async def test_result_type_is_compatible_with_existing_code(self):
        """
        Result型が既存のコードパターンと互換性がある

        既存のコードでの使用パターン:
        if result.is_success:
            translated_text = result.data
        else:
            error_message = result.error

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # 成功ケース
            success_result = await service.translate_text("Hello", "en", "en")
            if success_result.is_success:
                translated_text = success_result.data
                assert translated_text == "Hello"

            # 失敗ケース
            failure_result = await service.translate_text("Test", "invalid", "en")
            if not failure_result.is_success:
                error = failure_result.error
                assert isinstance(error, TranslationError)

    @pytest.mark.asyncio
    async def test_result_type_works_with_batch_translation(self):
        """
        Result型がバッチ翻訳でも正しく動作する

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # translate_textをモック
            mock_results = [
                Mock(is_success=True, data="Text 1"),
                Mock(is_success=True, data="Text 2"),
            ]

            with patch.object(service, "translate_text", side_effect=mock_results):
                result = await service.translate_batch(["テキスト1", "テキスト2"], "ja", "en")

            # Result型の互換性を検証
            assert result.is_success
            assert isinstance(result.data, list)
            assert len(result.data) == 2

    @pytest.mark.asyncio
    async def test_result_error_types_are_distinguishable(self):
        """
        Result型のエラーが型によって識別可能

        Requirements: 6.4
        """
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # レート制限エラー
            mock_response = AsyncMock(status_code=429)
            with patch.object(service.client, "post", return_value=mock_response):
                result = await service.translate_text("Test", "ja", "en")

            assert not result.is_success
            assert isinstance(result.error, APIRateLimitError)
            assert isinstance(result.error, TranslationError)  # 継承関係も検証
