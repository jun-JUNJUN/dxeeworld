"""
Email Authentication Handlers
Task 5.3: メール認証新規登録フローの実装
Task 5.4: メール認証ログインフローの実装
"""
import json
import logging
import tornado.web
from urllib.parse import urlencode
from ..services.email_auth_service import EmailAuthService, EmailAuthError
from ..services.email_service import EmailService, EmailError
from ..services.identity_service import IdentityService
from ..services.oauth_session_service import OAuthSessionService
from ..services.auth_error_handler import AuthErrorHandler
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class EmailRegistrationHandler(BaseHandler):
    """メール認証新規登録ハンドラー - Task 5.3"""

    def initialize(self):
        """Initialize handler dependencies"""
        self.email_auth_service = EmailAuthService()
        self.email_service = EmailService()
        self.identity_service = IdentityService()
        self.session_service = OAuthSessionService()
        self.error_handler = AuthErrorHandler()

    def get(self):
        """Display email registration form"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Registration</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="email"], select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #0056b3; }
                .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
                .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            </style>
        </head>
        <body>
            <h1>メール認証で新規登録</h1>
            <form method="post" action="/auth/email/register">
                <div class="form-group">
                    <label for="email">メールアドレス:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="user_type">ユーザータイプ:</label>
                    <select id="user_type" name="user_type" required>
                        <option value="">選択してください</option>
                        <option value="user">一般ユーザー</option>
                        <option value="ally">協力者</option>
                    </select>
                </div>
                <button type="submit">確認メールを送信</button>
            </form>
            <p><a href="/auth/login">既にアカウントをお持ちの方はこちら</a></p>
        </body>
        </html>
        """
        self.write(html)

    async def post(self):
        """Process email registration request"""
        try:
            # Parse input data
            if self.request.headers.get('Content-Type', '').startswith('application/json'):
                data = json.loads(self.request.body)
            else:
                data = {
                    'email': self.get_argument('email'),
                    'user_type': self.get_argument('user_type', 'user')
                }

            email = data.get('email', '').strip().lower()
            user_type = data.get('user_type', 'user')

            # Validate input
            if not email:
                self._send_error_response(400, "メールアドレスが必要です")
                return

            # Validate email format
            from ..utils.email_validator import is_valid_email
            if not is_valid_email(email):
                self._send_error_response(400, "有効なメールアドレス形式ではありません")
                return

            if user_type not in ['user', 'ally']:
                self._send_error_response(400, "無効なユーザータイプです")
                return

            # Check if email already exists
            existing_identity = await self.identity_service.find_identity_by_email(email)
            if existing_identity.is_success:
                self._send_error_response(409, "このメールアドレスは既に登録されています")
                return

            # Generate verification token
            token_result = await self.email_auth_service.generate_verification_token(
                email, 'registration'
            )

            if not token_result.is_success:
                error_result = self.error_handler.handle_email_error(token_result.error)
                self._send_error_response(500, error_result.user_message)
                return

            # Create verification URL
            base_url = self.request.protocol + "://" + self.request.host
            verification_url = f"{base_url}/auth/email/verify?" + urlencode({
                'token': token_result.data['token'],
                'type': 'registration',
                'user_type': user_type
            })

            # Send verification email
            email_result = await self.email_service.send_verification_email(
                email, verification_url
            )

            if not email_result.is_success:
                error_result = self.error_handler.handle_email_error(email_result.error)
                self._send_error_response(500, error_result.user_message)
                return

            # Success response
            self._send_success_response({
                'message': '確認メールを送信しました。メールのリンクをクリックして登録を完了してください。',
                'email_masked': self._mask_email(email),
                'expires_in_hours': 1
            })

        except Exception as e:
            logger.exception("Email registration failed: %s", e)
            error_result = self.error_handler.make_user_friendly(e)
            self._send_error_response(500, error_result.user_message)

    def _mask_email(self, email: str) -> str:
        """Mask email for display"""
        if '@' in email:
            local, domain = email.split('@', 1)
            masked_local = local[:2] + '***' if len(local) > 2 else '***'
            return f"{masked_local}@{domain}"
        return '***'


class EmailVerificationHandler(BaseHandler):
    """メール認証確認ハンドラー - Task 5.3"""

    def initialize(self):
        """Initialize handler dependencies"""
        self.email_auth_service = EmailAuthService()
        self.identity_service = IdentityService()
        self.session_service = OAuthSessionService()
        self.error_handler = AuthErrorHandler()

    async def get(self):
        """Handle email verification link click"""
        try:
            token = self.get_argument('token', '')
            verification_type = self.get_argument('type', '')
            user_type = self.get_argument('user_type', 'user')

            if not token:
                self._render_verification_result(False, "認証トークンが見つかりません")
                return

            # Verify token
            verification_result = await self.email_auth_service.verify_verification_token(token)

            if not verification_result.is_success:
                error_result = self.error_handler.handle_email_error(verification_result.error)
                self._render_verification_result(False, error_result.user_message)
                return

            verification_data = verification_result.data
            email = verification_data.get('email')  # Note: This is currently mock data

            if verification_type == 'registration':
                # Create new Identity for registration
                identity_result = await self.identity_service.create_or_update_identity(
                    email, 'email', user_type
                )

                if not identity_result.is_success:
                    self._render_verification_result(False, "アカウント作成に失敗しました")
                    return

                identity = identity_result.data

                # Create session for immediate login
                session_result = await self.session_service.create_oauth_session(
                    identity,
                    self.request.headers.get('User-Agent', 'browser'),
                    self._get_client_ip()
                )

                if session_result.is_success:
                    session_id = session_result.data['session_id']
                    self.set_secure_cookie('session_id', session_id, expires_days=30)

                self._render_verification_result(
                    True,
                    "メールアドレスの確認が完了しました。登録とログインが完了しました。",
                    redirect_url="/"
                )

            else:
                self._render_verification_result(
                    True,
                    "メールアドレスの確認が完了しました。"
                )

        except Exception as e:
            logger.exception("Email verification failed: %s", e)
            error_result = self.error_handler.make_user_friendly(e)
            self._render_verification_result(False, error_result.user_message)

    def _render_verification_result(self, success: bool, message: str, redirect_url: str = None):
        """Render verification result page"""
        status_class = "success" if success else "error"
        status_text = "成功" if success else "エラー"

        redirect_script = ""
        if success and redirect_url:
            redirect_script = f"""
            <script>
                setTimeout(function() {{
                    window.location.href = '{redirect_url}';
                }}, 3000);
            </script>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>メール認証結果</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }}
                .result {{ padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .icon {{ font-size: 48px; margin-bottom: 15px; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
            {redirect_script}
        </head>
        <body>
            <div class="result {status_class}">
                <div class="icon">{'✓' if success else '✗'}</div>
                <h2>認証{status_text}</h2>
                <p>{message}</p>
                {f'<p>3秒後に自動的にリダイレクトします...</p>' if success and redirect_url else ''}
            </div>
            {f'<p><a href="{redirect_url}">今すぐ移動する</a></p>' if success and redirect_url else ''}
            <p><a href="/">ホームページに戻る</a></p>
        </body>
        </html>
        """
        self.write(html)


class EmailLoginHandler(BaseHandler):
    """メール認証ログインハンドラー - Task 5.4"""

    def initialize(self):
        """Initialize handler dependencies"""
        self.email_auth_service = EmailAuthService()
        self.email_service = EmailService()
        self.identity_service = IdentityService()
        self.session_service = OAuthSessionService()
        self.error_handler = AuthErrorHandler()

    def get(self):
        """Display email login form"""
        step = self.get_argument('step', 'email')
        email = self.get_argument('email', '')

        if step == 'code':
            self._render_code_form(email)
        else:
            self._render_email_form()

    def _render_email_form(self):
        """Render email input form"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Login</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="email"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #0056b3; }
                .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
                .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            </style>
        </head>
        <body>
            <h1>メール認証でログイン</h1>
            <div class="message info">
                <p>登録済みのメールアドレスを入力してください。6桁の認証コードをメールで送信します。</p>
            </div>
            <form method="post" action="/auth/email/login">
                <div class="form-group">
                    <label for="email">メールアドレス:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <button type="submit">認証コードを送信</button>
            </form>
            <p><a href="/auth/email/register">新規登録はこちら</a></p>
        </body>
        </html>
        """
        self.write(html)

    def _render_code_form(self, email: str):
        """Render verification code input form"""
        masked_email = self._mask_email(email)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>認証コード入力</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input[type="text"] {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; text-align: center; font-size: 18px; letter-spacing: 4px; }}
                button {{ background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
                button.secondary {{ background-color: #6c757d; }}
                button:hover {{ opacity: 0.9; }}
                .message {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
                .info {{ background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
                .countdown {{ font-size: 14px; color: #666; }}
            </style>
            <script>
                let timeLeft = 300; // 5 minutes
                function updateCountdown() {{
                    const minutes = Math.floor(timeLeft / 60);
                    const seconds = timeLeft % 60;
                    document.getElementById('countdown').textContent =
                        `残り時間: ${{minutes}}:${{seconds.toString().padStart(2, '0')}}`;
                    if (timeLeft > 0) {{
                        timeLeft--;
                        setTimeout(updateCountdown, 1000);
                    }} else {{
                        document.getElementById('countdown').textContent = '認証コードの有効期限が切れました';
                    }}
                }}
                window.onload = updateCountdown;
            </script>
        </head>
        <body>
            <h1>認証コード入力</h1>
            <div class="message info">
                <p><strong>{masked_email}</strong> に6桁の認証コードを送信しました。</p>
                <p>メールを確認して、認証コードを入力してください。</p>
                <div class="countdown" id="countdown"></div>
            </div>
            <form method="post" action="/auth/email/verify-code">
                <input type="hidden" name="email" value="{email}">
                <div class="form-group">
                    <label for="code">認証コード (6桁):</label>
                    <input type="text" id="code" name="code" maxlength="6" pattern="[0-9]{{6}}" required>
                </div>
                <button type="submit">ログイン</button>
                <button type="button" class="secondary" onclick="window.location.href='/auth/email/login'">戻る</button>
            </form>
            <form method="post" action="/auth/email/resend-code" style="margin-top: 20px;">
                <input type="hidden" name="email" value="{email}">
                <button type="submit" class="secondary">認証コードを再送信</button>
            </form>
        </body>
        </html>
        """
        self.write(html)

    async def post(self):
        """Process email login request (send code)"""
        try:
            # Parse input data
            if self.request.headers.get('Content-Type', '').startswith('application/json'):
                data = json.loads(self.request.body)
            else:
                data = {'email': self.get_argument('email')}

            email = data.get('email', '').strip().lower()

            if not email:
                self._send_error_response(400, "メールアドレスが必要です")
                return

            # Check if identity exists
            identity_result = await self.identity_service.find_identity_by_email(email)
            if not identity_result.is_success:
                # For security, don't reveal if email exists or not
                self._send_success_response({
                    'message': '認証コードを送信しました。メールを確認してください。',
                    'email_masked': self._mask_email(email),
                    'next_step': 'verify_code'
                })
                return

            # Generate login code
            code_result = await self.email_auth_service.generate_login_code(email)

            if not code_result.is_success:
                error_result = self.error_handler.handle_email_error(code_result.error)
                self._send_error_response(500, error_result.user_message)
                return

            # Send code via email
            email_result = await self.email_service.send_login_code_email(
                email, code_result.data['code']
            )

            if not email_result.is_success:
                error_result = self.error_handler.handle_email_error(email_result.error)
                self._send_error_response(500, error_result.user_message)
                return

            # Redirect to code verification page
            if self.request.headers.get('Content-Type', '').startswith('application/json'):
                self._send_success_response({
                    'message': '認証コードを送信しました。メールを確認してください。',
                    'email_masked': self._mask_email(email),
                    'next_step': 'verify_code',
                    'redirect_url': f'/auth/email/login?step=code&email={email}'
                })
            else:
                self.redirect(f'/auth/email/login?step=code&email={email}')

        except Exception as e:
            logger.exception("Email login failed: %s", e)
            error_result = self.error_handler.make_user_friendly(e)
            self._send_error_response(500, error_result.user_message)

    def _mask_email(self, email: str) -> str:
        """Mask email for display"""
        if '@' in email:
            local, domain = email.split('@', 1)
            masked_local = local[:2] + '***' if len(local) > 2 else '***'
            return f"{masked_local}@{domain}"
        return '***'


class EmailCodeVerificationHandler(BaseHandler):
    """メール認証コード確認ハンドラー - Task 5.4"""

    def initialize(self):
        """Initialize handler dependencies"""
        self.email_auth_service = EmailAuthService()
        self.identity_service = IdentityService()
        self.session_service = OAuthSessionService()
        self.error_handler = AuthErrorHandler()

    async def post(self):
        """Verify login code and create session"""
        try:
            # Parse input data
            if self.request.headers.get('Content-Type', '').startswith('application/json'):
                data = json.loads(self.request.body)
            else:
                data = {
                    'email': self.get_argument('email'),
                    'code': self.get_argument('code')
                }

            email = data.get('email', '').strip().lower()
            code = data.get('code', '').strip()

            if not email or not code:
                self._send_error_response(400, "メールアドレスと認証コードが必要です")
                return

            # Verify code
            verification_result = await self.email_auth_service.verify_login_code(email, code)

            if not verification_result.is_success:
                error_result = self.error_handler.handle_email_error(verification_result.error)
                self._send_error_response(400, error_result.user_message)
                return

            # Get identity
            identity_result = await self.identity_service.find_identity_by_email(email)
            if not identity_result.is_success:
                self._send_error_response(404, "ユーザーが見つかりません")
                return

            identity = identity_result.data

            # Create OAuth session
            session_result = await self.session_service.create_oauth_session(
                identity,
                self.request.headers.get('User-Agent', 'browser'),
                self._get_client_ip()
            )

            if not session_result.is_success:
                self._send_error_response(500, "セッション作成に失敗しました")
                return

            session_id = session_result.data['session_id']

            # Set session cookie
            self.set_secure_cookie('session_id', session_id, expires_days=30)

            # Success response
            self._send_success_response({
                'message': 'ログインが完了しました',
                'user': {
                    'id': identity['id'],
                    'email_masked': identity.get('email_masked'),
                    'user_type': identity.get('user_type'),
                    'auth_method': 'email'
                },
                'redirect_url': '/'
            })

        except Exception as e:
            logger.exception("Code verification failed: %s", e)
            error_result = self.error_handler.make_user_friendly(e)
            self._send_error_response(500, error_result.user_message)


class EmailCodeResendHandler(BaseHandler):
    """認証コード再送信ハンドラー - Task 5.4"""

    def initialize(self):
        """Initialize handler dependencies"""
        self.email_auth_service = EmailAuthService()
        self.email_service = EmailService()
        self.error_handler = AuthErrorHandler()

    async def post(self):
        """Resend login code"""
        try:
            email = self.get_argument('email', '').strip().lower()

            if not email:
                self._send_error_response(400, "メールアドレスが必要です")
                return

            # Generate new login code
            code_result = await self.email_auth_service.generate_login_code(email)

            if not code_result.is_success:
                error_result = self.error_handler.handle_email_error(code_result.error)
                self._send_error_response(500, error_result.user_message)
                return

            # Send code via email
            email_result = await self.email_service.send_login_code_email(
                email, code_result.data['code']
            )

            if not email_result.is_success:
                error_result = self.error_handler.handle_email_error(email_result.error)
                self._send_error_response(500, error_result.user_message)
                return

            # Redirect back to code form
            self.redirect(f'/auth/email/login?step=code&email={email}')

        except Exception as e:
            logger.exception("Code resend failed: %s", e)
            error_result = self.error_handler.make_user_friendly(e)
            self._send_error_response(500, error_result.user_message)