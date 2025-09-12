# Technology Stack

## Architecture

### Claude Code CLI Platform
- **Primary Platform**: Claude Code CLI による AI 支援開発環境
- **Command System**: Markdown ベースのスラッシュコマンド定義
- **Execution Model**: Claude Sonnet 4 を使用したインタラクティブ実行
- **File Management**: ローカルファイルシステムとの直接統合

### Document-Driven Configuration
- **Command Definitions**: `.claude/commands/` ディレクトリ内の Markdown ファイル
- **Steering Documents**: `.kiro/steering/` での自動生成・管理文書
- **Specifications**: `.kiro/specs/` での機能仕様書管理
- **Project Configuration**: `CLAUDE.md` による全体設定

## Frontend

**N/A** - CLI ベースツールのため GUI フロントエンドなし

## Backend

### Command Processing Engine
- **Language**: Claude Code 内蔵コマンドプロセッサ
- **Format**: Markdown フロントマター + 実行内容
- **Tool Integration**: Bash, Read, Write, Edit, MultiEdit, Glob, Grep 等
- **State Management**: ファイルシステムベースの状態管理

### Document Generation System
- **Template Engine**: 動的 Markdown 生成システム
- **Content Management**: Git 履歴追跡による変更管理
- **Validation**: インタラクティブ承認プロセス

## Development Environment

### Required Tools
- **Claude Code CLI**: 最新版必須
- **Git**: バージョン管理（推奨）
- **Text Editor**: Markdown 編集対応エディタ

### Setup Steps
```bash
# プロジェクト初期化
claude-code

# ステアリング文書作成
/kiro:steering

# 新機能仕様作成例
/kiro:spec-init [detailed feature description]
```

## Common Commands

### Core Kiro Commands
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

### File Operations
- **Read**: 既存文書読み取り
- **Write/Edit**: 文書作成・編集
- **Glob/Grep**: ファイル検索・パターンマッチング
- **Bash**: システムコマンド実行

## Environment Variables

### Project Configuration
- **Working Directory**: `/Users/jun77/Documents/Dropbox/a_root/code/sustainablee`
- **Steering Path**: `.kiro/steering/`
- **Specs Path**: `.kiro/specs/`
- **Commands Path**: `.claude/commands/`

### Development Settings
- **Language Mode**: 思考は英語、生成は日本語
- **Git Integration**: 自動検出（現在非 Git リポジトリ）
- **File Encoding**: UTF-8

## Port Configuration

**N/A** - CLI ツールのためポート使用なし

## Dependencies

### Core Dependencies
- **Claude Code Platform**: 最新安定版
- **Claude Sonnet 4**: AI モデル
- **Local File System**: 直接ファイル操作

### Optional Dependencies
- **Git**: バージョン管理・変更追跡
- **Text Editor**: Markdown プレビュー機能推奨
- **Shell Environment**: Bash 互換シェル

## Security Considerations

### Data Protection
- **Local Processing**: 全データはローカル環境で処理
- **No External APIs**: サードパーティサービス依存なし
- **File Permissions**: 標準ファイルシステム権限に依存

### Best Practices
- **Sensitive Data**: ステアリング文書に機密情報含めない
- **Access Control**: プロジェクトディレクトリの適切な権限設定
- **Backup**: 重要文書の定期バックアップ推奨