"""
I18nFormService - レビューフォームの多言語翻訳辞書管理とデフォルト言語検出

このサービスは、レビュー投稿フォームの多言語対応をサポートします。
主な機能:
- 3言語（英語・日本語・中国語）のフォーム翻訳辞書の提供
- Accept-Languageヘッダーからブラウザ言語の検出
- サポート言語リストの取得

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 2.7, 2.8
"""

import re
from typing import Dict, List, Literal

LanguageCode = Literal["en", "ja", "zh"]


class I18nFormService:
    """レビューフォームの多言語サポートサービス"""

    def __init__(self):
        """サービスの初期化"""
        self._translations = self._build_translations()
        self._supported_languages = self._build_supported_languages()

    def get_form_translations(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        フォーム翻訳辞書を取得

        Returns:
            翻訳辞書 (labels, placeholders, buttons の3セクション)

        Examples:
            >>> service = I18nFormService()
            >>> translations = service.get_form_translations()
            >>> translations["labels"]["employment_status"]["ja"]
            '在職状況'
        """
        return self._translations

    def detect_browser_language(self, accept_language_header: str) -> LanguageCode:
        """
        Accept-Languageヘッダーからブラウザ言語を検出

        Args:
            accept_language_header: HTTPリクエストの Accept-Language ヘッダー

        Returns:
            言語コード ("en", "ja", "zh")
            未対応言語の場合は "en" にフォールバック

        Examples:
            >>> service = I18nFormService()
            >>> service.detect_browser_language("ja,en-US;q=0.9")
            'ja'
            >>> service.detect_browser_language("fr-FR,fr;q=0.9")
            'en'
        """
        if not accept_language_header:
            return "en"

        # Accept-Language ヘッダーをパース
        # 例: "ja,en-US;q=0.9,en;q=0.8" -> [("ja", 1.0), ("en-US", 0.9), ("en", 0.8)]
        languages = []
        for lang_part in accept_language_header.split(","):
            lang_part = lang_part.strip()
            if ";q=" in lang_part:
                lang, quality = lang_part.split(";q=")
                languages.append((lang.strip(), float(quality)))
            else:
                languages.append((lang_part, 1.0))

        # 品質値でソート（降順）
        languages.sort(key=lambda x: x[1], reverse=True)

        # サポート言語を検出
        for lang, _ in languages:
            # 言語コードの先頭2文字を取得（例: "ja-JP" -> "ja"）
            lang_code = lang.split("-")[0].lower()

            if lang_code == "ja":
                return "ja"
            elif lang_code == "zh":
                return "zh"
            elif lang_code == "en":
                return "en"

        # デフォルトは英語
        return "en"

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        サポート言語リストを取得

        Returns:
            言語オプションのリスト

        Examples:
            >>> service = I18nFormService()
            >>> languages = service.get_supported_languages()
            >>> len(languages)
            3
            >>> languages[0]["code"]
            'en'
        """
        return self._supported_languages

    def _build_supported_languages(self) -> List[Dict[str, str]]:
        """サポート言語リストを構築"""
        return [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "ja", "name": "Japanese", "native_name": "日本語"},
            {"code": "zh", "name": "Chinese", "native_name": "中文（简体）"},
        ]

    def _build_translations(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        翻訳辞書を構築

        Returns:
            labels, placeholders, buttons の3セクションを含む翻訳辞書
        """
        return {
            "labels": {
                # ページタイトル
                "review_form_title": {
                    "en": "Submit Review",
                    "ja": "レビュー投稿",
                    "zh": "提交评价",
                },
                # 言語選択
                "review_language": {
                    "en": "Review Language",
                    "ja": "レビュー言語",
                    "zh": "评价语言",
                },
                "select_language": {
                    "en": "Select the language for your review",
                    "ja": "レビューを投稿する言語を選択してください",
                    "zh": "请选择评价语言",
                },
                # 在職状況
                "employment_status": {
                    "en": "Employment Status",
                    "ja": "在職状況",
                    "zh": "在职状态",
                },
                "current_employee": {
                    "en": "Current Employee",
                    "ja": "現従業員",
                    "zh": "现员工",
                },
                "former_employee": {
                    "en": "Former Employee",
                    "ja": "元従業員",
                    "zh": "前员工",
                },
                # 勤務期間
                "employment_period": {
                    "en": "Employment Period",
                    "ja": "勤務期間",
                    "zh": "工作期间",
                },
                "start_year": {
                    "en": "Start Year",
                    "ja": "開始年",
                    "zh": "开始年份",
                },
                "end_year": {
                    "en": "End Year",
                    "ja": "終了年",
                    "zh": "结束年份",
                },
                "present": {
                    "en": "Present (Currently Employed)",
                    "ja": "現在勤務",
                    "zh": "在职",
                },
                # 評価項目
                "rating": {
                    "en": "Rating",
                    "ja": "評価",
                    "zh": "评分",
                },
                "rating_1": {
                    "en": "1 - Poor",
                    "ja": "1点",
                    "zh": "1分",
                },
                "rating_2": {
                    "en": "2 - Fair",
                    "ja": "2点",
                    "zh": "2分",
                },
                "rating_3": {
                    "en": "3 - Neutral",
                    "ja": "3点",
                    "zh": "3分",
                },
                "rating_4": {
                    "en": "4 - Good",
                    "ja": "4点",
                    "zh": "4分",
                },
                "rating_5": {
                    "en": "5 - Excellent",
                    "ja": "5点",
                    "zh": "5分",
                },
                "no_answer": {
                    "en": "No Answer",
                    "ja": "回答しない",
                    "zh": "不回答",
                },
                "year_suffix": {
                    "en": "",
                    "ja": "年",
                    "zh": "年",
                },
                "select_start_year": {
                    "en": "Select start year",
                    "ja": "開始年を選択",
                    "zh": "选择开始年份",
                },
                "select_end_year": {
                    "en": "Select end year",
                    "ja": "終了年を選択",
                    "zh": "选择结束年份",
                },
                # レビューカテゴリー
                "recommendation": {
                    "en": "Recommendation",
                    "ja": "推薦度合い",
                    "zh": "推荐度",
                },
                "recommendation_question": {
                    "en": "Would you recommend this company to other foreign nationals?",
                    "ja": "他の外国人に就業を推薦したい会社ですか？",
                    "zh": "您会向其他外国人推荐这家公司吗？",
                },
                "foreign_support": {
                    "en": "Foreign Employee Support",
                    "ja": "外国人の受け入れ制度",
                    "zh": "外籍员工支持",
                },
                "foreign_support_question": {
                    "en": "Does the company have adequate support systems for foreign employees?",
                    "ja": "外国人の受け入れ制度が整っていますか？",
                    "zh": "公司是否有完善的外籍员工支持制度？",
                },
                "company_culture": {
                    "en": "Company Culture",
                    "ja": "会社風土",
                    "zh": "公司文化",
                },
                "company_culture_question": {
                    "en": "Are company policies clear and does it respect cultural diversity?",
                    "ja": "会社方針は明確で、文化的多様性を尊重していますか？",
                    "zh": "公司政策明确且尊重文化多样性吗？",
                },
                "employee_relations": {
                    "en": "Employee Relations",
                    "ja": "社員との関係性",
                    "zh": "员工关系",
                },
                "employee_relations_question": {
                    "en": "Can you build respectful relationships with supervisors and colleagues?",
                    "ja": "上司・部下とも尊敬の念を持って関係が構築できますか？",
                    "zh": "能否与上司和同事建立相互尊重的关系？",
                },
                "evaluation_system": {
                    "en": "Evaluation System",
                    "ja": "成果・評価制度",
                    "zh": "评价制度",
                },
                "evaluation_system_question": {
                    "en": "Are foreign employees' achievements properly recognized?",
                    "ja": "外国人従業員の成果が認められる制度が整っていますか？",
                    "zh": "外籍员工的成就是否得到适当认可？",
                },
                "promotion_treatment": {
                    "en": "Promotion & Treatment",
                    "ja": "昇進・昇給・待遇",
                    "zh": "晋升与待遇",
                },
                "promotion_treatment_question": {
                    "en": "Are promotion and salary increase opportunities given fairly?",
                    "ja": "昇進・昇給機会は平等に与えられていますか？",
                    "zh": "晋升和加薪机会是否公平？",
                },
                # コメント
                "comment": {
                    "en": "Comment (Optional)",
                    "ja": "コメント（任意）",
                    "zh": "评论（可选）",
                },
                # プレビュー
                "preview_rating": {
                    "en": "Review Score Preview",
                    "ja": "レビュー点数プレビュー",
                    "zh": "评分预览",
                },
                "your_rating": {
                    "en": "Your rating:",
                    "ja": "あなたの評価:",
                    "zh": "您的评分:",
                },
                "items_answered": {
                    "en": "items answered",
                    "ja": "項目回答",
                    "zh": "项已回答",
                },
                "average_of_answered": {
                    "en": "Average of answered items",
                    "ja": "回答した項目の平均点",
                    "zh": "已回答项目的平均分",
                },
                # 必須マーク
                "required": {
                    "en": "*",
                    "ja": "*",
                    "zh": "*",
                },
            },
            "placeholders": {
                "select_start_year": {
                    "en": "Select start year",
                    "ja": "開始年を選択",
                    "zh": "选择开始年份",
                },
                "select_end_year": {
                    "en": "Select end year",
                    "ja": "終了年を選択",
                    "zh": "选择结束年份",
                },
                "comment": {
                    "en": "Share your specific experiences or episodes (max 1000 characters)",
                    "ja": "具体的な経験やエピソードがあれば教えてください（最大1000文字）",
                    "zh": "分享您的具体经历或事例（最多1000字）",
                },
                "select_language_placeholder": {
                    "en": "Select language",
                    "ja": "言語を選択",
                    "zh": "选择语言",
                },
            },
            "buttons": {
                "submit": {
                    "en": "Submit Review",
                    "ja": "レビューを投稿",
                    "zh": "提交评价",
                },
                "preview": {
                    "en": "Preview →",
                    "ja": "プレビュー →",
                    "zh": "预览 →",
                },
                "cancel": {
                    "en": "Cancel",
                    "ja": "キャンセル",
                    "zh": "取消",
                },
                "back": {
                    "en": "Back",
                    "ja": "戻る",
                    "zh": "返回",
                },
                "confirm": {
                    "en": "Confirm",
                    "ja": "確認",
                    "zh": "确认",
                },
            },
        }
