"""
Unified Authentication Handler
統合認証ページハンドラー - Google OAuth, Facebook OAuth, メール認証を統合
"""
import logging
import tornado.web
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class UnifiedLoginHandler(BaseHandler):
    """統合ログインページハンドラー"""

    def get(self):
        """統合ログインページを表示"""
        return_url = self.get_argument('return_url', '/')

        # ログインパネルのCSSとJSを読み込む
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ログイン - DxeeWorld</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="/static/css/login-panel.css">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    padding: 20px;
                }}
                .login-container {{
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    padding: 40px;
                    max-width: 450px;
                    width: 100%;
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 30px;
                    font-size: 28px;
                }}
                .auth-options {{
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }}
                .auth-button {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 14px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    color: white;
                }}
                .auth-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                .google-btn {{
                    background-color: #4285f4;
                }}
                .google-btn:hover {{
                    background-color: #357ae8;
                }}
                .facebook-btn {{
                    background-color: #1877f2;
                }}
                .facebook-btn:hover {{
                    background-color: #166fe5;
                }}
                .email-btn {{
                    background-color: #34a853;
                }}
                .email-btn:hover {{
                    background-color: #2d9449;
                }}
                .divider {{
                    display: flex;
                    align-items: center;
                    text-align: center;
                    margin: 25px 0;
                    color: #999;
                }}
                .divider::before,
                .divider::after {{
                    content: '';
                    flex: 1;
                    border-bottom: 1px solid #ddd;
                }}
                .divider span {{
                    padding: 0 15px;
                    font-size: 14px;
                }}
                .register-link {{
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                    font-size: 14px;
                }}
                .register-link a {{
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .register-link a:hover {{
                    text-decoration: underline;
                }}
                .icon {{
                    margin-right: 10px;
                    font-size: 20px;
                }}
                .home-link {{
                    text-align: center;
                    margin-top: 15px;
                }}
                .home-link a {{
                    color: #667eea;
                    text-decoration: none;
                    font-size: 14px;
                }}
                .home-link a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>DxeeWorld にログイン</h1>

                <div class="auth-options">
                    <a href="/auth/google?return_url={return_url}" class="auth-button google-btn">
                        <span class="icon">G</span>
                        Google でログイン
                    </a>

                    <a href="/auth/facebook?return_url={return_url}" class="auth-button facebook-btn">
                        <span class="icon">f</span>
                        Facebook でログイン
                    </a>

                    <div class="divider">
                        <span>または</span>
                    </div>

                    <a href="/auth/email/login?return_url={return_url}" class="auth-button email-btn">
                        <span class="icon">✉</span>
                        メールアドレスでログイン
                    </a>
                </div>

                <div class="register-link">
                    アカウントをお持ちでない方は<br>
                    <a href="/auth/email/register?return_url={return_url}">新規登録はこちら</a>
                </div>

                <div class="home-link">
                    <a href="/">← ホームに戻る</a>
                </div>
            </div>
        </body>
        </html>
        """
        self.write(html)


class UnifiedLogoutHandler(BaseHandler):
    """統合ログアウトハンドラー"""

    def initialize(self):
        """Initialize handler dependencies"""
        from ..services.oauth_session_service import OAuthSessionService
        self.session_service = OAuthSessionService()

    async def get(self):
        """ログアウト処理 (GETリクエスト)"""
        await self._logout()

    async def post(self):
        """ログアウト処理 (POSTリクエスト)"""
        await self._logout()

    async def _logout(self):
        """共通ログアウト処理"""
        try:
            # セッションID取得
            session_id = self.get_secure_cookie('session_id')
            if session_id:
                session_id = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id

                # OAuth セッション無効化
                await self.session_service.logout_session(session_id)

            # セッションクッキークリア
            self.clear_cookie('session_id')

            # ホームページにリダイレクト
            self.redirect('/')

        except Exception as e:
            logger.exception("Logout error: %s", e)
            self.redirect('/')
