"""
Task 5.1: Mini Panel HTML構造のテスト
Login/Register Mini Panel UI実装のテスト

Tests for the Login/Register Mini Panel HTML structure in base.html.
TDD - RED phase: Writing failing tests first.
"""

import unittest
from bs4 import BeautifulSoup
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class MiniPanelHTMLStructureTest(unittest.TestCase):
    """Task 5.1: Mini Panel HTML構造のテスト"""

    def setUp(self):
        """テンプレートファイルを読み込む"""
        template_path = os.path.join(project_root, 'templates', 'base.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
        self.soup = BeautifulSoup(self.template_content, 'html.parser')

    def test_mini_panel_container_exists(self):
        """RED: Mini Panelのコンテナが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel, "id='login-mini-panel' のdiv要素が見つかりません")

    def test_mini_panel_has_correct_class(self):
        """RED: Mini Panelが正しいクラス名を持つかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        self.assertIn('mini-panel', panel.get('class', []),
                     "Mini Panelに 'mini-panel' クラスが設定されていません")

    def test_mini_panel_initially_hidden(self):
        """RED: Mini Panelが初期状態で非表示かテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        style = panel.get('style', '')
        self.assertIn('display: none', style.lower(),
                     "Mini Panelが初期状態で非表示になっていません (display: none)")

    def test_panel_header_exists(self):
        """RED: パネルヘッダーが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        header = panel.find('div', class_='panel-header')
        self.assertIsNotNone(header, "class='panel-header' が見つかりません")

    def test_panel_title_exists(self):
        """RED: パネルタイトル "Sign in to DXEEWorld" が存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        header = panel.find('div', class_='panel-header')
        title = header.find('h3')
        self.assertIsNotNone(title, "パネルヘッダー内にh3タグが見つかりません")
        expected_title = "Sign in to DXEEWorld"
        self.assertIn(expected_title, title.get_text(),
                     f"タイトルが正しくありません。期待値: '{expected_title}'")

    def test_close_button_exists(self):
        """RED: 閉じるボタン (×) が存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        close_btn = panel.find('button', class_='close-btn')
        self.assertIsNotNone(close_btn, "class='close-btn' のボタンが見つかりません")
        self.assertIn('×', close_btn.get_text(),
                     "閉じるボタンに '×' アイコンが含まれていません")

    def test_panel_body_exists(self):
        """RED: パネルボディが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        body = panel.find('div', class_='panel-body')
        self.assertIsNotNone(body, "class='panel-body' が見つかりません")

    def test_google_login_button_exists(self):
        """RED: Googleログインボタンが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        google_btn = panel.find('button', class_='google-btn')
        self.assertIsNotNone(google_btn, "class='google-btn' が見つかりません")
        expected_text = "Google でログイン"
        self.assertIn(expected_text, google_btn.get_text(),
                     f"Googleボタンのテキストが正しくありません。期待値: '{expected_text}'")

    def test_google_button_has_onclick(self):
        """RED: Googleボタンにonclickイベントが設定されているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        google_btn = panel.find('button', class_='google-btn')
        self.assertIsNotNone(google_btn)
        onclick = google_btn.get('onclick', '')
        self.assertIn('loginWithGoogle', onclick,
                     "Googleボタンに 'loginWithGoogle()' イベントが設定されていません")

    def test_google_button_has_icon(self):
        """RED: Googleボタンにアイコン画像が含まれているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        google_btn = panel.find('button', class_='google-btn')
        self.assertIsNotNone(google_btn)
        icon = google_btn.find('img')
        self.assertIsNotNone(icon, "Googleボタン内にimgタグが見つかりません")
        src = icon.get('src', '')
        self.assertIn('google-icon', src.lower(),
                     "Googleアイコンのsrc属性が正しくありません")

    def test_facebook_login_button_exists(self):
        """RED: Facebookログインボタンが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        facebook_btn = panel.find('button', class_='facebook-btn')
        self.assertIsNotNone(facebook_btn, "class='facebook-btn' が見つかりません")
        expected_text = "Facebook でログイン"
        self.assertIn(expected_text, facebook_btn.get_text(),
                     f"Facebookボタンのテキストが正しくありません。期待値: '{expected_text}'")

    def test_facebook_button_has_onclick(self):
        """RED: Facebookボタンにonclickイベントが設定されているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        facebook_btn = panel.find('button', class_='facebook-btn')
        self.assertIsNotNone(facebook_btn)
        onclick = facebook_btn.get('onclick', '')
        self.assertIn('loginWithFacebook', onclick,
                     "Facebookボタンに 'loginWithFacebook()' イベントが設定されていません")

    def test_facebook_button_has_icon(self):
        """RED: Facebookボタンにアイコン画像が含まれているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        facebook_btn = panel.find('button', class_='facebook-btn')
        self.assertIsNotNone(facebook_btn)
        icon = facebook_btn.find('img')
        self.assertIsNotNone(icon, "Facebookボタン内にimgタグが見つかりません")
        src = icon.get('src', '')
        self.assertIn('facebook-icon', src.lower(),
                     "Facebookアイコンのsrc属性が正しくありません")

    def test_divider_exists(self):
        """RED: "または" 区切り線が存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        divider = panel.find('div', class_='divider')
        self.assertIsNotNone(divider, "class='divider' が見つかりません")
        expected_text = "または"
        self.assertIn(expected_text, divider.get_text(),
                     f"区切り線のテキストが正しくありません。期待値: '{expected_text}'")

    def test_email_input_exists(self):
        """RED: Email入力フィールドが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        email_input = panel.find('input', {'type': 'email', 'id': 'email-input'})
        self.assertIsNotNone(email_input, "type='email', id='email-input' のinputが見つかりません")

    def test_email_input_has_placeholder(self):
        """RED: Email入力フィールドにプレースホルダーが設定されているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        email_input = panel.find('input', id='email-input')
        self.assertIsNotNone(email_input)
        placeholder = email_input.get('placeholder', '')
        self.assertEqual(placeholder, "Email",
                        f"Email入力のプレースホルダーが正しくありません。期待値: 'Email'")

    def test_email_login_button_exists(self):
        """RED: "Sign in with Email" ボタンが存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        email_btn = panel.find('button', class_='email-btn')
        self.assertIsNotNone(email_btn, "class='email-btn' が見つかりません")
        expected_text = "Sign in with Email"
        self.assertIn(expected_text, email_btn.get_text(),
                     f"Emailログインボタンのテキストが正しくありません。期待値: '{expected_text}'")

    def test_email_button_has_onclick(self):
        """RED: Emailボタンにonclickイベントが設定されているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        email_btn = panel.find('button', class_='email-btn')
        self.assertIsNotNone(email_btn)
        onclick = email_btn.get('onclick', '')
        self.assertIn('loginWithEmail', onclick,
                     "Emailボタンに 'loginWithEmail()' イベントが設定されていません")

    def test_register_link_exists(self):
        """RED: 登録リンク "Don't have an account? Register" が存在するかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        self.assertIsNotNone(panel)
        register_link = panel.find('div', class_='register-link')
        self.assertIsNotNone(register_link, "class='register-link' が見つかりません")
        expected_text = "Don't have an account?"
        self.assertIn(expected_text, register_link.get_text(),
                     f"登録リンクのテキストが正しくありません。期待値: '{expected_text}'")

    def test_register_link_has_href(self):
        """RED: 登録リンクに正しいhref属性が設定されているかテスト"""
        panel = self.soup.find('div', id='login-mini-panel')
        register_div = panel.find('div', class_='register-link')
        self.assertIsNotNone(register_div)
        link = register_div.find('a')
        self.assertIsNotNone(link, "登録リンク内にaタグが見つかりません")
        href = link.get('href', '')
        expected_href = "/auth/email/register"
        self.assertEqual(href, expected_href,
                        f"登録リンクのhrefが正しくありません。期待値: '{expected_href}'")

    def test_login_panel_js_script_tag_exists(self):
        """RED: login-panel.js のscriptタグが存在するかテスト"""
        script_tags = self.soup.find_all('script')
        login_panel_js_found = False
        for script in script_tags:
            src = script.get('src', '')
            if 'login-panel.js' in src:
                login_panel_js_found = True
                break
        self.assertTrue(login_panel_js_found,
                       "login-panel.js のscriptタグが見つかりません")


if __name__ == '__main__':
    unittest.main()
