"""
翻訳サービス - DeepSeek API統合
レビューテキストの多言語翻訳を提供
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from ..utils.result import Result

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """翻訳エラーの基底クラス"""

    pass


class APIRateLimitError(TranslationError):
    """APIレート制限エラー"""

    pass


class APITimeoutError(TranslationError):
    """APIタイムアウトエラー"""

    pass


class TranslationService:
    """DeepSeek APIを使用した翻訳サービス"""

    # サポート言語
    SUPPORTED_LANGUAGES = {"ja": "日本語", "en": "英語", "zh": "中国語", "ko": "韓国語"}

    # DeepSeek API設定
    API_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_TIMEOUT = 30  # 秒
    MAX_RETRIES = 2

    def __init__(self, api_key: Optional[str] = None):
        """
        TranslationServiceの初期化

        Args:
            api_key: DeepSeek APIキー（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")

        self.client = httpx.AsyncClient(
            base_url=self.API_BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=self.DEFAULT_TIMEOUT,
        )

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None
    ) -> Result[str, TranslationError]:
        """
        テキストを翻訳

        Args:
            text: 翻訳するテキスト
            source_lang: 元言語コード（例: 'ja', 'en'）
            target_lang: 翻訳先言語コード（例: 'ja', 'en'）
            context: 翻訳のコンテキスト（例: 'company review'）

        Returns:
            Result[str, TranslationError]: 翻訳されたテキストまたはエラー
        """
        try:
            # 言語コードの検証
            if source_lang not in self.SUPPORTED_LANGUAGES:
                return Result.failure(
                    TranslationError(f"Unsupported source language: {source_lang}")
                )
            if target_lang not in self.SUPPORTED_LANGUAGES:
                return Result.failure(
                    TranslationError(f"Unsupported target language: {target_lang}")
                )

            # 同じ言語の場合は翻訳不要
            if source_lang == target_lang:
                return Result.success(text)

            # 空テキストの処理
            if not text or not text.strip():
                return Result.success("")

            # プロンプトの構築
            prompt = self._build_translation_prompt(text, source_lang, target_lang, context)

            # DeepSeek APIリクエスト
            response = await self._call_deepseek_api(prompt)

            if not response.is_success:
                return Result.failure(response.error)

            translated_text = response.data.get("translated_text", "")
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

        Args:
            texts: 翻訳するテキストのリスト
            source_lang: 元言語コード
            target_lang: 翻訳先言語コード
            context: 翻訳のコンテキスト

        Returns:
            Result[List[str], TranslationError]: 翻訳されたテキストのリストまたはエラー
        """
        try:
            if not texts:
                return Result.success([])

            # 各テキストを個別に翻訳（DeepSeek APIはバッチをサポートしていないため）
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

    def _build_translation_prompt(
        self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None
    ) -> str:
        """翻訳プロンプトを構築"""
        source_name = self.SUPPORTED_LANGUAGES.get(source_lang, source_lang)
        target_name = self.SUPPORTED_LANGUAGES.get(target_lang, target_lang)

        context_instruction = ""
        if context:
            context_instruction = f"\n\nContext: This is a {context}."

        prompt = f"""Translate the following text from {source_name} to {target_name}.
Please provide ONLY the translated text without any explanations or additional comments.{context_instruction}

Text to translate:
{text}

Translation:"""

        return prompt

    async def _call_deepseek_api(
        self, prompt: str, retry_count: int = 0
    ) -> Result[Dict[str, Any], TranslationError]:
        """
        DeepSeek APIを呼び出し

        Args:
            prompt: APIに送信するプロンプト
            retry_count: リトライ回数

        Returns:
            Result[Dict[str, Any], TranslationError]: API応答またはエラー
        """
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,  # 一貫性のある翻訳のため低めに設定
                    "max_tokens": 2000,
                },
            )

            # ステータスコードの確認
            if response.status_code == 429:
                # レート制限エラー
                logger.warning("DeepSeek API rate limit exceeded")
                return Result.failure(APIRateLimitError("API rate limit exceeded"))

            if response.status_code == 504 or response.status_code == 408:
                # タイムアウトエラー
                logger.warning("DeepSeek API timeout")
                if retry_count < self.MAX_RETRIES:
                    logger.info("Retrying API call (%d/%d)", retry_count + 1, self.MAX_RETRIES)
                    return await self._call_deepseek_api(prompt, retry_count + 1)
                return Result.failure(APITimeoutError("API timeout after retries"))

            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return Result.failure(TranslationError(error_msg))

            # レスポンスのパース
            data = response.json()
            if "choices" not in data or not data["choices"]:
                return Result.failure(TranslationError("Invalid API response format"))

            translated_text = data["choices"][0]["message"]["content"].strip()

            return Result.success(
                {
                    "translated_text": translated_text,
                    "model": data.get("model", self.DEFAULT_MODEL),
                    "usage": data.get("usage", {}),
                }
            )

        except httpx.TimeoutException as e:
            logger.warning("DeepSeek API request timeout: %s", e)
            if retry_count < self.MAX_RETRIES:
                logger.info("Retrying API call (%d/%d)", retry_count + 1, self.MAX_RETRIES)
                return await self._call_deepseek_api(prompt, retry_count + 1)
            return Result.failure(APITimeoutError(f"API timeout after retries: {str(e)}"))

        except httpx.RequestError as e:
            logger.exception("DeepSeek API request error: %s", e)
            return Result.failure(TranslationError(f"API request error: {str(e)}"))

        except Exception as e:
            logger.exception("Unexpected error calling DeepSeek API: %s", e)
            return Result.failure(TranslationError(f"Unexpected API error: {str(e)}"))

    async def close(self):
        """HTTPクライアントをクローズ"""
        await self.client.aclose()

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリー"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.close()

    @classmethod
    def is_language_supported(cls, lang_code: str) -> bool:
        """
        言語コードがサポートされているか確認

        Args:
            lang_code: 言語コード（例: 'ja', 'en'）

        Returns:
            bool: サポートされている場合True
        """
        return lang_code in cls.SUPPORTED_LANGUAGES

    @classmethod
    def get_supported_languages(cls) -> Dict[str, str]:
        """
        サポートされている言語のリストを取得

        Returns:
            Dict[str, str]: 言語コードと言語名のマッピング
        """
        return cls.SUPPORTED_LANGUAGES.copy()
