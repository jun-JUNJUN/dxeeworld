# マイグレーション実行ガイド

## 概要

このガイドでは、レビュー投稿・多言語対応機能のデータベースマイグレーションの実行手順、ロールバック手順、バリデーションチェックリストを説明します。

---

## 目次

1. [マイグレーション概要](#マイグレーション概要)
2. [事前準備](#事前準備)
3. [実行手順](#実行手順)
4. [ロールバック手順](#ロールバック手順)
5. [バリデーションチェックリスト](#バリデーションチェックリスト)
6. [トラブルシューティング](#トラブルシューティング)

---

## マイグレーション概要

### 変更内容

#### Review コレクション

**新規フィールド**:
- `language` (String, required): レビューの元言語（"ja" | "en" | "zh"）
- `comments_ja` (Object, optional): 日本語翻訳コメント
- `comments_en` (Object, optional): 英語翻訳コメント
- `comments_zh` (Object, optional): 中国語翻訳コメント

**新規インデックス**:
- `{ language: 1 }`: 言語別検索用

#### User コレクション

**新規フィールド**:
- `last_review_posted_at` (Date, optional): 最終レビュー投稿日時

**新規インデックス**:
- `{ last_review_posted_at: -1 }`: アクセス制御用

### 影響範囲

- 既存の全レビューに `language: "ja"` が設定されます
- 既存の全ユーザーに `last_review_posted_at` が設定されます（レビュー投稿履歴がある場合）
- アプリケーションの再起動が必要です

---

## 事前準備

### 1. バックアップの取得（必須）

**重要**: マイグレーション実行前に必ずデータベースのバックアップを取得してください。

```bash
# MongoDB のバックアップ
BACKUP_DIR="/path/to/backup/$(date +%Y%m%d_%H%M%S)"
mongodump --uri="mongodb://localhost:27017/dxeeworld" --out="$BACKUP_DIR"

# バックアップの確認
ls -lh "$BACKUP_DIR"
du -sh "$BACKUP_DIR"
```

**バックアップファイルの保管**:
- バックアップは最低1週間保管してください
- 本番環境では外部ストレージ（S3, GCS等）にコピーしてください

### 2. 環境確認

#### MongoDB の起動確認

```bash
# Docker 環境
docker ps | grep mongo

# MongoDB が起動していない場合
docker start dxeeworld-mongodb

# MongoDB バージョン確認
mongo --version  # または mongosh --version
```

#### 接続確認

```bash
# MongoDB への接続テスト
mongo "mongodb://localhost:27017/dxeeworld" --eval "db.stats()"

# または
mongosh "mongodb://localhost:27017/dxeeworld" --eval "db.stats()"
```

### 3. マイグレーションスクリプトの確認

```bash
# スクリプトが存在することを確認
ls -l src/tools/migrate_multilingual.py

# Python 環境の確認
uv run python --version
```

### 4. テスト環境でのドライラン（推奨）

本番環境で実行する前に、必ずテスト環境でドライランを実行してください。

```bash
# テスト環境で実行
export MONGODB_URI="mongodb://localhost:27017/dxeeworld_test"
uv run python src/tools/migrate_multilingual.py --dry-run
```

---

## 実行手順

### ステップ 1: メンテナンスモードの有効化（本番環境）

本番環境では、マイグレーション中のデータ不整合を防ぐため、メンテナンスモードを有効にしてください。

```bash
# アプリケーションの停止
systemctl stop dxeeworld

# または Docker 環境
docker stop dxeeworld-app
```

### ステップ 2: ドライラン実行

実際にデータを更新せず、マイグレーションの影響を確認します。

```bash
uv run python src/tools/migrate_multilingual.py --dry-run
```

**ドライランで確認する項目**:
- ✅ マイグレーション対象のレビュー数
- ✅ マイグレーション対象のユーザー数
- ✅ エラーの有無
- ✅ 予想実行時間

**ドライラン出力例**:
```
============================================================
多言語対応データモデル拡張マイグレーション
実行モード: ドライラン（実際のデータ更新は行いません）
開始時刻: 2024-11-04 13:00:00+00:00
============================================================

マイグレーション対象: 1,523 件のレビュー
マイグレーション対象: 245 件のユーザー
予想実行時間: 約 15 秒
```

### ステップ 3: 本番マイグレーション実行

ドライランで問題がないことを確認したら、本番マイグレーションを実行します。

```bash
uv run python src/tools/migrate_multilingual.py

# ログを保存する場合
uv run python src/tools/migrate_multilingual.py 2>&1 | tee migration_$(date +%Y%m%d_%H%M%S).log
```

**実行中の注意事項**:
- マイグレーション中はデータベースに接続しないでください
- プロセスを中断しないでください（Ctrl+C 禁止）
- ネットワーク接続が安定していることを確認してください

### ステップ 4: 自動検証

マイグレーション完了後、データ整合性が自動的に検証されます。

**検証項目**:
- ✅ 全てのレビューに `language` フィールドがある
- ✅ 全ての `language` 値が有効（en, ja, zh）
- ✅ 全てのユーザーに `last_review_posted_at` フィールドがある
- ✅ インデックスが正しく作成されている

### ステップ 5: 手動検証（推奨）

自動検証に加えて、手動でデータを確認してください。

```bash
# MongoDB コンソールに接続
mongosh "mongodb://localhost:27017/dxeeworld"

# または
mongo "mongodb://localhost:27017/dxeeworld"
```

**検証クエリ**:

```javascript
// 1. サンプルレビューを確認
db.reviews.findOne();

// 2. language フィールドの分布を確認
db.reviews.aggregate([
  { $group: { _id: "$language", count: { $sum: 1 } } }
]);

// 3. 翻訳フィールドが存在するレビューを確認
db.reviews.find({
  $or: [
    { comments_ja: { $exists: true } },
    { comments_en: { $exists: true } },
    { comments_zh: { $exists: true } }
  ]
}).count();

// 4. last_review_posted_at が設定されているユーザーを確認
db.users.find({ last_review_posted_at: { $exists: true } }).count();

// 5. インデックスを確認
db.reviews.getIndexes();
db.users.getIndexes();
```

### ステップ 6: アプリケーションの再起動

マイグレーションが成功したら、アプリケーションを再起動します。

```bash
# アプリケーションの起動
systemctl start dxeeworld

# または Docker 環境
docker start dxeeworld-app

# 起動確認
systemctl status dxeeworld

# または
docker ps | grep dxeeworld-app
```

### ステップ 7: 動作確認

アプリケーションが正常に動作することを確認します。

**確認項目**:
- ✅ アプリケーションが起動する
- ✅ レビュー一覧が表示される
- ✅ レビュー投稿フォームが表示される
- ✅ 多言語選択ドロップダウンが表示される
- ✅ 既存のレビューが正常に表示される

---

## ロールバック手順

マイグレーション後に問題が発生した場合のロールバック手順です。

### 方法 1: バックアップからの復元（推奨）

```bash
# 1. アプリケーションを停止
systemctl stop dxeeworld  # または docker stop dxeeworld-app

# 2. 現在のデータベースをバックアップ（念のため）
ROLLBACK_BACKUP="/path/to/rollback_backup/$(date +%Y%m%d_%H%M%S)"
mongodump --uri="mongodb://localhost:27017/dxeeworld" --out="$ROLLBACK_BACKUP"

# 3. バックアップから復元
BACKUP_DIR="/path/to/backup/20241104_130000"  # マイグレーション前のバックアップ
mongorestore --uri="mongodb://localhost:27017/dxeeworld" --drop "$BACKUP_DIR"

# 4. 復元確認
mongosh "mongodb://localhost:27017/dxeeworld" --eval "db.reviews.findOne()"

# 5. アプリケーションを起動
systemctl start dxeeworld  # または docker start dxeeworld-app
```

**復元後の確認**:
```javascript
// MongoDB コンソール
// language フィールドが存在しないことを確認
db.reviews.find({ language: { $exists: true } }).count();  // 0 であるべき

// last_review_posted_at フィールドが存在しないことを確認
db.users.find({ last_review_posted_at: { $exists: true } }).count();  // 0 であるべき
```

### 方法 2: 手動でフィールドを削除（非推奨）

**警告**: この方法は推奨されません。データ損失のリスクがあります。

```javascript
// MongoDB コンソール

// 1. Reviews コレクションから新規フィールドを削除
db.reviews.updateMany(
  {},
  {
    $unset: {
      language: "",
      comments_ja: "",
      comments_en: "",
      comments_zh: ""
    }
  }
);

// 2. Users コレクションから新規フィールドを削除
db.users.updateMany(
  {},
  { $unset: { last_review_posted_at: "" } }
);

// 3. インデックスを削除
db.reviews.dropIndex("language_1");
db.users.dropIndex("last_review_posted_at_-1");

// 4. 削除確認
db.reviews.find({ language: { $exists: true } }).count();
db.users.find({ last_review_posted_at: { $exists: true } }).count();
```

### ロールバック後の動作確認

- ✅ アプリケーションが起動する
- ✅ 既存機能が正常に動作する
- ✅ エラーログがないことを確認

---

## バリデーションチェックリスト

### マイグレーション前

- [ ] データベースのバックアップを取得した
- [ ] バックアップファイルが正常に作成されたことを確認した
- [ ] テスト環境でドライランを実行した
- [ ] ドライランで問題がないことを確認した
- [ ] 本番環境の接続情報が正しいことを確認した
- [ ] メンテナンスモードを有効にした（本番環境）
- [ ] アプリケーションを停止した（本番環境）

### マイグレーション実行中

- [ ] マイグレーションスクリプトが正常に開始した
- [ ] エラーメッセージがないことを確認した
- [ ] 進捗状況が表示されている

### マイグレーション完了後

#### 自動検証

- [ ] 全てのレビューに `language` フィールドがある
- [ ] 全ての `language` 値が有効（en, ja, zh）
- [ ] 全てのユーザーに `last_review_posted_at` フィールドがある
- [ ] インデックスが正しく作成されている

#### 手動検証

**Reviews コレクション**:
- [ ] `language` フィールドが全レビューに存在する
- [ ] `language` の値が "ja", "en", "zh" のいずれかである
- [ ] 既存の `comments` フィールドが保持されている
- [ ] レビュー数が変わっていない

**Users コレクション**:
- [ ] `last_review_posted_at` フィールドが適切に設定されている
- [ ] レビュー投稿履歴のないユーザーには設定されていない
- [ ] ユーザー数が変わっていない

**インデックス**:
- [ ] `reviews.language` インデックスが存在する
- [ ] `users.last_review_posted_at` インデックスが存在する

**アプリケーション動作**:
- [ ] アプリケーションが正常に起動する
- [ ] レビュー一覧が表示される
- [ ] レビュー投稿フォームが表示される
- [ ] 多言語選択が機能する
- [ ] エラーログがない

### ロールバック時

- [ ] バックアップから復元した
- [ ] 復元後のデータを確認した
- [ ] 新規フィールドが削除されたことを確認した
- [ ] アプリケーションが正常に動作することを確認した

---

## トラブルシューティング

### 1. MongoDB 接続エラー

**エラー**: `データベース接続エラー: ServerSelectionTimeoutError`

**原因**:
- MongoDB が起動していない
- 接続情報が間違っている
- ネットワークの問題

**解決方法**:
```bash
# MongoDB が起動しているか確認
docker ps | grep mongo

# 起動していない場合
docker start dxeeworld-mongodb

# 接続情報を確認
echo $MONGODB_URI
cat .env | grep MONGODB_URI

# 接続テスト
mongosh "$MONGODB_URI" --eval "db.stats()"
```

### 2. マイグレーションが途中で停止

**症状**: マイグレーションスクリプトが途中で停止する

**原因**:
- メモリ不足
- ネットワークの切断
- ディスク容量不足

**解決方法**:
```bash
# ディスク容量を確認
df -h

# メモリを確認
free -h

# MongoDB のログを確認
docker logs dxeeworld-mongodb | tail -100

# マイグレーションを再実行（冪等性があるため安全）
uv run python src/tools/migrate_multilingual.py
```

### 3. 検証エラー: language フィールドがない

**エラー**: `✗ language フィールドがないレビューが 5 件存在します`

**解決方法**:
```javascript
// MongoDB コンソールで確認
db.reviews.find({ language: { $exists: false } }).pretty();

// 手動で修正
db.reviews.updateMany(
  { language: { $exists: false } },
  { $set: { language: "ja" } }
);

// 再検証
db.reviews.find({ language: { $exists: false } }).count();  // 0 になるべき
```

### 4. インデックス作成エラー

**エラー**: `インデックス作成に失敗しました`

**解決方法**:
```javascript
// 既存のインデックスを確認
db.reviews.getIndexes();

// 重複インデックスを削除
db.reviews.dropIndex("language_1");

// インデックスを再作成
db.reviews.createIndex({ language: 1 });

// 確認
db.reviews.getIndexes();
```

### 5. アプリケーション起動エラー

**エラー**: マイグレーション後にアプリケーションが起動しない

**解決方法**:
```bash
# ログを確認
journalctl -u dxeeworld -n 100
# または
docker logs dxeeworld-app --tail 100

# 環境変数を確認
cat .env

# データベース接続を確認
mongosh "$MONGODB_URI" --eval "db.stats()"

# 必要に応じてロールバック
# （ロールバック手順を参照）
```

---

## パフォーマンス

### 推定実行時間

| レビュー数 | ユーザー数 | 推定時間 |
|----------|----------|---------|
| 100 | 20 | ~2秒 |
| 1,000 | 200 | ~5秒 |
| 10,000 | 2,000 | ~30秒 |
| 100,000 | 20,000 | ~5分 |

**注意**: 実際の実行時間は、データベースのパフォーマンス、ネットワーク速度、データ構造により変動します。

### パフォーマンスチューニング

大規模データベースの場合:

```bash
# バッチサイズを調整（スクリプト内で設定）
# デフォルト: 1000件ずつ処理

# MongoDB の接続数を確認
mongosh --eval "db.serverStatus().connections"

# 必要に応じて MongoDB のメモリを増やす
# docker-compose.yml で設定
```

---

## サポート

マイグレーションに関する問題が発生した場合:

1. **このドキュメントのトラブルシューティングセクションを確認**
2. **ログファイルを確認**（マイグレーション実行時の出力）
3. **データベースの状態を確認**（検証クエリを実行）
4. **バックアップから復元して再試行**
5. **問題が解決しない場合は、開発チームに連絡**

連絡時には以下の情報を提供してください:
- マイグレーションログ
- エラーメッセージ
- データベースの状態（レビュー数、ユーザー数）
- 環境情報（MongoDB バージョン、OS、メモリ）

---

## 関連ドキュメント

- [API ドキュメント](./API_DOCUMENTATION.md)
- [環境変数設定ガイド](./ENVIRONMENT_SETUP.md)
- [MongoDB データ構造](./MONGODB_STRUCTURE.md)
- [多言語対応マイグレーションガイド](./MIGRATION_MULTILINGUAL.md)

---

## 更新履歴

### v2.0.0 (2024-11-04)
- 詳細なロールバック手順の追加
- バリデーションチェックリストの追加
- トラブルシューティングセクションの拡充
- パフォーマンス情報の追加
