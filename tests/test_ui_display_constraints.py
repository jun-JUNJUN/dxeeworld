"""
Test for UI display constraints - Task 10.1

Tests that certain fields are hidden from the UI while retained in the database:
- Data source field should not be displayed on company detail page
- Database schema should still include data_source field
"""
import pytest
import re


class TestUIDisplayConstraints:
    """UI表示制約のテスト - Task 10.1"""

    def test_data_source_field_not_displayed_in_company_detail(self):
        """企業詳細ページに「データソース」フィールドが表示されていないことを確認 - Task 10.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 「データソース」というテキストが表示されていないことを確認
        data_source_patterns = [
            r'データソース',
            r'data[_\s-]?source',
            r'data_source',
        ]

        for pattern in data_source_patterns:
            # コメント内は除外（<!-- ... -->, {# ... #}）
            # JavaScriptコード内は除外（<script> ... </script>）
            # CSSコード内は除外（<style> ... </style>）

            # コメント、スクリプト、スタイルを除外したコンテンツを作成
            content_without_html_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            content_without_jinja_comments = re.sub(r'\{#.*?#\}', '', content_without_html_comments, flags=re.DOTALL)
            content_without_scripts = re.sub(r'<script.*?</script>', '', content_without_jinja_comments, flags=re.DOTALL | re.IGNORECASE)
            content_without_styles = re.sub(r'<style.*?</style>', '', content_without_scripts, flags=re.DOTALL | re.IGNORECASE)

            # 実際の表示内容にデータソースフィールドが含まれていないことを確認
            assert not re.search(pattern, content_without_styles, re.IGNORECASE), \
                f"企業詳細ページに「データソース」フィールドが表示されています: パターン {pattern}"

    def test_company_model_has_data_source_field(self):
        """Companyモデルにsource_filesフィールドが保持されていることを確認 - Task 10.1"""
        with open('src/models/company.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # source_filesフィールドがモデル定義に含まれていることを確認
        data_source_patterns = [
            r'source_files',
            r'[\'"]source_files[\'"]',
        ]

        found_data_source = any(re.search(pattern, content, re.IGNORECASE)
                               for pattern in data_source_patterns)

        assert found_data_source, \
            "Companyモデルにsource_filesフィールドが見つかりません（データベースには保持する必要があります）"

    def test_csv_import_service_can_set_source_files(self):
        """CSVインポート時にsource_filesフィールドが設定可能であることを確認 - Task 10.1"""
        # CSVインポート時にsource_filesフィールドが設定できることを確認
        # 実装の詳細は問わないが、モデルがフィールドをサポートしていることを確認
        with open('src/models/company.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # source_filesフィールドがモデルに存在することを再確認
        assert re.search(r'source_files', content, re.IGNORECASE), \
            "Companyモデルがsource_filesフィールドをサポートしていません"

    def test_company_detail_handler_can_access_data_source(self):
        """CompanyDetailHandlerがsource_filesフィールドにアクセスできることを確認 - Task 10.1"""
        # ハンドラーはデータベースから完全なデータを取得できる必要がある
        # （表示しないだけで、データへのアクセスは可能）

        with open('src/handlers/company_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # ハンドラーがcompanyオブジェクトを取得していることを確認
        # source_filesフィールドを明示的に除外していないことを確認
        exclusion_patterns = [
            r'del\s+company\[[\'"]source_files[\'"]\]',
            r'company\.pop\([\'"]source_files[\'"]\)',
            r'exclude.*?source_files',
        ]

        for pattern in exclusion_patterns:
            assert not re.search(pattern, content, re.IGNORECASE), \
                f"ハンドラーでsource_filesフィールドを除外しています（除外すべきではありません）: {pattern}"

    def test_company_list_page_does_not_show_data_source(self):
        """企業一覧ページにもデータソースフィールドが表示されていないことを確認 - Task 10.1"""
        with open('templates/companies/list.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 「データソース」というテキストが表示されていないことを確認
        data_source_patterns = [
            r'データソース',
            r'data[_\s-]?source',
        ]

        # コメントとスクリプトを除外
        content_without_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        content_without_scripts = re.sub(r'<script.*?</script>', '', content_without_comments, flags=re.DOTALL | re.IGNORECASE)

        for pattern in data_source_patterns:
            assert not re.search(pattern, content_without_scripts, re.IGNORECASE), \
                f"企業一覧ページに「データソース」フィールドが表示されています: パターン {pattern}"

    def test_company_detail_shows_other_essential_fields(self):
        """企業詳細ページが他の必須フィールドを正しく表示していることを確認 - Task 10.1"""
        with open('templates/companies/detail.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 必須フィールドが表示されていることを確認
        essential_fields = [
            (r'company.*?name', '企業名'),
            (r'industry', '業界'),
            (r'location', '所在地'),
            (r'description', '説明'),
        ]

        for pattern, field_name in essential_fields:
            assert re.search(pattern, content, re.IGNORECASE), \
                f"企業詳細ページに {field_name} フィールドが表示されていません"
