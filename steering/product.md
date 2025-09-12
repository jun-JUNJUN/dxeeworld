# Product Overview

## Product Overview

Kiro-style Spec Driven Development implementation using Claude Code CLI. This project provides a structured workflow system that guides AI development through three distinct phases: Requirements → Design → Tasks → Implementation. The system emphasizes thorough planning, human review, and systematic progress tracking to ensure high-quality software development outcomes.

## Core Features

- **三段階承認ワークフロー** - Requirements → Design → Tasks の段階的承認プロセス
- **Claude Code スラッシュコマンド統合** - `/kiro:` prefix でのコマンド体系
- **ステアリング文書管理** - プロジェクト全体のルールとコンテキスト自動管理
- **仕様書自動生成** - 機能ごとの正式な開発プロセス文書化
- **進捗状況追跡** - `spec-status` による現在のフェーズと進捗確認
- **インタラクティブ承認** - 各フェーズで人間によるレビューと承認を要求
- **カスタムステアリング** - 専門化されたコンテキスト用のカスタム設定
- **日本語思考プロセス** - 思考は英語、回答生成は日本語

## Target Use Cases

### 新機能開発
- 要件定義から設計、タスク化、実装まで体系的管理
- 人間のレビューポイントでの品質確保
- 段階的承認による開発リスク軽減

### 既存システム拡張  
- 現在のアーキテクチャパターンとの整合性確保
- 既存コードベースへの影響評価
- 段階的実装による影響範囲管理

### チーム開発協力
- 明確な開発ステージと成果物定義
- レビューポイントでのステークホルダー確認
- 進捗状況の可視化と共有

### AI支援開発
- Claude Code の capabilities を最大限活用
- 構造化されたプロンプトと文書管理
- 一貫性のある開発品質確保

## Key Value Proposition

### 体系的品質管理
従来のアドホックな AI 開発から、構造化された3段階承認プロセスによる品質管理へ移行。各段階で人間のレビューを必須とすることで、要件の見落としや設計の不備を早期発見。

### 開発効率向上
事前の要件・設計承認により、実装段階での手戻りを最小化。明確なタスク分解により、実装作業の並列化と進捗管理を容易化。

### 知識継承性
ステアリング文書とスペック文書による開発知識の体系的蓄積。プロジェクトコンテキストの自動管理により、AI とのインタラクション品質を継続的に向上。

### スケーラビリティ
小規模な機能追加から大規模なシステム変更まで、同一のワークフローで対応可能。カスタムステアリングにより、専門分野やプロジェクト特性に応じた柔軟な運用。