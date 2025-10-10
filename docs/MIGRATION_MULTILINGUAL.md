# 多言語対応データモデル拡張マイグレーションガイド

## 概要

このマイグレーションは、DXEEWorld プラットフォームのレビューシステムに多言語対応機能を追加します。

### 変更内容

#### Review モデル
- **language** フィールドを追加（"en", "ja", "zh" のいずれか、デフォルト: "ja"）
- **comments_ja** フィールドを追加（オプショナル、日本語翻訳）
- **comments_zh** フィールドを追加（オプショナル、中国語翻訳）
- **comments_en** フィールドを追加（オプショナル、英語翻訳）

#### User モデル
- **last_review_posted_at** フィールドを追加（オプショナル、最終レビュー投稿日時）

#### インデックス
- `reviews.language` インデックス（多言語分析用）
- `users.last_review_posted_at` インデックス（アクセス制御用）

## 実行前の準備

### 1. バックアップ

**必須**: マイグレーション実行前に必ずデータベースのバックアップを取得してください。

```bash
# MongoDB のバックアップ
mongodump --uri="mongodb://localhost:27017/dxeeworld" --out=/path/to/backup/$(date +%Y%m%d_%H%M%S)
```

### 2. 環境確認

```bash
# MongoDB が起動していることを確認
docker ps | grep mongo

# MongoDB が起動していない場合
docker start dxeeworld-mongodb
```

### 3. テスト環境での動作確認

本番環境で実行する前に、必ずテスト環境でドライランを実行してください。

## マイグレーション実行手順

### ステップ 1: ドライラン（推奨）

実際にデータを更新せず、マイグレーションの影響を確認します。

```bash
uv run python src/tools/migrate_multilingual.py --dry-run
```

**ドライランで確認する項目:**
- マイグレーション対象のレビュー数
- マイグレーション対象のユーザー数
- エラーの有無

### ステップ 2: 本番マイグレーション実行

ドライランで問題がないことを確認したら、本番マイグレーションを実行します。

```bash
uv run python src/tools/migrate_multilingual.py
```

### ステップ 3: 検証

マイグレーション後、データ整合性が自動的に検証されます。

**検証項目:**
- 全てのレビューに `language` フィールドがある
- 全ての `language` 値が有効（en, ja, zh）
- 全てのユーザーに `last_review_posted_at` フィールドがある

## マイグレーション出力例

### 成功時

```
============================================================
多言語対応データモデル拡張マイグレーション
実行モード: 本番実行
開始時刻: 2025-10-10 13:00:00+00:00
============================================================

============================================================
レビューマイグレーション開始
============================================================
マイグレーション対象: 150 件
既にマイグレーション済み: 0 件
✓ 150 件のレビューを更新しました

============================================================
ユーザーマイグレーション開始
============================================================
マイグレーション対象ユーザー: 45 件
  ユーザー 507f1f77bcf86cd799439011: 最終投稿 2025-09-15 10:23:45+00:00
  ...
✓ 40 件のユーザーを更新しました
  （レビュー投稿履歴なし: 5 件）

============================================================
インデックス作成
============================================================
✓ reviews.language インデックスを作成しました
✓ users.last_review_posted_at インデックスを作成しました

============================================================
データ整合性検証
============================================================
✓ 全てのレビューに language フィールドがあります
✓ 全てのレビューの language 値が有効です (en, ja, zh)
✓ 全てのユーザーに last_review_posted_at フィールドがあります

統計情報:
  総レビュー数: 150
  総ユーザー数: 45

✓ データ整合性検証に成功しました

============================================================
マイグレーション完了
============================================================
終了時刻: 2025-10-10 13:00:05+00:00
実行時間: 5.23 秒

結果サマリー:
  レビュー更新: 150 件
  レビュー既存: 0 件
  ユーザー更新: 40 件
  レビュー履歴なしユーザー: 5 件

エラー: なし
```

## トラブルシューティング

### MongoDB 接続エラー

**エラー**: `データベース接続エラー: ServerSelectionTimeoutError`

**解決方法**:
```bash
# MongoDB が起動しているか確認
docker ps | grep mongo

# 起動していない場合
docker start dxeeworld-mongodb

# 接続情報を確認
cat .env | grep MONGODB_URL
```

### 既にマイグレーション済み

マイグレーションスクリプトは冪等性があるため、複数回実行しても安全です。

```
マイグレーション対象: 0 件
既にマイグレーション済み: 150 件
マイグレーション対象のレビューはありません
```

この場合、既にマイグレーションが完了しているため、何もする必要はありません。

### 検証エラー

**エラー**: `✗ language フィールドがないレビューが 5 件存在します`

**解決方法**:
1. マイグレーションスクリプトを再度実行
2. 問題が解決しない場合、手動で確認:

```bash
# MongoDB コンソールで確認
mongo dxeeworld

# language フィールドがないレビューを検索
db.reviews.find({ language: { $exists: false } }).pretty()

# 手動で修正
db.reviews.updateMany(
  { language: { $exists: false } },
  { $set: { language: "ja" } }
)
```

## ロールバック

マイグレーション後に問題が発生した場合のロールバック手順:

### 1. バックアップから復元

```bash
# バックアップから復元
mongorestore --uri="mongodb://localhost:27017/dxeeworld" /path/to/backup/20251010_130000
```

### 2. 手動でフィールドを削除（非推奨）

```javascript
// MongoDB コンソール
db.reviews.updateMany({}, { $unset: { language: "", comments_ja: "", comments_zh: "", comments_en: "" } })
db.users.updateMany({}, { $unset: { last_review_posted_at: "" } })
```

**注意**: 手動でのロールバックは推奨されません。必ずバックアップから復元してください。

## テスト

### ユニットテスト

```bash
# モデルのテスト
uv run pytest tests/test_review_multilingual.py -v
uv run pytest tests/test_user_review_access.py -v

# データ構造テスト
uv run pytest tests/test_mongodb_data_structure.py -v
```

### MongoDB 統合テスト（MongoDB 起動が必要）

```bash
# マイグレーションテスト（MongoDB 起動時のみ）
uv run pytest tests/test_migration_multilingual.py -v
```

## 関連ファイル

- **マイグレーションスクリプト**: `src/tools/migrate_multilingual.py`
- **Review モデル**: `src/models/review.py`
- **User モデル**: `src/models/user.py`
- **テスト**:
  - `tests/test_review_multilingual.py`
  - `tests/test_user_review_access.py`
  - `tests/test_migration_multilingual.py`
  - `tests/test_mongodb_data_structure.py`

## サポート

マイグレーションに関する問題が発生した場合:

1. まずこのドキュメントのトラブルシューティングセクションを確認
2. ログファイルを確認（マイグレーション実行時の出力）
3. バックアップから復元して再試行
4. 問題が解決しない場合は、開発チームに連絡

## 次のステップ

マイグレーション完了後の開発タスク:

1. **タスク 2**: アクセス制御層の実装（UserService の拡張）
2. **タスク 3**: 多言語フォームの実装（I18nFormService の作成）
3. **タスク 4**: 雇用期間バリデーションの実装
4. **タスク 5**: 翻訳サービスの統合（DeepSeek API）

詳細は `.kiro/specs/review-listing-and-multilingual-improvements/tasks.md` を参照してください。
