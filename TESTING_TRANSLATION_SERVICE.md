# Translation Service Testing Guide

## Overview
This guide provides manual testing scenarios for the DeepSeek API-based translation service implemented in Tasks 5.1-5.3.

## Prerequisites

### 1. Setup DeepSeek API Key
```bash
# Get your API key from https://platform.deepseek.com/
# Add to your .env file:
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

### 2. Install Dependencies
```bash
cd /Users/jun77/Documents/Dropbox/a_root/code/dxeeworld
uv sync
```

## Test Scenarios

### Scenario 1: Single Comment Translation (Japanese → English + Chinese)

**Objective:** Verify that a Japanese review comment is correctly translated to English and Chinese.

**Steps:**
1. Create a test script `test_translation_manual.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from src.services.translation_service import TranslationService

load_dotenv()

async def test_japanese_to_others():
    service = TranslationService()
    
    # Japanese comment
    comment = "この会社は外国人社員を大切にしています。給与も良く、働きやすい環境です。"
    
    print("=" * 50)
    print("Test 1: Japanese → English + Chinese")
    print("=" * 50)
    print(f"Original (Japanese): {comment}")
    print()
    
    result = await service.translate_to_other_languages(comment, "ja")
    
    if result["success"]:
        print("✅ Translation successful!")
        print(f"English: {result['translations'].get('en', 'N/A')}")
        print(f"Chinese: {result['translations'].get('zh', 'N/A')}")
    else:
        print("❌ Translation failed!")
        print(f"Errors: {result['errors']}")
    
    print()

if __name__ == "__main__":
    asyncio.run(test_japanese_to_others())
```

2. Run the test:
```bash
uv run python test_translation_manual.py
```

**Expected Result:**
```
✅ Translation successful!
English: This company values foreign employees. The salary is good, and it's a comfortable working environment.
Chinese: 这家公司重视外国员工。薪水很好，工作环境舒适。
```

---

### Scenario 2: Single Comment Translation (English → Japanese + Chinese)

**Steps:**
Add this function to `test_translation_manual.py`:

```python
async def test_english_to_others():
    service = TranslationService()
    
    comment = "This is an excellent company with great work-life balance and competitive salary."
    
    print("=" * 50)
    print("Test 2: English → Japanese + Chinese")
    print("=" * 50)
    print(f"Original (English): {comment}")
    print()
    
    result = await service.translate_to_other_languages(comment, "en")
    
    if result["success"]:
        print("✅ Translation successful!")
        print(f"Japanese: {result['translations'].get('ja', 'N/A')}")
        print(f"Chinese: {result['translations'].get('zh', 'N/A')}")
    else:
        print("❌ Translation failed!")
        print(f"Errors: {result['errors']}")
    
    print()

# In main:
asyncio.run(test_english_to_others())
```

**Expected Result:**
```
✅ Translation successful!
Japanese: これはワークライフバランスと競争力のある給与を持つ素晴らしい会社です。
Chinese: 这是一家拥有良好工作生活平衡和有竞争力薪资的优秀公司。
```

---

### Scenario 3: Single Comment Translation (Chinese → English + Japanese)

**Steps:**
Add this function:

```python
async def test_chinese_to_others():
    service = TranslationService()
    
    comment = "这家公司的工作环境很好，同事关系融洽，福利待遇优厚。"
    
    print("=" * 50)
    print("Test 3: Chinese → English + Japanese")
    print("=" * 50)
    print(f"Original (Chinese): {comment}")
    print()
    
    result = await service.translate_to_other_languages(comment, "zh")
    
    if result["success"]:
        print("✅ Translation successful!")
        print(f"English: {result['translations'].get('en', 'N/A')}")
        print(f"Japanese: {result['translations'].get('ja', 'N/A')}")
    else:
        print("❌ Translation failed!")
        print(f"Errors: {result['errors']}")
    
    print()
```

---

### Scenario 4: Batch Translation (Multiple Categories)

**Objective:** Verify that multiple review categories can be translated in a single API call.

**Steps:**
Add this function:

```python
async def test_batch_translation():
    service = TranslationService()
    
    comments = {
        "recommendation": "強くお勧めします。",
        "company_culture": "多様性を尊重する文化があります。",
        "evaluation_system": "公平な評価制度が整っています。",
        "work_life_balance": "ワークライフバランスが良好です。"
    }
    
    print("=" * 50)
    print("Test 4: Batch Translation (Japanese → English + Chinese)")
    print("=" * 50)
    print("Original comments (Japanese):")
    for category, text in comments.items():
        print(f"  - {category}: {text}")
    print()
    
    result = await service.batch_translate_comments(comments, "ja")
    
    if result["success"]:
        print("✅ Batch translation successful!")
        print()
        print("English translations:")
        for category, text in result["translated_comments"].get("en", {}).items():
            print(f"  - {category}: {text}")
        print()
        print("Chinese translations:")
        for category, text in result["translated_comments"].get("zh", {}).items():
            print(f"  - {category}: {text}")
    else:
        print("❌ Batch translation failed!")
        print(f"Errors: {result['errors']}")
    
    print()
```

**Expected Result:**
```
✅ Batch translation successful!

English translations:
  - recommendation: Highly recommended.
  - company_culture: There is a culture that respects diversity.
  - evaluation_system: A fair evaluation system is in place.
  - work_life_balance: Work-life balance is good.

Chinese translations:
  - recommendation: 强烈推荐。
  - company_culture: 有尊重多样性的文化。
  - evaluation_system: 有完善的公平评估制度。
  - work_life_balance: 工作生活平衡良好。
```

---

### Scenario 5: Error Handling - Invalid Language Code

**Objective:** Verify graceful error handling for invalid language codes.

**Steps:**
```python
async def test_invalid_language():
    service = TranslationService()
    
    comment = "Test comment"
    
    print("=" * 50)
    print("Test 5: Invalid Language Code")
    print("=" * 50)
    
    result = await service.translate_to_other_languages(comment, "invalid")
    
    if not result["success"]:
        print("✅ Error handled correctly!")
        print(f"Error: {result['errors'][0]['error_message']}")
    else:
        print("❌ Should have returned error!")
    
    print()
```

**Expected Result:**
```
✅ Error handled correctly!
Error: Invalid source language: invalid
```

---

### Scenario 6: Error Handling - Empty Comment

**Objective:** Verify handling of empty comments.

**Steps:**
```python
async def test_empty_comment():
    service = TranslationService()
    
    print("=" * 50)
    print("Test 6: Empty Comment")
    print("=" * 50)
    
    result = await service.translate_to_other_languages("", "en")
    
    if not result["success"]:
        print("✅ Error handled correctly!")
        print(f"Error: {result['errors'][0]['error_message']}")
    else:
        print("❌ Should have returned error!")
    
    print()
```

**Expected Result:**
```
✅ Error handled correctly!
Error: Empty text provided
```

---

### Scenario 7: Error Handling - Missing API Key

**Objective:** Verify graceful degradation when API key is not configured.

**Steps:**
```python
async def test_missing_api_key():
    # Temporarily remove API key
    original_key = os.environ.get("DEEPSEEK_API_KEY")
    if "DEEPSEEK_API_KEY" in os.environ:
        del os.environ["DEEPSEEK_API_KEY"]
    
    service = TranslationService()
    
    print("=" * 50)
    print("Test 7: Missing API Key")
    print("=" * 50)
    
    result = await service.translate_to_other_languages("Test", "en")
    
    if not result["success"]:
        print("✅ Error handled correctly!")
        print(f"Error: {result['errors'][0]['error_message']}")
    else:
        print("❌ Should have returned error!")
    
    # Restore API key
    if original_key:
        os.environ["DEEPSEEK_API_KEY"] = original_key
    
    print()
```

**Expected Result:**
```
✅ Error handled correctly!
Error: API call failed (or DEEPSEEK_API_KEY not configured)
```

---

### Scenario 8: Token Usage Monitoring

**Objective:** Monitor token usage and cost estimation.

**Steps:**
```python
async def test_token_usage():
    service = TranslationService()
    
    comment = "この会社は外国人社員を大切にしています。給与も良く、働きやすい環境です。チームワークが素晴らしく、上司も部下も互いに尊重し合っています。"
    
    print("=" * 50)
    print("Test 8: Token Usage Monitoring")
    print("=" * 50)
    print(f"Original (Japanese): {comment}")
    print()
    
    # Direct API call to see usage
    prompt = f"""You are a professional translator. Please translate the following review comment to English, Chinese (Simplified).
Preserve the original meaning and tone while making it natural and readable.
Return the translation result in the following JSON format:
{{
  "en": "English translation",
  "zh": "Chinese (Simplified) translation"
}}

Comment (language: Japanese):
{comment}"""
    
    system_message = "You are a professional translator specializing in business documents and review comments."
    
    api_response = await service.call_deepseek_api(prompt, system_message)
    
    if api_response["success"]:
        usage = api_response["usage"]
        print("✅ Translation successful!")
        print()
        print("Token Usage:")
        print(f"  - Prompt tokens: {usage['prompt_tokens']}")
        print(f"  - Completion tokens: {usage['completion_tokens']}")
        print(f"  - Total tokens: {usage['total_tokens']}")
        print()
        print("Cost Estimation:")
        input_cost = usage['prompt_tokens'] * 0.14 / 1_000_000
        output_cost = usage['completion_tokens'] * 0.28 / 1_000_000
        total_cost = input_cost + output_cost
        print(f"  - Input cost: ${input_cost:.6f}")
        print(f"  - Output cost: ${output_cost:.6f}")
        print(f"  - Total cost: ${total_cost:.6f}")
    else:
        print("❌ Translation failed!")
        print(f"Error: {api_response['error_message']}")
    
    print()
```

**Expected Result:**
```
✅ Translation successful!

Token Usage:
  - Prompt tokens: 150
  - Completion tokens: 80
  - Total tokens: 230

Cost Estimation:
  - Input cost: $0.000021
  - Output cost: $0.000022
  - Total cost: $0.000043
```

---

## Complete Test Script

Here's the complete `test_translation_manual.py` file:

```python
import asyncio
import os
from dotenv import load_dotenv
from src.services.translation_service import TranslationService

load_dotenv()

async def test_japanese_to_others():
    service = TranslationService()
    comment = "この会社は外国人社員を大切にしています。給与も良く、働きやすい環境です。"
    
    print("=" * 50)
    print("Test 1: Japanese → English + Chinese")
    print("=" * 50)
    print(f"Original (Japanese): {comment}")
    print()
    
    result = await service.translate_to_other_languages(comment, "ja")
    
    if result["success"]:
        print("✅ Translation successful!")
        print(f"English: {result['translations'].get('en', 'N/A')}")
        print(f"Chinese: {result['translations'].get('zh', 'N/A')}")
    else:
        print("❌ Translation failed!")
        print(f"Errors: {result['errors']}")
    print()

async def test_english_to_others():
    service = TranslationService()
    comment = "This is an excellent company with great work-life balance and competitive salary."
    
    print("=" * 50)
    print("Test 2: English → Japanese + Chinese")
    print("=" * 50)
    print(f"Original (English): {comment}")
    print()
    
    result = await service.translate_to_other_languages(comment, "en")
    
    if result["success"]:
        print("✅ Translation successful!")
        print(f"Japanese: {result['translations'].get('ja', 'N/A')}")
        print(f"Chinese: {result['translations'].get('zh', 'N/A')}")
    else:
        print("❌ Translation failed!")
        print(f"Errors: {result['errors']}")
    print()

async def test_chinese_to_others():
    service = TranslationService()
    comment = "这家公司的工作环境很好，同事关系融洽，福利待遇优厚。"
    
    print("=" * 50)
    print("Test 3: Chinese → English + Japanese")
    print("=" * 50)
    print(f"Original (Chinese): {comment}")
    print()
    
    result = await service.translate_to_other_languages(comment, "zh")
    
    if result["success"]:
        print("✅ Translation successful!")
        print(f"English: {result['translations'].get('en', 'N/A')}")
        print(f"Japanese: {result['translations'].get('ja', 'N/A')}")
    else:
        print("❌ Translation failed!")
        print(f"Errors: {result['errors']}")
    print()

async def test_batch_translation():
    service = TranslationService()
    comments = {
        "recommendation": "強くお勧めします。",
        "company_culture": "多様性を尊重する文化があります。",
        "evaluation_system": "公平な評価制度が整っています。",
        "work_life_balance": "ワークライフバランスが良好です。"
    }
    
    print("=" * 50)
    print("Test 4: Batch Translation (Japanese → English + Chinese)")
    print("=" * 50)
    print("Original comments (Japanese):")
    for category, text in comments.items():
        print(f"  - {category}: {text}")
    print()
    
    result = await service.batch_translate_comments(comments, "ja")
    
    if result["success"]:
        print("✅ Batch translation successful!")
        print()
        print("English translations:")
        for category, text in result["translated_comments"].get("en", {}).items():
            print(f"  - {category}: {text}")
        print()
        print("Chinese translations:")
        for category, text in result["translated_comments"].get("zh", {}).items():
            print(f"  - {category}: {text}")
    else:
        print("❌ Batch translation failed!")
        print(f"Errors: {result['errors']}")
    print()

async def test_invalid_language():
    service = TranslationService()
    
    print("=" * 50)
    print("Test 5: Invalid Language Code")
    print("=" * 50)
    
    result = await service.translate_to_other_languages("Test comment", "invalid")
    
    if not result["success"]:
        print("✅ Error handled correctly!")
        print(f"Error: {result['errors'][0]['error_message']}")
    else:
        print("❌ Should have returned error!")
    print()

async def test_empty_comment():
    service = TranslationService()
    
    print("=" * 50)
    print("Test 6: Empty Comment")
    print("=" * 50)
    
    result = await service.translate_to_other_languages("", "en")
    
    if not result["success"]:
        print("✅ Error handled correctly!")
        print(f"Error: {result['errors'][0]['error_message']}")
    else:
        print("❌ Should have returned error!")
    print()

async def test_token_usage():
    service = TranslationService()
    comment = "この会社は外国人社員を大切にしています。給与も良く、働きやすい環境です。"
    
    print("=" * 50)
    print("Test 7: Token Usage Monitoring")
    print("=" * 50)
    print(f"Original (Japanese): {comment}")
    print()
    
    prompt = f"""You are a professional translator. Please translate the following review comment to English, Chinese (Simplified).
Preserve the original meaning and tone while making it natural and readable.
Return the translation result in the following JSON format:
{{
  "en": "English translation",
  "zh": "Chinese (Simplified) translation"
}}

Comment (language: Japanese):
{comment}"""
    
    system_message = "You are a professional translator specializing in business documents and review comments."
    
    api_response = await service.call_deepseek_api(prompt, system_message)
    
    if api_response["success"]:
        usage = api_response["usage"]
        print("✅ Translation successful!")
        print()
        print("Token Usage:")
        print(f"  - Prompt tokens: {usage['prompt_tokens']}")
        print(f"  - Completion tokens: {usage['completion_tokens']}")
        print(f"  - Total tokens: {usage['total_tokens']}")
        print()
        print("Cost Estimation:")
        input_cost = usage['prompt_tokens'] * 0.14 / 1_000_000
        output_cost = usage['completion_tokens'] * 0.28 / 1_000_000
        total_cost = input_cost + output_cost
        print(f"  - Input cost: ${input_cost:.6f}")
        print(f"  - Output cost: ${output_cost:.6f}")
        print(f"  - Total cost: ${total_cost:.6f}")
    else:
        print("❌ Translation failed!")
        print(f"Error: {api_response['error_message']}")
    print()

async def main():
    print("\n")
    print("=" * 50)
    print("DeepSeek Translation Service - Manual Testing")
    print("=" * 50)
    print("\n")
    
    await test_japanese_to_others()
    await test_english_to_others()
    await test_chinese_to_others()
    await test_batch_translation()
    await test_invalid_language()
    await test_empty_comment()
    await test_token_usage()
    
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Running the Tests

```bash
# Run all tests
uv run python test_translation_manual.py

# Or run individual scenarios by commenting out tests in main()
```

---

## Expected Test Results Summary

| Scenario | Expected Result | Pass Criteria |
|----------|----------------|---------------|
| 1. Japanese → EN + ZH | ✅ 2 translations returned | Translations are accurate and natural |
| 2. English → JA + ZH | ✅ 2 translations returned | Translations are accurate and natural |
| 3. Chinese → EN + JA | ✅ 2 translations returned | Translations are accurate and natural |
| 4. Batch Translation | ✅ All categories translated | All 4 categories translated correctly |
| 5. Invalid Language | ✅ Error returned | Error message indicates invalid language |
| 6. Empty Comment | ✅ Error returned | Error message indicates empty text |
| 7. Token Usage | ✅ Usage stats displayed | Token counts and costs shown correctly |

---

## Troubleshooting

### Issue: "DEEPSEEK_API_KEY not configured"
**Solution:** Make sure you've added your API key to `.env` file:
```bash
DEEPSEEK_API_KEY=sk-your-actual-key
```

### Issue: "API request timeout (30s)"
**Solution:** 
- Check your internet connection
- DeepSeek API might be slow or down
- Consider increasing timeout in `translation_service.py`

### Issue: "JSON parse failed"
**Solution:** 
- This might happen if DeepSeek returns non-JSON response
- Check the logged content in the error message
- The service will gracefully degrade and return error

---

## Cost Monitoring

Track your API usage at: https://platform.deepseek.com/usage

**Estimated costs per test run:**
- Single translation: ~$0.00004 (230 tokens)
- Batch translation: ~$0.00012 (600 tokens)
- Full test suite (7 tests): ~$0.0003 total

Very affordable for testing! 🎉
