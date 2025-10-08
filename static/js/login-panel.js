/**
 * Login Mini Panel JavaScript Controller
 * Task 5.3: Mini Panel JavaScript制御
 */

class LoginPanel {
    constructor() {
        this.panel = document.getElementById('login-mini-panel');
        this.emailInput = document.getElementById('email-input');
        this.closeBtn = this.panel?.querySelector('.close-btn');
        this.registerLink = document.getElementById('register-link');

        this.init();
    }

    init() {
        if (!this.panel) return;

        // Close button event
        this.closeBtn?.addEventListener('click', () => this.hide());

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (e.target === this.panel) {
                this.hide();
            }
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible()) {
                this.hide();
            }
        });

        // Register link with return_url
        if (this.registerLink) {
            this.registerLink.addEventListener('click', (e) => {
                e.preventDefault();
                const returnUrl = encodeURIComponent(window.location.href);
                window.location.href = `/auth/email/register?return_url=${returnUrl}`;
            });
        }

        // Auto-show if showLoginPanel variable is set
        if (window.showLoginPanel === true) {
            this.show();
        }
    }

    show() {
        if (!this.panel) return;

        this.panel.style.display = 'block';
        this.panel.setAttribute('aria-hidden', 'false');

        // Focus on email input
        setTimeout(() => {
            this.emailInput?.focus();
        }, 100);
    }

    hide() {
        if (!this.panel) return;

        this.panel.style.display = 'none';
        this.panel.setAttribute('aria-hidden', 'true');
    }

    isVisible() {
        return this.panel && this.panel.style.display !== 'none';
    }

    setLoading(loading) {
        if (!this.panel) return;

        if (loading) {
            this.panel.classList.add('loading');
        } else {
            this.panel.classList.remove('loading');
        }
    }

    showError(message) {
        // Create error message element if it doesn't exist
        let errorEl = this.panel?.querySelector('.error-message');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'error-message';
            errorEl.style.cssText = 'color: #f44336; font-size: 12px; margin-top: 8px; text-align: center;';
            this.panel?.querySelector('.panel-body')?.appendChild(errorEl);
        }
        errorEl.textContent = message;
        errorEl.style.display = 'block';

        // Hide error after 5 seconds
        setTimeout(() => {
            if (errorEl) errorEl.style.display = 'none';
        }, 5000);
    }
}

// Global functions for button clicks
async function loginWithGoogle() {
    window.location.href = '/auth/google/login';
}

async function loginWithFacebook() {
    window.location.href = '/auth/facebook/login';
}

async function loginWithEmail() {
    const panel = window.loginPanel;
    if (!panel) return;

    const emailInput = document.getElementById('email-input');
    const email = emailInput?.value.trim();

    if (!email) {
        panel.showError('メールアドレスを入力してください');
        return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        panel.showError('有効なメールアドレス形式ではありません');
        return;
    }

    panel.setLoading(true);

    try {
        const response = await fetch('/auth/email/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Redirect to code verification page
            window.location.href = data.redirect_url || `/auth/email/login?step=code&email=${encodeURIComponent(email)}`;
        } else {
            panel.showError(data.error || 'ログインに失敗しました');
        }
    } catch (error) {
        console.error('Login error:', error);
        panel.showError('ネットワークエラーが発生しました');
    } finally {
        panel.setLoading(false);
    }
}

// Initialize login panel on page load
document.addEventListener('DOMContentLoaded', () => {
    window.loginPanel = new LoginPanel();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LoginPanel, loginWithEmail, loginWithGoogle, loginWithFacebook };
}
