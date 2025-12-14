"""
End-to-End tests for review detail pages - Tasks 11.1, 11.2

Tests complete user flows:
- Task 11.1: Full access user review viewing flow
- Task 11.2: Preview user category review viewing flow
"""
import pytest
import re


class TestFullAccessUserReviewFlow:
    """フルアクセスユーザーのレビュー閲覧フロー - Task 11.1"""

    def test_review_detail_page_has_full_comments_visible(self):
        """個別レビュー詳細ページで全項目のコメントが表示されることを確認 - Task 11.1"""
        # テンプレートファイルを確認
        with open('templates/review_detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # プレビューモードとフルアクセスモードの条件分岐を確認
        # {% elif preview_mode %} でマスキング、それ以外で表示
        preview_mode_pattern = r'\{%\s*elif\s+preview_mode\s*%\}'
        assert re.search(preview_mode_pattern, content), \
            "レビュー詳細ページにpreview_mode条件分岐が見つかりません"

        # コメント表示ロジックの存在確認（preview_mode以外の場合）
        comment_display_pattern = r'category-comment'
        assert re.search(comment_display_pattern, content), \
            "レビュー詳細ページにコメント表示ロジックが見つかりません"

        # コメントマスキングロジック（プレビューモード）の存在確認
        masking_patterns = [
            r'preview_mode',
            r'comment-masked',
            r'\*+',  # マスキング文字
        ]

        found_masking = any(re.search(pattern, content, re.IGNORECASE)
                          for pattern in masking_patterns)
        assert found_masking, \
            "プレビューモードのマスキングロジックが見つかりません"

    def test_review_detail_shows_all_six_rating_categories(self):
        """レビュー詳細ページで6つの評価項目すべてが表示されることを確認 - Task 11.1"""
        with open('templates/review_detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 6つの評価項目キーの存在確認
        categories = [
            'recommendation',
            'foreign_support',
            'company_culture',
            'employee_relations',
            'evaluation_system',
            'promotion_treatment',
        ]

        for category in categories:
            assert re.search(category, content), \
                f"レビュー詳細ページに評価項目 {category} が見つかりません"

        # category_labelsディクショナリの使用確認
        assert re.search(r'category_labels', content), \
            "レビュー詳細ページにcategory_labelsが見つかりません"

    def test_review_detail_has_back_to_company_link(self):
        """レビュー詳細ページに企業詳細ページへの戻るリンクが存在することを確認 - Task 11.1"""
        with open('templates/review_detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 企業詳細ページへのリンク確認（company_id変数を使用）
        company_link_pattern = r'/companies/\{\{\s*company_id\s*\}\}'
        assert re.search(company_link_pattern, content), \
            "レビュー詳細ページに企業詳細ページへのリンクが見つかりません"

        # 戻るリンクテキストの確認
        back_patterns = [
            r'戻る',
            r'企業ページ',
            r'企業詳細',
        ]

        found_back_text = any(re.search(pattern, content, re.IGNORECASE)
                             for pattern in back_patterns)
        assert found_back_text, "レビュー詳細ページに戻るリンクテキストが見つかりません"

    def test_company_detail_has_review_detail_links(self):
        """企業詳細ページにレビュー詳細ページへのリンクが存在することを確認 - Task 11.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 「詳細を見る」リンクの存在確認（review['id']を使用）
        detail_link_pattern = r'/companies/\{\{\s*company\[[\'"]id[\'"]\]\s*\}\}/reviews/\{\{\s*review\[[\'"]id[\'"]\]\s*\}\}'
        assert re.search(detail_link_pattern, content), \
            "企業詳細ページにレビュー詳細リンクが見つかりません"

        # 「詳細を見る」テキストの確認
        assert re.search(r'詳細を見る', content), \
            "企業詳細ページに「詳細を見る」テキストが見つかりません"

    def test_review_handler_has_full_access_logic(self):
        """レビューハンドラーにフルアクセス判定ロジックが存在することを確認 - Task 11.1"""
        with open('src/handlers/review_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # アクセス制御関連のクラス・メソッドの存在確認
        access_control_patterns = [
            r'AccessControlMiddleware',
            r'access_control',
            r'preview',  # preview_modeまたはpreview関連
        ]

        found_access_control = any(re.search(pattern, content, re.IGNORECASE)
                                  for pattern in access_control_patterns)
        assert found_access_control, \
            "レビューハンドラーにアクセス制御ロジックが見つかりません"


class TestPreviewUserCategoryReviewFlow:
    """プレビューユーザーの質問別レビュー閲覧フロー - Task 11.2"""

    def test_company_detail_has_category_review_links(self):
        """企業詳細ページに質問別レビュー一覧へのリンクが存在することを確認 - Task 11.2"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 「受入制度のレビューを見る」リンクの確認
        foreign_support_link = r'/companies/\{\{\s*company\[[\'"]id[\'"]\]\s*\}\}/reviews/by-category/foreign_support'
        assert re.search(foreign_support_link, content), \
            "企業詳細ページに受入制度の質問別レビュー一覧リンクが見つかりません"

        # リンクテキストの確認
        assert re.search(r'受入制度.*?レビュー.*?見る', content, re.IGNORECASE), \
            "企業詳細ページに「受入制度のレビューを見る」テキストが見つかりません"

    def test_category_review_list_template_exists(self):
        """質問別レビュー一覧テンプレートが存在することを確認 - Task 11.2"""
        import os
        template_path = 'templates/category_review_list.html'
        assert os.path.exists(template_path), \
            f"質問別レビュー一覧テンプレート {template_path} が見つかりません"

    def test_category_review_list_has_masked_comments_for_preview(self):
        """質問別レビュー一覧でプレビューモード時にコメントがマスクされることを確認 - Task 11.2"""
        with open('templates/category_review_list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # プレビューモード条件分岐の確認
        preview_mode_pattern = r'\{%\s*elif\s+preview_mode\s*%\}'
        assert re.search(preview_mode_pattern, content), \
            "質問別レビュー一覧にpreview_mode条件分岐が見つかりません"

        # マスキング表示の確認
        masking_pattern = r'comment-masked'
        assert re.search(masking_pattern, content), \
            "質問別レビュー一覧にコメントマスキングロジックが見つかりません"

        # コメント表示ロジックの確認（preview_mode以外の場合）
        comment_display_pattern = r'review-comment'
        assert re.search(comment_display_pattern, content), \
            "質問別レビュー一覧にコメント表示ロジックが見つかりません"

    def test_category_review_list_has_cta_for_preview_users(self):
        """質問別レビュー一覧にプレビューユーザー向けCTAが存在することを確認 - Task 11.2"""
        with open('templates/category_review_list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # CTA（Call-to-Action）の存在確認
        cta_patterns = [
            r'レビューを投稿',
            r'preview-cta',
        ]

        found_cta = any(re.search(pattern, content, re.IGNORECASE)
                       for pattern in cta_patterns)
        assert found_cta, \
            "質問別レビュー一覧にプレビューユーザー向けCTAが見つかりません"

        # CTAがpreview_mode条件付きで表示されることを確認
        cta_conditional_pattern = r'\{%\s*if\s+preview_mode\s*%\}'
        assert re.search(cta_conditional_pattern, content), \
            "CTAがpreview_mode条件付きで表示されていません"

    def test_category_review_handler_exists(self):
        """カテゴリ別レビュー一覧ハンドラーが存在することを確認 - Task 11.2"""
        import os

        # CategoryReviewListHandler が専用ファイルに存在することを確認
        handler_file_path = 'src/handlers/category_review_list_handler.py'
        assert os.path.exists(handler_file_path), \
            f"カテゴリ別レビュー一覧ハンドラーファイル {handler_file_path} が見つかりません"

        with open(handler_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # CategoryReviewListHandler クラスの存在確認
        class_pattern = r'class\s+CategoryReviewListHandler'
        assert re.search(class_pattern, content), \
            "CategoryReviewListHandlerクラスが見つかりません"

    def test_category_review_handler_has_access_level_logic(self):
        """カテゴリ別レビュー一覧ハンドラーにアクセスレベル判定ロジックが存在することを確認 - Task 11.2"""
        with open('src/handlers/category_review_list_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # アクセス制御関連のクラス・メソッドの存在確認
        access_patterns = [
            r'AccessControlMiddleware',
            r'access_control',
            r'preview',
        ]

        found_access = any(re.search(pattern, content, re.IGNORECASE)
                         for pattern in access_patterns)
        assert found_access, \
            "カテゴリ別レビュー一覧ハンドラーにアクセス制御ロジックが見つかりません"

    def test_routing_for_category_review_list(self):
        """カテゴリ別レビュー一覧のルーティングが存在することを確認 - Task 11.2"""
        with open('src/app.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # ルーティング定義の存在確認
        routing_pattern = r'/companies/.*?/reviews/by-category/.*?CategoryReviewListHandler'
        assert re.search(routing_pattern, content, re.IGNORECASE), \
            "カテゴリ別レビュー一覧のルーティングが見つかりません"

    def test_category_review_list_displays_category_name(self):
        """質問別レビュー一覧でカテゴリ名（日本語）が表示されることを確認 - Task 11.2"""
        with open('templates/category_review_list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # カテゴリ名の表示確認
        category_label_pattern = r'\{\{\s*category_label\s*\}\}'
        assert re.search(category_label_pattern, content), \
            "質問別レビュー一覧にcategory_labelの表示が見つかりません"

    def test_category_review_list_shows_average_score(self):
        """質問別レビュー一覧で当該項目の平均評価スコアが表示されることを確認 - Task 11.2"""
        with open('templates/category_review_list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 平均評価スコアの表示確認
        average_score_pattern = r'category-average'
        assert re.search(average_score_pattern, content, re.IGNORECASE), \
            "質問別レビュー一覧に平均評価スコアの表示が見つかりません"

    def test_category_review_list_shows_total_count(self):
        """質問別レビュー一覧でレビュー総数が表示されることを確認 - Task 11.2"""
        with open('templates/category_review_list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # レビュー総数の表示確認
        count_patterns = [
            r'total_count',
            r'review-count',
            r'レビュー.*?件',
        ]

        found_count = any(re.search(pattern, content, re.IGNORECASE)
                        for pattern in count_patterns)
        assert found_count, \
            "質問別レビュー一覧にレビュー総数の表示が見つかりません"
