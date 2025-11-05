# 環境変数設定ガイド

## 概要

このガイドでは、レビュー投稿・多言語翻訳機能に必要な環境変数の設定方法を説明します。

---

## 目次

1. [必須環境変数](#必須環境変数)
2. [DeepL API設定](#deepl-api設定)
3. [オプション環境変数](#オプション環境変数)
4. [環境別設定例](#環境別設定例)
5. [トラブルシューティング](#トラブルシューティング)

---

## 必須環境変数

### DEEPL_API_KEY

DeepL翻訳APIの認証キーです。

**設定方法**:

1. `.env` ファイルに追加:
```bash
DEEPL_API_KEY=your-deepl-api-key-here
```

2. または環境変数として設定:
```bash
export DEEPL_API_KEY=your-deepl-api-key-here
```

**取得方法**:

1. [DeepL API ウェブサイト](https://www.deepl.com/pro-api)にアクセス
2. アカウントを作成（Free版またはPro版）
3. APIキーをコピー

**注意事項**:
- APIキーは秘密情報です。`.env` ファイルを `.gitignore` に追加してください
- 本番環境では環境変数として設定することを推奨します
- APIキーが設定されていない場合、アプリケーション起動時にエラーが発生します

---

## DeepL API設定

### Free版 vs Pro版の選択

DeepL APIには2つのプランがあります。

#### Free版（無料）

**特徴**:
- 月間500,000文字まで無料
- APIエンドポイント: `https://api-free.deepl.com/v2`
- クレジットカード登録不要

**適用シーン**:
- 開発環境
- 小規模プロジェクト
- プロトタイピング

**設定例**:
```bash
DEEPL_API_KEY=your-free-api-key:fx
DEEPL_API_BASE_URL=https://api-free.deepl.com/v2
```

#### Pro版（有料）

**特徴**:
- 月額料金: 約$25/100万文字
- 無制限の翻訳文字数（従量課金）
- APIエンドポイント: `https://api.deepl.com/v2`
- より高速なレスポンス
- SLAサポート

**適用シーン**:
- 本番環境
- 大規模プロジェクト
- 高トラフィックアプリケーション

**設定例**:
```bash
DEEPL_API_KEY=your-pro-api-key
DEEPL_API_BASE_URL=https://api.deepl.com/v2
```

### APIエンドポイントの設定

**DEEPL_API_BASE_URL** (オプション)

デフォルト値: `https://api-free.deepl.com/v2`

Pro版を使用する場合は明示的に設定してください:

```bash
DEEPL_API_BASE_URL=https://api.deepl.com/v2
```

---

## オプション環境変数

### アクセス制御設定

**ACCESS_CONTROL_RULES** (オプション)

URLパターンごとのアクセス制御ルールを定義します。

**フォーマット**:
```
pattern1,permission1,permission2;pattern2,permission1
```

**例**:
```bash
ACCESS_CONTROL_RULES="/reviews/new,user,admin;/admin,admin"
```

**説明**:
- `/reviews/new`: `user` または `admin` 権限が必要
- `/admin`: `admin` 権限が必要

**ACCESS_CONTROL_RELOAD_INTERVAL** (オプション)

アクセス制御設定の再読み込み間隔（秒）。

**デフォルト値**: `30`

```bash
ACCESS_CONTROL_RELOAD_INTERVAL=60
```

### データベース設定

**MONGODB_URI** (必須)

MongoDB接続文字列。

```bash
MONGODB_URI=mongodb://localhost:27017/dxeeworld
```

### セッション設定

**SESSION_SECRET** (必須)

セッションの暗号化に使用する秘密鍵。

```bash
SESSION_SECRET=your-very-long-random-secret-key-here
```

**注意**: 本番環境では必ず強力なランダム文字列を使用してください。

### ログレベル設定

**LOG_LEVEL** (オプション)

アプリケーションのログレベル。

**デフォルト値**: `INFO`

**設定可能な値**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

```bash
LOG_LEVEL=DEBUG
```

---

## 環境別設定例

### 開発環境 (.env.development)

```bash
# DeepL API (Free版)
DEEPL_API_KEY=your-free-api-key:fx
DEEPL_API_BASE_URL=https://api-free.deepl.com/v2

# データベース (ローカル)
MONGODB_URI=mongodb://localhost:27017/dxeeworld_dev

# セッション
SESSION_SECRET=dev-secret-key-change-in-production

# ログレベル
LOG_LEVEL=DEBUG

# アクセス制御（開発環境では無効化）
# ACCESS_CONTROL_RULES=
```

### ステージング環境 (.env.staging)

```bash
# DeepL API (Free版またはPro版)
DEEPL_API_KEY=your-staging-api-key
DEEPL_API_BASE_URL=https://api-free.deepl.com/v2

# データベース (ステージング)
MONGODB_URI=mongodb://staging-db:27017/dxeeworld_staging

# セッション
SESSION_SECRET=${STAGING_SESSION_SECRET}

# ログレベル
LOG_LEVEL=INFO

# アクセス制御
ACCESS_CONTROL_RULES="/reviews/new,user,admin;/admin,admin"
ACCESS_CONTROL_RELOAD_INTERVAL=60
```

### 本番環境 (.env.production)

```bash
# DeepL API (Pro版推奨)
DEEPL_API_KEY=${DEEPL_API_KEY_PROD}
DEEPL_API_BASE_URL=https://api.deepl.com/v2

# データベース (本番)
MONGODB_URI=${MONGODB_URI_PROD}

# セッション
SESSION_SECRET=${SESSION_SECRET_PROD}

# ログレベル
LOG_LEVEL=WARNING

# アクセス制御
ACCESS_CONTROL_RULES="/reviews/new,user,admin;/admin,admin"
ACCESS_CONTROL_RELOAD_INTERVAL=300
```

**注意**: 本番環境では環境変数を直接 `.env` ファイルに記載せず、シークレット管理システム（AWS Secrets Manager, Azure Key Vault等）を使用してください。

---

## Feature Flag設定

Feature Flagを使用して、特定の機能を有効/無効にできます。

### 利用可能なFeature Flag

**ENABLE_TRANSLATION** (オプション)

翻訳機能の有効/無効を制御します。

**デフォルト値**: `true`

```bash
# 翻訳機能を無効化
ENABLE_TRANSLATION=false
```

**用途**:
- メンテナンス時に翻訳機能を一時的に無効化
- DeepL APIの使用量制限に達した場合の緊急対応
- A/Bテスト

**ENABLE_ACCESS_CONTROL** (オプション)

アクセス制御機能の有効/無効を制御します。

**デフォルト値**: `true`

```bash
# アクセス制御を無効化（開発環境用）
ENABLE_ACCESS_CONTROL=false
```

**TRANSLATION_TIMEOUT** (オプション)

翻訳APIのタイムアウト時間（秒）。

**デフォルト値**: `5`

```bash
# タイムアウトを10秒に延長
TRANSLATION_TIMEOUT=10
```

---

## セキュリティのベストプラクティス

### 1. `.env` ファイルをバージョン管理から除外

`.gitignore` に以下を追加:
```
.env
.env.local
.env.*.local
```

### 2. `.env.example` を作成

必要な環境変数のテンプレートを提供:

```bash
# .env.example
DEEPL_API_KEY=your-api-key-here
DEEPL_API_BASE_URL=https://api-free.deepl.com/v2
MONGODB_URI=mongodb://localhost:27017/dxeeworld
SESSION_SECRET=your-secret-key-here
LOG_LEVEL=INFO
```

### 3. 強力な秘密鍵の生成

```bash
# ランダムな秘密鍵を生成
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. 本番環境での環境変数管理

- AWS Secrets Manager
- Azure Key Vault
- Google Cloud Secret Manager
- HashiCorp Vault

を使用して、環境変数を安全に管理してください。

---

## トラブルシューティング

### エラー: "DEEPL_API_KEY is required"

**原因**: DEEPL_API_KEY が設定されていません。

**解決方法**:
1. `.env` ファイルに `DEEPL_API_KEY` を追加
2. APIキーが正しいことを確認
3. `.env` ファイルが正しい場所（プロジェクトルート）にあることを確認

### エラー: "API rate limit exceeded"

**原因**: DeepL APIの使用量制限に達しました。

**解決方法**:
1. Free版の場合: 月間500,000文字制限を確認
2. Pro版へのアップグレードを検討
3. 一時的に `ENABLE_TRANSLATION=false` で翻訳機能を無効化

### エラー: "Translation timeout"

**原因**: DeepL APIのレスポンスが5秒以内に返りませんでした。

**解決方法**:
1. ネットワーク接続を確認
2. `TRANSLATION_TIMEOUT` を延長（例: `10`）
3. DeepL APIのステータスページを確認: https://status.deepl.com/

### 翻訳が動作しない

**チェックリスト**:
1. `DEEPL_API_KEY` が正しく設定されているか
2. `DEEPL_API_BASE_URL` が Free版/Pro版に対応しているか
3. `ENABLE_TRANSLATION=true` になっているか
4. ログファイルでエラーメッセージを確認

---

## 使用量のモニタリング

### DeepL API使用量の確認

1. [DeepL API アカウント](https://www.deepl.com/pro-account)にログイン
2. 「使用状況」セクションで現在の使用量を確認
3. アラート設定で上限に近づいた際の通知を設定

### アプリケーションログ

翻訳APIの呼び出しはログに記録されます:

```
INFO - Translation API call: ja -> en (125 chars)
INFO - Parallel translation completed: ja -> ['en', 'zh'] (success: 2/2)
WARNING - Translation failed: API timeout
```

ログレベルを `DEBUG` に設定すると、より詳細な情報が記録されます。

---

## 参考リンク

- [DeepL API ドキュメント](https://www.deepl.com/docs-api)
- [DeepL API 価格](https://www.deepl.com/pro-api)
- [DeepL API ステータス](https://status.deepl.com/)

---

## 更新履歴

### v2.0.0 (2024-11-04)
- DeepL API設定の追加
- Feature Flag設定の追加
- セキュリティベストプラクティスの追加

### v1.0.0 (2024-10-01)
- 初版作成
