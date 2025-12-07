# レビューコレクション インデックス仕様

このドキュメントは、`review-detail-pages` 機能で使用されるMongoDBインデックスの仕様と管理方法を説明します。

## 概要

レビュー詳細ページ機能では、以下の2種類のクエリに対してパフォーマンスを最適化する必要があります：

1. **個別レビュー詳細クエリ**: 特定のレビューIDでレビューを取得
2. **質問別レビュー一覧クエリ**: 特定企業の特定評価項目に対するレビューを取得

これらのクエリを効率化するため、複合インデックスを使用しています。

## インデックス一覧

### 1. 基本インデックス

```javascript
{
  "name": "company_id_1_is_active_1_created_at_-1",
  "keys": {
    "company_id": 1,      // 昇順
    "is_active": 1,       // 昇順
    "created_at": -1      // 降順
  }
}
```

**用途**:
- 個別レビュー詳細ページのクエリ最適化
- 質問別レビュー一覧ページの基本クエリ最適化
- レビュー一覧の投稿日時順ソート

**対象クエリ例**:
```javascript
db.reviews.find({
  "company_id": "company123",
  "is_active": true
}).sort({ "created_at": -1 })
```

### 2. 評価項目別インデックス（6つ）

各評価項目（recommendation, foreign_support, company_culture, employee_relations, evaluation_system, promotion_treatment）に対して、以下の構造のインデックスを作成しています。

```javascript
{
  "name": "company_id_1_ratings.recommendation_1_is_active_1_created_at_-1",
  "keys": {
    "company_id": 1,                // 昇順
    "ratings.recommendation": 1,    // 昇順
    "is_active": 1,                 // 昇順
    "created_at": -1                // 降順
  }
}
```

**全インデックス一覧**:
- `company_id_1_ratings.recommendation_1_is_active_1_created_at_-1`
- `company_id_1_ratings.foreign_support_1_is_active_1_created_at_-1`
- `company_id_1_ratings.company_culture_1_is_active_1_created_at_-1`
- `company_id_1_ratings.employee_relations_1_is_active_1_created_at_-1`
- `company_id_1_ratings.evaluation_system_1_is_active_1_created_at_-1`
- `company_id_1_ratings.promotion_treatment_1_is_active_1_created_at_-1`

**用途**:
- 質問別レビュー一覧ページのクエリ最適化
- 特定評価項目に回答したレビューのフィルタリング
- ページネーションによる効率的なデータ取得

**対象クエリ例**:
```javascript
db.reviews.find({
  "company_id": "company123",
  "ratings.foreign_support": { $ne: null },
  "is_active": true
}).sort({ "created_at": -1 }).skip(0).limit(20)
```

## パフォーマンス目標

### クエリ実行時間

| クエリ種類 | 目標時間 | 備考 |
|-----------|---------|------|
| 個別レビュー詳細 | < 5ms | _idインデックス使用 |
| 質問別レビュー一覧（20件） | < 10ms | 複合インデックス使用 |
| 総件数取得 | < 5ms | インデックスカバーされたcount |

### ページレンダリング時間

| ページ種類 | 目標時間 | 備考 |
|-----------|---------|------|
| 個別レビュー詳細ページ | < 200ms | DB取得 + テンプレートレンダリング |
| 質問別レビュー一覧ページ | < 300ms | DB取得（20件） + テンプレートレンダリング |

## インデックス管理

### インデックス作成スクリプト

`scripts/create_review_indexes.py` を使用してインデックスを一括作成できます。

```bash
# インデックスを作成
uv run python scripts/create_review_indexes.py
```

**スクリプトの動作**:
1. 既存のインデックスをチェック
2. 不足しているインデックスのみを作成
3. インデックスの検証を実行
4. 結果をコンソールに表示

### インデックス検証

`tests/test_review_indexes.py` を使用してインデックスの存在と動作を検証できます。

```bash
# インデックステストを実行
uv run pytest tests/test_review_indexes.py -v
```

**テスト内容**:
- 必須インデックスの存在確認
- インデックス構造の検証
- クエリでのインデックス使用確認
- パフォーマンステスト（100件のレビューで50ms以内）

### MongoDBシェルでの確認

```bash
# インデックス一覧を表示
mongosh --eval "db.getSiblingDB('dxeeworld').reviews.getIndexes()" mongodb://localhost:27017
```

## トラブルシューティング

### インデックスが使用されていない

クエリの実行計画を確認してください：

```javascript
db.reviews.find({
  "company_id": "company123",
  "ratings.foreign_support": { $ne: null },
  "is_active": true
}).sort({ "created_at": -1 }).explain("executionStats")
```

`winningPlan` に `IXSCAN` ステージが含まれていれば、インデックスが使用されています。

### パフォーマンスが遅い

以下を確認してください：

1. **インデックスの存在確認**:
   ```bash
   uv run python scripts/create_review_indexes.py
   ```

2. **インデックスの統計情報更新**:
   ```javascript
   db.reviews.reIndex()
   ```

3. **クエリプロファイリング**:
   ```javascript
   db.setProfilingLevel(2)  // 全クエリをログ
   db.system.profile.find().sort({ ts: -1 }).limit(10)
   ```

## 将来の拡張

### キャッシング戦略（Phase 2）

Redisキャッシュを導入する場合、以下のデータをキャッシュすることを検討：

1. **匿名化表示名**: `anon:user:{user_id}` → `"ユーザーA"`
   - TTL: 1日
2. **レビュー詳細**: `review:detail:{review_id}`
   - TTL: 1時間
   - 無効化トリガー: レビュー更新時

### インデックス最適化（Phase 2）

1. **部分インデックス**: `is_active=true` のレビューのみにインデックスを作成
   ```javascript
   db.reviews.createIndex(
     { "company_id": 1, "created_at": -1 },
     { partialFilterExpression: { is_active: true } }
   )
   ```

2. **カバリングインデックス**: 必要なフィールドをすべてインデックスに含める
   ```javascript
   db.reviews.createIndex({
     "company_id": 1,
     "ratings.foreign_support": 1,
     "is_active": 1,
     "created_at": -1,
     "user_id": 1,
     "employment_status": 1
   })
   ```

## 参照

- **設計書**: [.kiro/specs/review-detail-pages/design.md](/.kiro/specs/review-detail-pages/design.md)
- **要件定義書**: [.kiro/specs/review-detail-pages/requirements.md](/.kiro/specs/review-detail-pages/requirements.md)
- **MongoDB インデックス公式ドキュメント**: https://www.mongodb.com/docs/manual/indexes/

## 履歴

- **2025-12-07**: 初版作成 - Task 6.1完了
- インデックステスト実装
- インデックス作成スクリプト実装
