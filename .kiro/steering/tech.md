# Technology Stack

## Architecture

### Web Application Architecture
- **Framework**: Tornado 6.5.2 - 高性能 Python Web フレームワーク
- **Database**: MongoDB 7.0+ with Motor (非同期ドライバー)
- **Authentication**: OAuth 2.0 (Google, Facebook) + Email verification
- **Session Management**: Secure cookie-based sessions with encryption
- **Template Engine**: Jinja2 3.1.3 - サーバーサイドレンダリング

### Development Framework (Kiro)
- **Command System**: Markdown ベースのスラッシュコマンド定義
- **AI Platform**: Claude Sonnet 4 を使用したインタラクティブ開発
- **Steering Documents**: `.kiro/steering/` での自動生成・管理文書
- **Specifications**: `.kiro/specs/` での機能仕様書管理
- **Project Configuration**: `CLAUDE.md` による全体設定

## Frontend

### User Interface
- **Design Framework**: Kaggle-inspired responsive design
- **Template System**: Jinja2 templates with base template inheritance
- **Styling**: Custom CSS with mobile-first responsive layout
- **JavaScript**: Vanilla JavaScript for interactive features
- **Static Assets**: CSS/JS served via Tornado static file handler

### Page Structure
```
templates/
├── base.html           # Base template with navigation
├── home.html          # Landing page
├── companies/         # Company-related pages
│   ├── list.html      # Company listings with filters
│   └── detail.html    # Company detail pages
├── reviews/           # Review system pages
│   ├── list.html      # Review listings
│   ├── create.html    # Review creation form
│   └── edit.html      # Review editing
├── jobs/              # Job listings
└── errors/            # Error pages
```

## Backend

### Web Application (Python 3.9+)
- **Language**: Python with asyncio support
- **Framework**: Tornado 6.5.2 - 非同期 Web サーバー
- **Database**: Motor 3.6.0+ (MongoDB 非同期ドライバー)
- **Authentication**: bcrypt 4.1.2 for password hashing
- **Security**: cryptography 41.0.7+ for encryption, CSRF protection

### Application Structure
```
src/
├── app.py                # Main application entry point
├── config.py            # Configuration management
├── database.py          # MongoDB connection and utilities
├── handlers/            # Request handlers (MVC Controllers)
│   ├── auth_handler.py  # Authentication endpoints
│   ├── company_handler.py # Company CRUD operations
│   ├── review_handler.py  # Review system
│   └── email_auth_handler.py # Email verification
├── models/              # Data models
│   ├── user.py          # User model with authentication
│   ├── company.py       # Company data model
│   ├── review.py        # Review model with 7-point rating
│   └── job.py           # Job listings model
├── services/            # Business logic services
├── middleware/          # Authentication and access control
└── utils/               # Utility functions
```

### Development Framework (Kiro)
- **Command Processing**: Claude Code 内蔵コマンドプロセッサ
- **Document Management**: Git 履歴追跡による変更管理
- **Validation**: インタラクティブ承認プロセス

## Development Environment

### Required Tools
- **Claude Code CLI**: 最新版必須
- **Git**: バージョン管理（推奨）
- **Text Editor**: Markdown 編集対応エディタ

### Setup Steps
```bash
# 依存関係インストール (推奨: uv)
uv sync

# 環境設定
cp .env.example .env
# .env ファイルを編集して適切な値を設定

# MongoDB 起動
docker run -d -p 27017:27017 --name mongodb mongo:latest

# サーバー起動
./activate_server.sh
# または
uv run python run_server.py

# テスト実行
./activate_server.sh test
# または
uv run pytest
```

## Common Commands

### Application Management
```bash
# サーバー起動
./activate_server.sh              # 推奨起動方法
uv run python run_server.py      # 直接起動

# テスト実行
./activate_server.sh test         # テストスイート実行
uv run pytest                    # 直接 pytest 実行
uv run pytest tests/test_*.py    # 特定テスト実行

# 開発ツール
uv run ruff check                # コード品質チェック
uv run black .                   # コードフォーマット
uv run mypy src/                 # 型チェック
```

### Development Commands (Kiro Framework)
```bash
# ステアリング管理
/kiro:steering                    # 基本ステアリング文書作成・更新
/kiro:steering-custom            # カスタムステアリング作成

# 仕様書管理
/kiro:spec-init [description]    # 新仕様書初期化
/kiro:spec-requirements [feature] # 要件定義生成
/kiro:spec-design [feature]      # 設計文書生成
/kiro:spec-tasks [feature]       # タスク分解生成
/kiro:spec-status [feature]      # 進捗状況確認

# 検証コマンド
/kiro:validate-design [feature]  # 設計検証
/kiro:validate-gap [feature]     # ギャップ分析
```

## Environment Variables

### Application Configuration (.env)
```bash
# Server Settings
PORT=8202                         # Web server port
DEBUG=True                        # Development mode
SECRET_KEY=your-secret-key        # Session encryption key

# Database
MONGODB_URL=mongodb://localhost:27017/dxeeworld
MONGODB_DATABASE=dxeeworld

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Development Framework Settings
- **Working Directory**: `/Users/jun77/Documents/Dropbox/a_root/code/dxeeworld`
- **Steering Path**: `.kiro/steering/`
- **Specs Path**: `.kiro/specs/`
- **Commands Path**: `.claude/commands/`
- **Language Mode**: 思考は英語、生成は日本語
- **Git Integration**: 自動検出
- **File Encoding**: UTF-8

## Port Configuration

### Application Ports
- **Web Server**: 8202 (default) - Tornado HTTP server
- **MongoDB**: 27017 (default) - Database server
- **Development**: 開発時は localhost:8202 でアクセス

### Service Endpoints
```
http://localhost:8202/            # Home page
http://localhost:8202/companies   # Company listings
http://localhost:8202/reviews     # Review system
http://localhost:8202/jobs        # Job listings
http://localhost:8202/login       # Authentication
http://localhost:8202/health      # Health check
```

## Dependencies

### Production Dependencies (pyproject.toml)
```toml
tornado = "6.5.2"               # Web framework
motor = ">=3.6.0"               # MongoDB async driver
bcrypt = "4.1.2"                # Password hashing
jinja2 = "3.1.3"                # Template engine
python-dotenv = "1.0.0"         # Environment variables
requests-oauthlib = ">=1.3.1"   # OAuth client
itsdangerous = ">=2.1.2"        # Secure tokens
email-validator = ">=2.0.0"     # Email validation
cryptography = ">=41.0.7"       # Encryption
```

### Development Dependencies
```toml
pytest = "7.4.4"                # Testing framework
pytest-asyncio = "0.21.1"       # Async test support
pytest-tornado = "0.8.1"        # Tornado test integration
ruff                             # Linting and formatting
black                            # Code formatter
mypy                             # Type checking
```

### External Services
- **MongoDB 7.0+**: Database server
- **SMTP Server**: Email delivery (Gmail, SendGrid, etc.)
- **OAuth Providers**: Google, Facebook APIs
- **Claude Code Platform**: Development framework
- **Git**: バージョン管理・変更追跡

## Security Considerations

### Data Protection
- **Local Processing**: 全データはローカル環境で処理
- **No External APIs**: サードパーティサービス依存なし
- **File Permissions**: 標準ファイルシステム権限に依存

### Best Practices
- **Environment Variables**: `.env` ファイルで機密情報管理、Git 追跡対象外
- **Password Security**: bcrypt による安全なハッシュ化、平文保存禁止
- **Session Security**: 暗号化されたセッションクッキー、CSRF 保護
- **Database Security**: MongoDB 接続の認証設定、適切なインデックス
- **OAuth Security**: HTTPS 必須、state パラメータ検証
- **Input Validation**: 全入力データのサニタイゼーション
- **Error Handling**: 機密情報を含まないエラーレスポンス
- **Development Secrets**: ステアリング文書に機密情報含めない
- **Backup**: データベースとアプリケーション設定の定期バックアップ