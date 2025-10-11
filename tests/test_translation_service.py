"""
TranslationServiceのユニットテスト（Task 5.1, 5.2）
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.services.translation_service import TranslationService, TranslationError


class TestTranslationService:
    """TranslationServiceのテストクラス"""

    @pytest.mark.asyncio
    async def test_translate_from_japanese_to_other_languages(self):
        """日本語→英語+中国語の翻訳成功"""
        service = TranslationService()
        comment = "これは素晴らしい会社です。"

        # DeepSeek APIのモックレスポンス
        mock_response = {
            "success": True,
            "content": '{"en": "This is a wonderful company.", "zh": "这是一家很棒的公司。"}',
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
        }

        with patch.object(service, "call_deepseek_api", return_value=mock_response):
            result = await service.translate_to_other_languages(comment, "ja")

        assert result["success"] is True
        assert result["source_language"] == "ja"
        assert "en" in result["translations"]
        assert "zh" in result["translations"]
        assert "ja" not in result["translations"]  # 元言語は含まれない
        assert result["translations"]["en"] == "This is a wonderful company."
        assert result["translations"]["zh"] == "这是一家很棒的公司。"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_translate_from_chinese_to_other_languages(self):
        """中国語→英語+日本語の翻訳成功"""
        service = TranslationService()
        comment = "这是一家很棒的公司。"

        mock_response = {
            "success": True,
            "content": '{"en": "This is a wonderful company.", "ja": "これは素晴らしい会社です。"}',
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
        }

        with patch.object(service, "call_deepseek_api", return_value=mock_response):
            result = await service.translate_to_other_languages(comment, "zh")

        assert result["success"] is True
        assert result["source_language"] == "zh"
        assert "en" in result["translations"]
        assert "ja" in result["translations"]
        assert "zh" not in result["translations"]
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_translate_from_english_to_other_languages(self):
        """英語→日本語+中国語の翻訳成功"""
        service = TranslationService()
        comment = "This is a wonderful company."

        mock_response = {
            "success": True,
            "content": '{"ja": "これは素晴らしい会社です。", "zh": "这是一家很棒的公司。"}',
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
        }

        with patch.object(service, "call_deepseek_api", return_value=mock_response):
            result = await service.translate_to_other_languages(comment, "en")

        assert result["success"] is True
        assert result["source_language"] == "en"
        assert "ja" in result["translations"]
        assert "zh" in result["translations"]
        assert "en" not in result["translations"]
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_deepseek_api_failure_graceful_degradation(self):
        """DeepSeek API失敗時のGraceful Degradation（Task 5.2）"""
        service = TranslationService()
        comment = "This is a test."

        # API接続失敗をシミュレート
        mock_response = {"success": False, "error_message": "Connection timeout", "usage": None}

        with patch.object(service, "call_deepseek_api", return_value=mock_response):
            result = await service.translate_to_other_languages(comment, "en")

        # Graceful degradation: 翻訳失敗でもエラーを返す（投稿は継続可能）
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert result["translations"] == {}

    @pytest.mark.asyncio
    async def test_deepseek_api_json_parse_error(self):
        """DeepSeek APIの不正なJSON応答時のエラーハンドリング（Task 5.2）"""
        service = TranslationService()
        comment = "This is a test."

        # 不正なJSON応答をシミュレート
        mock_response = {
            "success": True,
            "content": "This is not valid JSON",
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
        }

        with patch.object(service, "call_deepseek_api", return_value=mock_response):
            result = await service.translate_to_other_languages(comment, "en")

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert (
            "JSON" in result["errors"][0]["error_message"]
            or "parse" in result["errors"][0]["error_message"].lower()
        )

    @pytest.mark.asyncio
    async def test_batch_translate_comments(self):
        """複数カテゴリーのコメント一括翻訳（Task 5.3）"""
        service = TranslationService()
        comments = {
            "recommendation": "強くお勧めします。",
            "company_culture": "素晴らしい文化です。",
            "evaluation_system": "公平な評価制度です。",
        }

        mock_response = {
            "success": True,
            "content": """
{
    "en": {
        "recommendation": "Highly recommend.",
        "company_culture": "Wonderful culture.",
        "evaluation_system": "Fair evaluation system."
    },
    "zh": {
        "recommendation": "强烈推荐。",
        "company_culture": "很棒的文化。",
        "evaluation_system": "公平的评估制度。"
    }
}
""",
            "usage": {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180},
        }

        with patch.object(service, "call_deepseek_api", return_value=mock_response):
            result = await service.batch_translate_comments(comments, "ja")

        assert result["success"] is True
        assert "en" in result["translated_comments"]
        assert "zh" in result["translated_comments"]
        assert "ja" not in result["translated_comments"]
        assert result["translated_comments"]["en"]["recommendation"] == "Highly recommend."
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_invalid_source_language(self):
        """無効な言語コードのバリデーション"""
        service = TranslationService()
        comment = "Test comment"

        result = await service.translate_to_other_languages(comment, "invalid")

        assert result["success"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_empty_comment_handling(self):
        """空コメントの処理"""
        service = TranslationService()
        comment = ""

        result = await service.translate_to_other_languages(comment, "en")

        # 空コメントはエラーまたは空の翻訳結果を返す
        assert result["success"] is False or result["translations"] == {}
