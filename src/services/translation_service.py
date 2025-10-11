"""
Translation Service using DeepSeek API
Task 5.1, 5.2: Translation service implementation and error handling
"""

import os
import json
import logging
import httpx
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """Translation service error"""

    pass


class TranslationService:
    """
    Translation service with DeepSeek API integration

    Requirements: 3.4, 4.3
    Design: LLM-based translation using DeepSeek Chat Completion API
    """

    def __init__(self):
        """Initialize translation service"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_endpoint = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        self.timeout = 30  # 30 second timeout (considering LLM response time)

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not set in environment variables")

    async def translate_to_other_languages(self, text: str, source_language: str) -> Dict[str, Any]:
        """
        Translate to the 2 languages other than the source language

        Args:
            text: Text to translate
            source_language: Source language code ("en", "ja", "zh")

        Returns:
            dict: {
                "success": bool,
                "source_language": str,
                "translations": {"ja"?: str, "zh"?: str, "en"?: str},
                "errors": [TranslationError]
            }
        """
        # Validation
        valid_languages = ["en", "ja", "zh"]
        if source_language not in valid_languages:
            return {
                "success": False,
                "source_language": source_language,
                "translations": {},
                "errors": [
                    {
                        "category": "validation",
                        "target_language": "",
                        "error_message": f"Invalid source language: {source_language}",
                    }
                ],
            }

        if not text or not text.strip():
            return {
                "success": False,
                "source_language": source_language,
                "translations": {},
                "errors": [
                    {
                        "category": "validation",
                        "target_language": "",
                        "error_message": "Empty text provided",
                    }
                ],
            }

        # Determine target languages (2 languages other than source)
        target_languages = [lang for lang in valid_languages if lang != source_language]

        # Create prompt
        language_names = {"en": "English", "ja": "Japanese", "zh": "Chinese (Simplified)"}
        target_lang_names = ", ".join(language_names[lang] for lang in target_languages)

        prompt = f"""You are a professional translator. Please translate the following review comment to {target_lang_names}.
Preserve the original meaning and tone while making it natural and readable.
Return the translation result in the following JSON format:
{{
"""
        for lang in target_languages:
            prompt += f'  "{lang}": "{language_names[lang]} translation",\n'
        prompt = prompt.rstrip(",\n") + "\n}\n\n"
        prompt += f"Comment (language: {language_names[source_language]}):\n{text}"

        system_message = "You are a professional translator specializing in business documents and review comments."

        # Call DeepSeek API
        api_response = await self.call_deepseek_api(prompt, system_message)

        if not api_response["success"]:
            return {
                "success": False,
                "source_language": source_language,
                "translations": {},
                "errors": [
                    {
                        "category": "api_error",
                        "target_language": "",
                        "error_message": api_response.get("error_message", "API call failed"),
                    }
                ],
            }

        # Parse JSON
        try:
            translations = json.loads(api_response["content"])

            # Validation: Check if required languages are included
            for lang in target_languages:
                if lang not in translations:
                    logger.warning(f"Target language {lang} not in response")

            return {
                "success": True,
                "source_language": source_language,
                "translations": translations,
                "errors": [],
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, content: {api_response['content']}")
            return {
                "success": False,
                "source_language": source_language,
                "translations": {},
                "errors": [
                    {
                        "category": "parse_error",
                        "target_language": "",
                        "error_message": f"JSON parse failed: {str(e)}",
                    }
                ],
            }

    async def batch_translate_comments(
        self, comments: Dict[str, str], source_language: str
    ) -> Dict[str, Any]:
        """
        Batch translate multiple category comments

        Args:
            comments: Dictionary in {category: comment_text} format
            source_language: Source language code

        Returns:
            dict: {
                "success": bool,
                "translated_comments": {
                    "ja"?: {category: text},
                    "zh"?: {category: text},
                    "en"?: {category: text}
                },
                "errors": [TranslationError]
            }
        """
        # Validation
        valid_languages = ["en", "ja", "zh"]
        if source_language not in valid_languages:
            return {
                "success": False,
                "translated_comments": {},
                "errors": [
                    {
                        "category": "validation",
                        "target_language": "",
                        "error_message": f"Invalid source language: {source_language}",
                    }
                ],
            }

        if not comments:
            return {
                "success": False,
                "translated_comments": {},
                "errors": [
                    {
                        "category": "validation",
                        "target_language": "",
                        "error_message": "No comments provided",
                    }
                ],
            }

        # Determine target languages
        target_languages = [lang for lang in valid_languages if lang != source_language]

        # Create prompt (multiple categories)
        language_names = {"en": "English", "ja": "Japanese", "zh": "Chinese (Simplified)"}
        target_lang_names = ", ".join(language_names[lang] for lang in target_languages)

        prompt = f"""You are a professional translator. Please translate the following review comments (multiple categories) to {target_lang_names}.
Preserve the original meaning and tone while making it natural and readable.
Return the translation result in the following JSON format:
{{
"""
        for lang in target_languages:
            prompt += f'  "{lang}": {{\n'
            for category in comments.keys():
                prompt += f'    "{category}": "{language_names[lang]} translation",\n'
            prompt = prompt.rstrip(",\n") + "\n  },\n"
        prompt = prompt.rstrip(",\n") + "\n}\n\n"

        prompt += f"Comments (language: {language_names[source_language]}):\n"
        for category, text in comments.items():
            prompt += f"- {category}: {text}\n"

        system_message = "You are a professional translator specializing in business documents and review comments."

        # Call DeepSeek API
        api_response = await self.call_deepseek_api(prompt, system_message)

        if not api_response["success"]:
            return {
                "success": False,
                "translated_comments": {},
                "errors": [
                    {
                        "category": "api_error",
                        "target_language": "",
                        "error_message": api_response.get("error_message", "API call failed"),
                    }
                ],
            }

        # Parse JSON
        try:
            translated_comments = json.loads(api_response["content"])

            return {"success": True, "translated_comments": translated_comments, "errors": []}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, content: {api_response['content']}")
            return {
                "success": False,
                "translated_comments": {},
                "errors": [
                    {
                        "category": "parse_error",
                        "target_language": "",
                        "error_message": f"JSON parse failed: {str(e)}",
                    }
                ],
            }

    async def call_deepseek_api(self, prompt: str, system_message: str) -> Dict[str, Any]:
        """
        Request to DeepSeek Chat Completion API

        Args:
            prompt: User prompt
            system_message: System message

        Returns:
            dict: {
                "success": bool,
                "content": str,
                "error_message": Optional[str],
                "usage": Optional[dict]
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "content": "",
                "error_message": "DEEPSEEK_API_KEY not configured",
                "usage": None,
            }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,  # Prioritize translation accuracy
                        "max_tokens": 2000,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"DeepSeek API error: {response.status_code} {response.text}")
                    return {
                        "success": False,
                        "content": "",
                        "error_message": f"API returned status {response.status_code}",
                        "usage": None,
                    }

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage")

                logger.info(f"DeepSeek API success: {usage}")

                return {"success": True, "content": content, "error_message": None, "usage": usage}

        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            return {
                "success": False,
                "content": "",
                "error_message": "API request timeout (30s)",
                "usage": None,
            }

        except httpx.RequestError as e:
            logger.error(f"DeepSeek API request error: {e}")
            return {
                "success": False,
                "content": "",
                "error_message": f"Connection error: {str(e)}",
                "usage": None,
            }

        except Exception as e:
            logger.exception(f"Unexpected error in DeepSeek API call: {e}")
            return {
                "success": False,
                "content": "",
                "error_message": f"Unexpected error: {str(e)}",
                "usage": None,
            }
