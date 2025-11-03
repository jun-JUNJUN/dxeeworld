"""
TranslationService (DeepL API統合) のユニットテスト

TDD方式でDeepL API統合機能をテスト
"""

import pytest
import os
from unittest.mock import AsyncMock, patch, Mock
from src.services.translation_service import (
    TranslationService,
    TranslationError,
    APIRateLimitError,
    APITimeoutError,
)


class TestTranslationServiceInitialization:
    """Task 2.1: TranslationService初期化と設定管理のテスト"""

    def test_init_with_api_key_from_environment(self):
        """環境変数からAPIキーを正しく読み込む"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-api-key-123"}):
            service = TranslationService()
            assert service.api_key == "test-api-key-123"

    def test_init_with_explicit_api_key(self):
        """明示的に渡されたAPIキーを使用する"""
        service = TranslationService(api_key="explicit-key-456")
        assert service.api_key == "explicit-key-456"

    def test_init_raises_error_when_api_key_missing(self):
        """APIキーが設定されていない場合はValueErrorを発生"""
        with patch.dict(os.environ, {}, clear=True):
            # DEEPL_API_KEYが存在しない環境でValueErrorが発生することを確認
            with pytest.raises(ValueError, match="DEEPL_API_KEY is required"):
                TranslationService()

    def test_init_sets_default_base_url(self):
        """デフォルトでフリープランのBase URLを使用"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()
            assert service.base_url == "https://api-free.deepl.com/v2"

    def test_init_sets_base_url_from_environment(self):
        """環境変数からBase URLを読み込む"""
        with patch.dict(
            os.environ,
            {
                "DEEPL_API_KEY": "test-key",
                "DEEPL_API_BASE_URL": "https://api.deepl.com/v2",
            },
        ):
            service = TranslationService()
            assert service.base_url == "https://api.deepl.com/v2"

    def test_init_creates_async_client_with_auth_header(self):
        """httpx.AsyncClientが認証ヘッダー付きで作成される"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key-789"}):
            service = TranslationService()
            # クライアントが作成されていることを確認
            assert service.client is not None
            # 認証ヘッダーが設定されていることを確認
            assert "Authorization" in service.client.headers
            assert service.client.headers["Authorization"] == "DeepL-Auth-Key test-key-789"

    def test_init_sets_timeout_to_30_seconds(self):
        """タイムアウトが30秒に設定される"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()
            # httpx.AsyncClientのタイムアウト設定を確認
            assert service.client.timeout.read == 30.0


class TestLanguageCodeConversion:
    """Task 2.2: 言語コード変換と検証機能のテスト"""

    def test_language_code_mapping_defined(self):
        """言語コードマッピング辞書が定義されている"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()
            assert hasattr(service, "LANGUAGE_CODE_MAPPING")
            assert service.LANGUAGE_CODE_MAPPING["ja"] == "JA"
            assert service.LANGUAGE_CODE_MAPPING["en"] == "EN"
            assert service.LANGUAGE_CODE_MAPPING["zh"] == "ZH"

    def test_convert_to_deepl_lang_code_success(self):
        """アプリケーション言語コードをDeepL形式に変換"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()
            assert service._convert_to_deepl_lang_code("ja") == "JA"
            assert service._convert_to_deepl_lang_code("en") == "EN"
            assert service._convert_to_deepl_lang_code("zh") == "ZH"

    def test_convert_to_deepl_lang_code_unsupported(self):
        """サポート外の言語コードでKeyErrorを発生"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()
            with pytest.raises(KeyError):
                service._convert_to_deepl_lang_code("ko")

    def test_is_language_supported(self):
        """is_language_supported()が正しく判定"""
        assert TranslationService.is_language_supported("ja") is True
        assert TranslationService.is_language_supported("en") is True
        assert TranslationService.is_language_supported("zh") is True
        assert TranslationService.is_language_supported("ko") is False
        assert TranslationService.is_language_supported("invalid") is False

    def test_get_supported_languages(self):
        """get_supported_languages()がマッピング辞書を返す"""
        languages = TranslationService.get_supported_languages()
        assert "ja" in languages
        assert "en" in languages
        assert "zh" in languages
        assert languages["ja"] == "JA"


class TestTranslateText:
    """Task 2.3: テキスト翻訳機能のテスト"""

    @pytest.mark.asyncio
    async def test_translate_text_success(self):
        """正常系: DeepL APIが正常なレスポンスを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # DeepL APIレスポンスをモック
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = Mock(
                return_value={
                    "translations": [{"detected_source_language": "JA", "text": "Hello, world!"}]
                }
            )

            with patch.object(service.client, "post", return_value=mock_response):
                result = await service.translate_text("こんにちは、世界！", "ja", "en")

            assert result.is_success
            assert result.data == "Hello, world!"

    @pytest.mark.asyncio
    async def test_translate_text_same_language_returns_original(self):
        """同一言語の場合、API呼び出しをスキップして元テキストを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("Hello", "en", "en")

            assert result.is_success
            assert result.data == "Hello"

    @pytest.mark.asyncio
    async def test_translate_text_empty_string_returns_empty(self):
        """空文字列入力の場合、空文字列を返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("", "ja", "en")

            assert result.is_success
            assert result.data == ""

    @pytest.mark.asyncio
    async def test_translate_text_whitespace_only_returns_empty(self):
        """空白のみの入力の場合、空文字列を返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("   ", "ja", "en")

            assert result.is_success
            assert result.data == ""

    @pytest.mark.asyncio
    async def test_translate_text_unsupported_source_language(self):
        """サポート外の元言語でエラーを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("Test", "ko", "en")

            assert not result.is_success
            assert isinstance(result.error, TranslationError)
            assert "Unsupported language" in str(result.error)

    @pytest.mark.asyncio
    async def test_translate_text_unsupported_target_language(self):
        """サポート外の翻訳先言語でエラーを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_text("Test", "en", "ko")

            assert not result.is_success
            assert isinstance(result.error, TranslationError)


class TestErrorHandlingAndRetry:
    """Task 2.4: エラーハンドリングとリトライロジックのテスト"""

    @pytest.mark.asyncio
    async def test_translate_text_rate_limit_error(self):
        """HTTPステータス429でAPIRateLimitErrorを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            mock_response = AsyncMock()
            mock_response.status_code = 429

            with patch.object(service.client, "post", return_value=mock_response):
                result = await service.translate_text("Test", "ja", "en")

            assert not result.is_success
            assert isinstance(result.error, APIRateLimitError)

    @pytest.mark.asyncio
    async def test_translate_text_timeout_with_retry(self):
        """HTTPステータス504でリトライが実行される"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # 最初の2回は504エラー、3回目は成功
            mock_response_success = AsyncMock()
            mock_response_success.status_code = 200
            mock_response_success.json = Mock(
                return_value={
                    "translations": [{"detected_source_language": "JA", "text": "Test"}]
                }
            )

            mock_responses = [
                AsyncMock(status_code=504),
                AsyncMock(status_code=504),
                mock_response_success,
            ]

            with patch.object(service.client, "post", side_effect=mock_responses):
                result = await service.translate_text("テスト", "ja", "en")

            # リトライ成功
            assert result.is_success
            assert result.data == "Test"

    @pytest.mark.asyncio
    async def test_translate_text_timeout_exceeds_max_retries(self):
        """リトライ上限到達でAPITimeoutErrorを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # 全てのリクエストが504エラー
            mock_response = AsyncMock(status_code=504)

            with patch.object(service.client, "post", return_value=mock_response):
                result = await service.translate_text("Test", "ja", "en")

            assert not result.is_success
            assert isinstance(result.error, APITimeoutError)

    @pytest.mark.asyncio
    async def test_translate_text_httpx_timeout_exception(self):
        """httpx.TimeoutExceptionでリトライが実行される"""
        import httpx

        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # 最初はTimeoutException、2回目は成功
            mock_response_success = AsyncMock()
            mock_response_success.status_code = 200
            mock_response_success.json = Mock(
                return_value={
                    "translations": [{"detected_source_language": "JA", "text": "Success"}]
                }
            )

            mock_responses = [
                httpx.TimeoutException("Request timeout"),
                mock_response_success,
            ]

            with patch.object(service.client, "post", side_effect=mock_responses):
                result = await service.translate_text("テスト", "ja", "en")

            # リトライ成功
            assert result.is_success
            assert result.data == "Success"


class TestBatchTranslation:
    """Task 2.5: バッチ翻訳機能のテスト"""

    @pytest.mark.asyncio
    async def test_translate_batch_empty_list(self):
        """空リスト入力で空リストを返す"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            result = await service.translate_batch([], "ja", "en")

            assert result.is_success
            assert result.data == []

    @pytest.mark.asyncio
    async def test_translate_batch_success(self):
        """複数テキストの正常翻訳"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # translate_textをモック
            mock_results = [
                Mock(is_success=True, data="Salary"),
                Mock(is_success=True, data="Benefits"),
                Mock(is_success=True, data="Career"),
            ]

            with patch.object(service, "translate_text", side_effect=mock_results):
                result = await service.translate_batch(["給与", "福利厚生", "キャリア"], "ja", "en")

            assert result.is_success
            assert len(result.data) == 3
            assert result.data == ["Salary", "Benefits", "Career"]

    @pytest.mark.asyncio
    async def test_translate_batch_graceful_degradation(self):
        """一部翻訳失敗時にGraceful Degradationが動作"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # 2番目の翻訳が失敗
            mock_results = [
                Mock(is_success=True, data="Salary"),
                Mock(is_success=False, error=TranslationError("API Error")),
                Mock(is_success=True, data="Career"),
            ]

            with patch.object(service, "translate_text", side_effect=mock_results):
                result = await service.translate_batch(["給与", "福利厚生", "キャリア"], "ja", "en")

            assert result.is_success
            assert len(result.data) == 3
            # 失敗したテキストは元テキストを返す
            assert result.data == ["Salary", "福利厚生", "Career"]

    @pytest.mark.asyncio
    async def test_translate_batch_result_length_matches_input(self):
        """結果リスト長が入力リスト長と同じ"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            mock_results = [Mock(is_success=True, data=f"Text{i}") for i in range(5)]

            with patch.object(service, "translate_text", side_effect=mock_results):
                result = await service.translate_batch(["T1", "T2", "T3", "T4", "T5"], "ja", "en")

            assert result.is_success
            assert len(result.data) == 5


class TestAsyncContextManager:
    """Task 2.6: 非同期コンテキストマネージャーのテスト"""

    @pytest.mark.asyncio
    async def test_context_manager_enters_successfully(self):
        """async withブロックで正しく動作"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            async with TranslationService() as service:
                assert service is not None
                assert service.client is not None

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self):
        """__aexit__後にHTTPクライアントが正しくクローズされる"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            # acloseMockを作成
            with patch.object(service.client, "aclose", new_callable=AsyncMock) as mock_aclose:
                async with service:
                    pass

                # aclosed
                mock_aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method_releases_resources(self):
        """close()メソッドが正しくリソースを解放"""
        with patch.dict(os.environ, {"DEEPL_API_KEY": "test-key"}):
            service = TranslationService()

            with patch.object(service.client, "aclose", new_callable=AsyncMock) as mock_aclose:
                await service.close()

                mock_aclose.assert_called_once()
