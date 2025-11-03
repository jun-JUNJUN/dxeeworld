"""
翻訳サービス - DeepL API統合
レビューテキストの多言語翻訳を提供

DeepL Translation APIを使用して高品質な翻訳を実現。
サポート言語: 日本語(ja)、英語(en)、中国語(zh)
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from ..utils.result import Result

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """翻訳エラーの基底クラス"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class APIRateLimitError(TranslationError):
    """APIレート制限エラー (HTTPステータス429)"""

    pass


class APITimeoutError(TranslationError):
    """APIタイムアウトエラー (HTTPステータス504, 408, または httpx.TimeoutException)"""

    pass


class TranslationService:
    """DeepL APIを使用した翻訳サービス

    使用例:
        async with TranslationService() as service:
            result = await service.translate_text("こんにちは", "ja", "en")
            if result.is_success:
                print(result.data)  # "Hello"
    """

    # 言語コードマッピング (アプリケーション形式 -> DeepL API形式)
    LANGUAGE_CODE_MAPPING = {
        "ja": "JA",  # 日本語
        "en": "EN",  # 英語
        "zh": "ZH",  # 中国語
    }

    # DeepL API設定
    DEFAULT_BASE_URL = "https://api-free.deepl.com/v2"
    DEFAULT_TIMEOUT = 30  # 秒
    MAX_RETRIES = 2

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        TranslationServiceの初期化

        Args:
            api_key: DeepL APIキー（省略時は環境変数DEEPL_API_KEYから取得）
            base_url: DeepL API Base URL（省略時は環境変数DEEPL_API_BASE_URLまたはデフォルト値）

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        # APIキーの取得
        self.api_key = api_key or os.getenv("DEEPL_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPL_API_KEY is required")

        # Base URLの取得
        self.base_url = base_url or os.getenv("DEEPL_API_BASE_URL", self.DEFAULT_BASE_URL)

        # httpx.AsyncClientの作成
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.DEFAULT_TIMEOUT,
        )

    def _convert_to_deepl_lang_code(self, app_lang_code: str) -> str:
        """
        アプリケーション言語コードをDeepL API形式に変換

        Args:
            app_lang_code: アプリケーション言語コード (ja, en, zh)

        Returns:
            str: DeepL API形式の言語コード (JA, EN, ZH)

        Raises:
            KeyError: サポートされていない言語コードの場合
        """
        return self.LANGUAGE_CODE_MAPPING[app_lang_code]

    @classmethod
    def is_language_supported(cls, lang_code: str) -> bool:
        """
        言語コードがサポートされているか確認

        Args:
            lang_code: 言語コード (ja, en, zh)

        Returns:
            bool: サポートされている場合True
        """
        return lang_code in cls.LANGUAGE_CODE_MAPPING

    @classmethod
    def get_supported_languages(cls) -> Dict[str, str]:
        """
        サポートされている言語のマッピング辞書を取得

        Returns:
            Dict[str, str]: アプリケーション言語コード -> DeepL API言語コードのマッピング
        """
        return cls.LANGUAGE_CODE_MAPPING.copy()

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None
    ) -> Result[str, TranslationError]:
        """
        テキストを翻訳

        Args:
            text: 翻訳するテキスト
            source_lang: 元言語コード (ja, en, zh)
            target_lang: 翻訳先言語コード (ja, en, zh)
            context: 翻訳のコンテキスト（未使用）

        Returns:
            Result[str, TranslationError]: 翻訳されたテキストまたはエラー

        Examples:
            >>> result = await service.translate_text("こんにちは", "ja", "en")
            >>> if result.is_success:
            ...     print(result.data)  # "Hello"
        """
        try:
            # 言語コードの検証
            if not self.is_language_supported(source_lang):
                return Result.failure(TranslationError(f"Unsupported language: {source_lang}"))
            if not self.is_language_supported(target_lang):
                return Result.failure(TranslationError(f"Unsupported language: {target_lang}"))

            # 同じ言語の場合は翻訳不要
            if source_lang == target_lang:
                return Result.success(text)

            # 空テキストの処理
            if not text or not text.strip():
                return Result.success("")

            # 言語コードをDeepL形式に変換
            deepl_source = self._convert_to_deepl_lang_code(source_lang)
            deepl_target = self._convert_to_deepl_lang_code(target_lang)

            # DeepL APIリクエスト
            response = await self._call_deepl_api(
                text=[text], source_lang=deepl_source, target_lang=deepl_target
            )

            if not response.is_success:
                return Result.failure(response.error)

            translated_text = response.data
            logger.info(
                "Translation successful: %s -> %s (length: %d -> %d)",
                source_lang,
                target_lang,
                len(text),
                len(translated_text),
            )

            return Result.success(translated_text)

        except Exception as e:
            logger.exception("Translation failed: %s", e)
            return Result.failure(TranslationError(f"Translation failed: {str(e)}"))

    async def translate_batch(
        self, texts: List[str], source_lang: str, target_lang: str, context: Optional[str] = None
    ) -> Result[List[str], TranslationError]:
        """
        複数のテキストをバッチ翻訳

        個別の翻訳が失敗した場合、元のテキストを返すGraceful Degradationを実装。

        Args:
            texts: 翻訳するテキストのリスト
            source_lang: 元言語コード (ja, en, zh)
            target_lang: 翻訳先言語コード (ja, en, zh)
            context: 翻訳のコンテキスト（未使用）

        Returns:
            Result[List[str], TranslationError]: 翻訳されたテキストのリストまたはエラー

        Examples:
            >>> texts = ["こんにちは", "さようなら"]
            >>> result = await service.translate_batch(texts, "ja", "en")
            >>> if result.is_success:
            ...     print(result.data)  # ["Hello", "Goodbye"]
        """
        try:
            if not texts:
                return Result.success([])

            # 各テキストを個別に翻訳
            translated_texts = []
            for text in texts:
                result = await self.translate_text(text, source_lang, target_lang, context)
                if not result.is_success:
                    # エラー時は元のテキストを返す（Graceful Degradation）
                    logger.warning(
                        "Failed to translate text in batch, using original: %s", result.error
                    )
                    translated_texts.append(text)
                else:
                    translated_texts.append(result.data)

            return Result.success(translated_texts)

        except Exception as e:
            logger.exception("Batch translation failed: %s", e)
            return Result.failure(TranslationError(f"Batch translation failed: {str(e)}"))

    async def _call_deepl_api(
        self, text: List[str], source_lang: str, target_lang: str, retry_count: int = 0
    ) -> Result[str, TranslationError]:
        """
        DeepL APIを呼び出し、必要に応じてリトライ

        Args:
            text: 翻訳するテキストの配列
            source_lang: ソース言語コード (DeepL形式: JA, EN, ZH)
            target_lang: ターゲット言語コード (DeepL形式: JA, EN, ZH)
            retry_count: 現在のリトライ回数

        Returns:
            Result[str, TranslationError]: 翻訳されたテキストまたはエラー

        Retry Policy:
            - タイムアウト (504, 408, httpx.TimeoutException) 時のみリトライ
            - 最大リトライ回数: MAX_RETRIES (2回)
            - その他のエラーは即座に失敗を返す
        """
        try:
            response = await self.client.post(
                "/translate",
                json={"text": text, "source_lang": source_lang, "target_lang": target_lang},
            )

            # ステータスコードの確認
            if response.status_code == 429:
                # レート制限エラー
                logger.warning("DeepL API rate limit exceeded")
                return Result.failure(APIRateLimitError("API rate limit exceeded"))

            if response.status_code in (504, 408):
                # タイムアウトエラー
                logger.warning("DeepL API timeout (status: %d)", response.status_code)
                if retry_count < self.MAX_RETRIES:
                    logger.info("Retrying API call (%d/%d)", retry_count + 1, self.MAX_RETRIES)
                    return await self._call_deepl_api(
                        text, source_lang, target_lang, retry_count + 1
                    )
                return Result.failure(APITimeoutError("API timeout after retries"))

            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return Result.failure(TranslationError(error_msg))

            # レスポンスのパース
            data = response.json()
            if "translations" not in data or not data["translations"]:
                return Result.failure(TranslationError("Invalid API response format"))

            translated_text = data["translations"][0]["text"]

            return Result.success(translated_text)

        except httpx.TimeoutException as e:
            logger.warning("DeepL API request timeout: %s", e)
            if retry_count < self.MAX_RETRIES:
                logger.info("Retrying API call (%d/%d)", retry_count + 1, self.MAX_RETRIES)
                return await self._call_deepl_api(text, source_lang, target_lang, retry_count + 1)
            return Result.failure(APITimeoutError(f"API timeout after retries: {str(e)}"))

        except httpx.RequestError as e:
            logger.exception("DeepL API request error: %s", e)
            return Result.failure(TranslationError(f"API request error: {str(e)}"))

        except Exception as e:
            logger.exception("Unexpected error calling DeepL API: %s", e)
            return Result.failure(TranslationError(f"Unexpected API error: {str(e)}"))

    async def close(self) -> None:
        """HTTPクライアントをクローズしリソースを解放"""
        await self.client.aclose()

    async def __aenter__(self) -> "TranslationService":
        """非同期コンテキストマネージャーのエントリー"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """非同期コンテキストマネージャーの終了"""
        await self.close()
