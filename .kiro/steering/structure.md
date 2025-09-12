# Project Structure

## Root Directory Organization

```
sustainablee/
├── .claude/              # Claude Code configuration and commands
│   └── commands/         # Custom slash commands definitions
│       └── kiro/         # Kiro workflow command suite
├── .kiro/               # Kiro framework files
│   ├── steering/        # Project steering documents (generated)
│   └── specs/           # Feature specifications (created per feature)
└── CLAUDE.md            # Main project configuration
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
機能ごとの仕様書（動的生成、現在は空）：

```
.kiro/specs/
└── [feature-name]/
    ├── requirements.md  # 要件定義書
    ├── design.md       # 設計文書
    └── tasks.md        # タスク分解書
```

## Code Organization Patterns

### Command Structure Pattern
各 Kiro コマンドは以下の構造に従う：

```markdown
---
description: [コマンドの説明]
allowed-tools: [使用可能ツールのリスト]
---

# [コマンド名]
[コマンドの詳細説明と実行内容]
```

### Document Generation Pattern
ステアリング文書は以下のパターンで生成・更新：

1. **既存ファイル検査** - 新規作成 vs 更新の判定
2. **プロジェクト分析** - ファイル構造・設定・変更履歴の調査
3. **内容生成/更新** - 検出された情報に基づく文書作成
4. **ユーザー設定保持** - 既存のカスタマイズ内容保護

### Specification Lifecycle Pattern
```
spec-init → spec-requirements → spec-design → spec-tasks → [implementation]
     ↓             ↓                ↓           ↓
  Initial       Requirements    Design      Task List
  Document      Generation      Review      Generation
```

## File Naming Conventions

### Command Files
- **Pattern**: `[action-category].md`
- **Examples**: `spec-init.md`, `validate-design.md`
- **Location**: `.claude/commands/kiro/`

### Steering Documents  
- **Pattern**: `[domain].md`
- **Standard Names**: `product.md`, `tech.md`, `structure.md`
- **Custom Names**: User-defined for specialized contexts
- **Location**: `.kiro/steering/`

### Specification Documents
- **Pattern**: `.kiro/specs/[feature-name]/[phase].md`
- **Phases**: `requirements.md`, `design.md`, `tasks.md`
- **Feature Names**: kebab-case, descriptive

## Import Organization

### Command Dependencies
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

### Document-Centric Architecture
全ての設定・仕様・進捗情報を Markdown 文書として管理。コード生成前の企画・設計段階に重点を置く。

### Phase-Gate Process
各開発段階で明確な成果物と承認プロセスを定義。前段階の承認なしに次段階へ進行させない。

### Context Preservation
ステアリング文書による一貫したプロジェクトコンテキスト維持。AI とのインタラクション品質向上。

### Incremental Documentation
プロジェクト変更に応じた文書の段階的更新。既存カスタマイズ内容の保護と新情報の追加。

### Tool Integration
Claude Code の native capabilities を最大限活用。外部依存を最小化した self-contained なワークフロー。

## Future Structure Considerations

### 実装フェーズでの展開予想
```
sustainablee/
├── src/                 # ソースコード（言語別）
├── tests/              # テスト
├── docs/               # プロジェクト文書
├── scripts/            # ビルド・デプロイスクリプト
└── config/             # 設定ファイル
```

### 多言語対応時の構造
```
.kiro/steering/
├── product.md          # 基本（日本語）
├── tech.md            
├── structure.md        
└── locale/             # 言語別カスタマイズ
    ├── en/
    └── zh/
```