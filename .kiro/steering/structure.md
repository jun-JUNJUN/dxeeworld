# Project Structure

## Root Directory Organization

```
dxeeworld/
├── .claude/              # Claude Code configuration and commands
│   └── commands/         # Custom slash commands definitions
│       └── kiro/         # Kiro workflow command suite
├── .kiro/               # Kiro framework files
│   ├── steering/        # Project steering documents (generated)
│   └── specs/           # Feature specifications (created per feature)
├── src/                 # Application source code
│   ├── handlers/        # HTTP request handlers (Controllers)
│   ├── models/          # Data models (MongoDB documents)
│   ├── services/        # Business logic services
│   ├── middleware/      # Authentication and access control
│   └── utils/           # Utility functions
├── templates/           # Jinja2 HTML templates
│   ├── companies/       # Company-related pages
│   ├── reviews/         # Review system pages
│   ├── jobs/           # Job listing pages
│   └── errors/         # Error pages
├── static/              # Static assets (CSS, JS, images)
│   ├── css/            # Stylesheets
│   │   └── main.css    # Main stylesheet
│   └── js/             # JavaScript files
│       ├── main.js     # Global navigation and user info
│       ├── reviewForm.js # Multilingual review form handling
│       └── login-panel.js # Authentication UI management
├── tests/               # Test suite
├── docs/                # Documentation files
│   ├── MIGRATION_MULTILINGUAL.md # Multilingual migration guide
│   └── MONGODB_STRUCTURE.md # Database structure documentation
├── pyproject.toml       # Python project configuration
├── run_server.py        # Server startup script
├── activate_server.sh   # Development server launcher
├── CLAUDE.md           # Main project configuration
├── README.md           # Project documentation
├── SETUP.md            # Setup and installation guide
└── TESTING_TRANSLATION_SERVICE.md # Translation service testing guide
```

## Subdirectory Structures

### `.claude/commands/kiro/` - Command Definitions
Kiro ワークフローの各段階を管理するコマンド群：

```
.claude/commands/kiro/
├── steering.md          # ステアリング文書管理コマンド
├── steering-custom.md   # カスタムステアリング作成
├── spec-init.md        # 仕様書初期化
├── spec-requirements.md # 要件定義生成
├── spec-design.md      # 設計文書生成  
├── spec-tasks.md       # タスク分解生成
├── spec-impl.md        # 実装支援
├── spec-status.md      # 進捗状況確認
├── validate-design.md  # 設計検証
└── validate-gap.md     # ギャップ分析
```

### `.kiro/steering/` - Project Context Documents
プロジェクト全体のコンテキスト文書（自動生成・管理）：

```
.kiro/steering/
├── product.md          # プロダクト概要・機能・価値提案
├── tech.md            # 技術スタック・開発環境・コマンド
└── structure.md       # プロジェクト構造・命名規則・パターン
```

### `.kiro/specs/` - Feature Specifications
機能ごとの仕様書（Kiro フレームワークによる動的生成）：

```
.kiro/specs/
├── startup-platform/       # Kaggle-like startup platform
├── company-listing/         # Company database with CSV import
├── company-reviews/         # Employee review system
├── oauth-authentication/    # OAuth services
└── ui-navigation-redesign/  # UI navigation cleanup
    ├── requirements.md      # 要件定義書
    ├── design.md           # 設計文書
    └── tasks.md            # タスク分解書
```

### `src/` - Application Source Code
Python Web アプリケーションのメインコード：

```
src/
├── app.py                  # Tornado application factory
├── config.py              # Configuration management
├── database.py            # MongoDB connection utilities
├── handlers/              # HTTP request handlers
│   ├── auth_handler.py    # Authentication (register, login)
│   ├── company_handler.py # Company CRUD operations
│   ├── review_handler.py  # Review system (create, edit, list, multilingual)
│   ├── email_auth_handler.py # Email verification system
│   ├── user_info_handler.py # User information and logout
│   ├── home_handler.py    # Landing page
│   └── health_handler.py  # Health check endpoint
├── models/                # Data models (MongoDB documents)
│   ├── user.py           # User model with authentication
│   ├── company.py        # Company data model
│   ├── review.py         # Review model with 7-point rating (multilingual)
│   ├── review_history.py # Review edit history tracking
│   └── job.py            # Job listings model
├── services/              # Business logic services
│   ├── auth_service.py   # Authentication business logic
│   ├── company_service.py # Company data management
│   ├── review_service.py # Review calculation and management
│   ├── review_submission_service.py # Review creation and validation
│   ├── translation_service.py # Multilingual translation (EN/ZH/JA)
│   ├── i18n_form_service.py # Internationalized form handling
│   ├── search_service.py # Search functionality
│   ├── oauth_service.py  # OAuth integration
│   ├── oauth_session_service.py # OAuth session management
│   └── email_auth_service.py # Email authentication and verification
├── middleware/            # Request processing middleware
│   ├── auth_middleware.py # Session management
│   └── access_control_middleware.py # Authorization
├── tools/                 # Data import/export tools
│   ├── csv_import_tool.py # Company data CSV import
│   ├── migrate_multilingual.py # Multilingual data migration
│   └── show_mongodb_structure.py # Database structure inspection
└── utils/                 # Utility functions
    └── result.py         # Result wrapper classes
```

### `templates/` - HTML Templates
Jinja2 template files with responsive design：

```
templates/
├── base.html             # Base template with navigation
├── home.html            # Landing page
├── companies/           # Company-related pages
│   ├── list.html        # Company listings with filters
│   └── detail.html      # Company detail with reviews
├── reviews/             # Review system pages
│   ├── list.html        # Review listings with filtering
│   ├── create.html      # Review creation form (multilingual)
│   ├── confirm.html     # Review confirmation page (multilingual)
│   └── edit.html        # Review editing interface
├── jobs/                # Job listing pages
│   └── list.html        # Job search and listings
└── errors/              # Error pages
    ├── 404.html         # Not found
    └── 500.html         # Server error
```

### `tests/` - Test Suite
包括的なテストスイート（61 test files）：

```
tests/
├── test_*.py            # Individual feature tests
├── test_auth_*.py       # Authentication tests
├── test_company_*.py    # Company feature tests
├── test_review_*.py     # Review system tests
├── test_oauth_*.py      # OAuth integration tests
├── test_ui_*.py         # UI component tests
└── test_mobile_*.py     # Mobile responsiveness tests
```

## Code Organization Patterns

### MVC Architecture Pattern
Tornado フレームワークに基づく MVC パターン：

- **Models** (`src/models/`): MongoDB document models with validation
- **Views** (`templates/`): Jinja2 templates with responsive design
- **Controllers** (`src/handlers/`): HTTP request handlers with async support
- **Services** (`src/services/`): Business logic separation
- **Middleware** (`src/middleware/`): Cross-cutting concerns (auth, validation)

### Async/Await Pattern
非同期プログラミングによる高性能 Web アプリケーション：

```python
class CompanyHandler(BaseHandler):
    async def get(self, company_id):
        company = await self.company_service.get_by_id(company_id)
        reviews = await self.review_service.get_by_company(company_id)
        self.render('companies/detail.html', company=company, reviews=reviews)
```

### Service Layer Pattern
ビジネスロジックとデータアクセスの分離：

```python
# Service handles business logic
class ReviewService:
    async def calculate_average_rating(self, company_id):
        reviews = await self.review_model.find_by_company(company_id)
        return sum(r.overall_rating for r in reviews) / len(reviews)

# Handler coordinates request/response
class ReviewHandler:
    async def post(self):
        data = self.get_json_body()
        review = await self.review_service.create_review(data)
        self.write_json({'review_id': str(review.id)})
```

### Development Framework Patterns (Kiro)

#### Command Structure Pattern
各 Kiro コマンドは以下の構造に従う：

```markdown
---
description: [コマンドの説明]
allowed-tools: [使用可能ツールのリスト]
---

# [コマンド名]
[コマンドの詳細説明と実行内容]
```

#### Specification Lifecycle Pattern
```
spec-init → spec-requirements → spec-design → spec-tasks → [implementation]
     ↓             ↓                ↓           ↓
  Initial       Requirements    Design      Task List
  Document      Generation      Review      Generation
```

## File Naming Conventions

### Python Source Files
- **Pattern**: `snake_case.py`
- **Examples**: `company_handler.py`, `review_service.py`, `oauth_middleware.py`
- **Test Files**: `test_[module_name].py`
- **Location**: `src/` and `tests/`

### Template Files
- **Pattern**: `[page_name].html`
- **Examples**: `company_list.html`, `review_create.html`
- **Base Templates**: `base.html` for common layout
- **Location**: `templates/[feature]/`

### Static Assets
- **CSS**: `snake_case.css` in `static/css/`
  - `main.css`: Core styling and responsive design
- **JavaScript**: `camelCase.js` in `static/js/`
  - `main.js`: Global navigation and user info display
  - `reviewForm.js`: Multilingual review form handling
  - `login-panel.js`: Authentication UI management
- **Images**: descriptive names in `static/images/`

### Development Framework Files

#### Command Files
- **Pattern**: `[action-category].md`
- **Examples**: `spec-init.md`, `validate-design.md`
- **Location**: `.claude/commands/kiro/`

#### Steering Documents
- **Pattern**: `[domain].md`
- **Standard Names**: `product.md`, `tech.md`, `structure.md`
- **Custom Names**: User-defined for specialized contexts
- **Location**: `.kiro/steering/`

#### Specification Documents
- **Pattern**: `.kiro/specs/[feature-name]/[phase].md`
- **Phases**: `requirements.md`, `design.md`, `tasks.md`
- **Feature Names**: kebab-case, descriptive

## Import Organization

### Python Import Standards
Python コードのインポート順序 (PEP 8 準拠)：

```python
# 1. Standard library imports
import os
import logging
from datetime import datetime

# 2. Third-party imports
import tornado.web
import motor.motor_tornado
from bson import ObjectId

# 3. Local application imports
from .models.user import User
from .services.auth_service import AuthService
from .utils.result import Result
```

### Template Inheritance
Jinja2 テンプレートの継承パターン：

```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>{% block head %}{% endblock %}</head>
<body>{% block content %}{% endblock %}</body>
</html>

<!-- companies/list.html -->
{% extends "base.html" %}
{% block content %}
<div class="company-list">...</div>
{% endblock %}
```

### Configuration Dependencies
アプリケーション設定の依存関係：

```python
# config.py - Environment-based configuration
from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URL = getenv('MONGODB_URL', 'mongodb://localhost:27017')
    SECRET_KEY = getenv('SECRET_KEY')
    GOOGLE_CLIENT_ID = getenv('GOOGLE_CLIENT_ID')
```

### Development Framework Dependencies
Claude Code コマンドは以下のツールに依存：

- **File Operations**: Read, Write, Edit, MultiEdit
- **Search**: Glob, Grep
- **System**: Bash
- **Navigation**: LS

### Document References
ステアリング文書間の参照パターン：

- **Cross-references**: `@filename.md` syntax
- **Command references**: `/kiro:command-name` format
- **Path references**: Relative paths from project root

## Key Architectural Principles

### Web Application Architecture

#### Async-First Design
非同期プログラミングによる高性能・高スループット実現。MongoDB との非同期通信、並行リクエスト処理をサポート。

#### Security by Design
認証・認可・暗号化をアーキテクチャレベルで組み込み。OAuth 2.0、bcrypt、CSRF protection、secure session management を標準実装。

#### Responsive & Mobile-First
Kaggle-inspired UI/UX with mobile-first responsive design。デスクトップ・タブレット・スマートフォンでの一貫したユーザー体験。

#### Modular Service Architecture
Handler → Service → Model の明確な責任分離。ビジネスロジックの独立性とテスタビリティを重視。

#### Data-Driven Features
CSV インポート、検索・フィルタリング、レビュー集計など、データ処理機能を中核とした設計。

### Development Framework Architecture (Kiro)

#### Document-Centric Development
全ての設定・仕様・進捗情報を Markdown 文書として管理。コード生成前の企画・設計段階に重点を置く。

#### Phase-Gate Process
各開発段階で明確な成果物と承認プロセスを定義。前段階の承認なしに次段階へ進行させない。

#### Context Preservation
ステアリング文書による一貫したプロジェクトコンテキスト維持。AI とのインタラクション品質向上。

#### Incremental Documentation
プロジェクト変更に応じた文書の段階的更新。既存カスタマイズ内容の保護と新情報の追加。

#### Tool Integration
Claude Code の native capabilities を最大限活用。外部依存を最小化した self-contained なワークフロー。

## Future Structure Considerations

### Scalability Enhancements
```
dxeeworld/
├── src/
│   ├── api/            # REST API endpoints
│   ├── admin/          # Admin interface
│   ├── background/     # Background tasks (Celery)
│   └── integrations/   # External service integrations
├── migrations/         # Database migration scripts
├── docker/             # Container configurations
├── docs/              # API documentation
├── scripts/           # Deployment and maintenance scripts
└── monitoring/        # Logging and metrics configuration
```

### Multi-Language Platform Support
```
templates/
├── base.html
├── ja/                # Japanese templates (current)
├── en/                # English templates
└── zh/                # Chinese templates

static/
├── css/
├── js/
└── i18n/              # Internationalization files
    ├── ja.json
    ├── en.json
    └── zh.json
```

### Development Framework Evolution
```
.kiro/
├── steering/
│   ├── product.md      # 基本（日本語）
│   ├── tech.md
│   ├── structure.md
│   └── locale/         # 言語別カスタマイズ
│       ├── en/
│       └── zh/
├── specs/
└── workflows/          # CI/CD workflow definitions
    ├── test.yml
    ├── deploy.yml
    └── security.yml
```

### Performance Optimization Structure
```
src/
├── cache/             # Redis caching layer
├── search/            # Elasticsearch integration
├── cdn/               # CDN asset management
└── analytics/         # User behavior analytics
```