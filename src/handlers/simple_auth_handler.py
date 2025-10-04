"""
簡単な認証ハンドラー（テスト用）
"""
import tornado.web
from .base_handler import BaseHandler
from ..services.session_service import SessionService


class SimpleLoginHandler(BaseHandler):
    """簡単なログインハンドラー（テスト用）"""

    def get(self):
        """ログインフォーム表示"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>簡単ログイン</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
                input, button { display: block; width: 100%; margin: 10px 0; padding: 10px; }
                button { background: #007bff; color: white; border: none; cursor: pointer; }
                button:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <h1>簡単ログイン（テスト用）</h1>
            <form method="post" action="/simple-login">
                <input type="email" name="email" placeholder="メールアドレス" required>
                <input type="text" name="name" placeholder="名前" required>
                <button type="submit">ログイン</button>
            </form>
            <p><small>テスト用：任意のメールアドレスと名前でログインできます</small></p>
        </body>
        </html>
        """
        self.write(html)

    async def post(self):
        """簡単ログイン処理"""
        try:
            email = self.get_argument('email')
            name = self.get_argument('name')

            # 簡単なユーザーオブジェクトを作成（テスト用）
            class SimpleUser:
                def __init__(self, email, name):
                    self.id = email  # メールアドレスをIDとして使用
                    self.email = email
                    self.name = name

            user = SimpleUser(email, name)

            # セッション作成
            session_service = SessionService()
            user_agent = self.request.headers.get('User-Agent', '')
            ip_address = self.get_client_ip()

            session_result = await session_service.create_session(user, user_agent, ip_address)

            if not session_result.is_success:
                self.set_status(500)
                self.write("セッション作成に失敗しました")
                return

            session_id = session_result.data

            # セッションクッキー設定
            self.set_secure_cookie('session_id', session_id, expires_days=1)

            # 成功ページ
            self.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ログイン成功</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }}
                    .success {{ color: green; }}
                    a {{ color: #007bff; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1 class="success">ログイン成功！</h1>
                <p>ようこそ、{name}さん</p>
                <p>メールアドレス: {email}</p>
                <p><a href="/review">レビュー一覧を見る</a></p>
                <p><a href="/companies">企業一覧を見る</a></p>
                <p><a href="/simple-logout">ログアウト</a></p>
            </body>
            </html>
            """)

        except Exception as e:
            self.set_status(500)
            self.write(f"エラーが発生しました: {e}")


class SimpleLogoutHandler(BaseHandler):
    """簡単なログアウトハンドラー（テスト用）"""

    async def get(self):
        """ログアウト処理"""
        try:
            # セッション無効化
            session_id = self.get_secure_cookie('session_id')
            if session_id:
                session_id = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
                session_service = SessionService()
                await session_service.invalidate_session(session_id)

            # セッションクッキークリア
            self.clear_cookie('session_id')

            # ログアウト成功ページ
            self.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ログアウト</title>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; text-align: center; }
                    .success { color: green; }
                    a { color: #007bff; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1 class="success">ログアウトしました</h1>
                <p><a href="/simple-login">再度ログイン</a></p>
                <p><a href="/">ホームページに戻る</a></p>
            </body>
            </html>
            """)

        except Exception as e:
            self.set_status(500)
            self.write(f"エラーが発生しました: {e}")