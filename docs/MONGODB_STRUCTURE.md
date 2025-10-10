# MongoDB データ構造ドキュメント

## データベース概要

- **データベース名**: `dxeeworld`
- **接続URI**: `mongodb://localhost:27017/`
- **MongoDB バージョン**: 7.0+

## コレクション一覧

1. **reviews** - 企業レビュー
2. **users** - ユーザー情報
3. **companies** - 企業情報
4. **jobs** - 求人情報
5. **sessions** - セッション管理
6. **email_verifications** - メール認証トークン
7. **review_history** - レビュー編集履歴

---

## 1. Reviews コレクション

企業に対する従業員のレビュー情報を管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "company_id": String,                    // 企業ID
  "user_id": String,                       // ユーザーID
  "employment_status": String,             // "current" | "former"
  "employment_period": {                   // 勤務期間
    "start_year": Number,                  // 開始年 (例: 2020)
    "end_year": Number | null              // 終了年 (null = 現在勤務中)
  },
  "ratings": {                             // 7段階評価 (1-5)
    "recommendation": Number | null,       // 推薦度
    "foreign_support": Number | null,      // 外国人サポート
    "company_culture": Number | null,      // 企業文化
    "employee_relations": Number | null,   // 従業員関係
    "evaluation_system": Number | null,    // 評価システム
    "promotion_treatment": Number | null   // 昇進・待遇
  },
  "comments": {                            // 元言語のコメント
    "recommendation": String | null,
    "foreign_support": String | null,
    "company_culture": String | null,
    "employee_relations": String | null,
    "evaluation_system": String | null,
    "promotion_treatment": String | null
  },
  "individual_average": Number,            // 個別平均評価 (0.0-5.0)
  "answered_count": Number,                // 回答した項目数
  "created_at": ISODate,                   // 作成日時
  "updated_at": ISODate,                   // 更新日時
  "is_active": Boolean,                    // 有効フラグ

  // 多言語対応フィールド（新規追加）
  "language": String,                      // "en" | "ja" | "zh" (デフォルト: "ja")
  "comments_ja": {                         // 日本語翻訳 (オプショナル)
    "recommendation": String | null,
    "foreign_support": String | null,
    // ... 他のカテゴリー
  },
  "comments_zh": {                         // 中国語翻訳 (オプショナル)
    "recommendation": String | null,
    // ... 他のカテゴリー
  },
  "comments_en": {                         // 英語翻訳 (オプショナル)
    "recommendation": String | null,
    // ... 他のカテゴリー
  }
}
```

### インデックス

```javascript
// 既存インデックス
{ "company_id": 1, "created_at": -1 }      // 企業別レビュー取得用
{ "user_id": 1 }                           // ユーザー別レビュー取得用

// 新規インデックス（多言語対応）
{ "language": 1 }                          // 言語別レビュー分析用
```

### サンプルドキュメント

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "company_id": "company_123",
  "user_id": "user_456",
  "employment_status": "former",
  "employment_period": {
    "start_year": 2020,
    "end_year": 2023
  },
  "ratings": {
    "recommendation": 4,
    "foreign_support": 5,
    "company_culture": 3,
    "employee_relations": 4,
    "evaluation_system": 3,
    "promotion_treatment": 4
  },
  "comments": {
    "recommendation": "素晴らしい職場環境でした",
    "foreign_support": "外国人社員へのサポートが充実",
    "company_culture": "フラットな組織文化",
    "employee_relations": "チームワークが良い",
    "evaluation_system": "評価基準が明確",
    "promotion_treatment": "実力主義の昇進制度"
  },
  "individual_average": 3.8,
  "answered_count": 6,
  "created_at": ISODate("2024-01-15T10:30:00Z"),
  "updated_at": ISODate("2024-01-15T10:30:00Z"),
  "is_active": true,
  "language": "ja",
  "comments_en": {
    "recommendation": "Great work environment",
    "foreign_support": "Excellent support for foreign employees",
    "company_culture": "Flat organizational culture",
    "employee_relations": "Good teamwork",
    "evaluation_system": "Clear evaluation criteria",
    "promotion_treatment": "Merit-based promotion system"
  },
  "comments_zh": {
    "recommendation": "很棒的工作环境",
    "foreign_support": "对外籍员工的支持很充分",
    // ... 他のカテゴリー
  }
}
```

### 多言語フィールドの仕様

- **language**: レビューの元言語（必須）
  - `"ja"`: 日本語
  - `"en"`: 英語
  - `"zh"`: 中国語（簡体字）

- **翻訳フィールド** (オプショナル):
  - 元言語が日本語の場合: `comments_en`, `comments_zh` が存在
  - 元言語が英語の場合: `comments_ja`, `comments_zh` が存在
  - 元言語が中国語の場合: `comments_ja`, `comments_en` が存在
  - 翻訳失敗時はフィールド自体が存在しない

---

## 2. Users コレクション

プラットフォームのユーザー情報を管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "email": String,                         // メールアドレス (ユニーク)
  "name": String,                          // ユーザー名
  "user_type": String,                     // "JOB_SEEKER" | "RECRUITER"
  "password_hash": String,                 // ハッシュ化パスワード
  "company_id": String | null,             // 所属企業ID (リクルーター用)
  "position": String | null,               // 役職
  "profile": {                             // プロフィール情報
    "bio": String | null,
    "skills": Array<String>,               // スキルリスト
    "experience_years": Number | null,
    "education": String | null,
    "location": String | null,
    "linkedin_url": String | null,
    "github_url": String | null,
    "portfolio_url": String | null
  },
  "created_at": ISODate,                   // 作成日時
  "updated_at": ISODate,                   // 更新日時
  "is_active": Boolean,                    // 有効フラグ

  // レビューアクセス権限フィールド（新規追加）
  "last_review_posted_at": ISODate | null  // 最終レビュー投稿日時
}
```

### インデックス

```javascript
// 既存インデックス
{ "email": 1 }                             // ユニーク、ログイン用
{ "user_type": 1 }                         // ユーザータイプ別取得用

// 新規インデックス（レビューアクセス制御）
{ "last_review_posted_at": -1 }            // アクセス権限チェック用
```

### サンプルドキュメント

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "email": "user@example.com",
  "name": "山田太郎",
  "user_type": "JOB_SEEKER",
  "password_hash": "$2b$12$...",
  "company_id": null,
  "position": null,
  "profile": {
    "bio": "ソフトウェアエンジニア、5年の経験",
    "skills": ["Python", "JavaScript", "React"],
    "experience_years": 5,
    "education": "東京大学 情報工学科",
    "location": "東京都",
    "linkedin_url": "https://linkedin.com/in/yamada",
    "github_url": "https://github.com/yamada",
    "portfolio_url": "https://yamada.dev"
  },
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-10-10T12:00:00Z"),
  "is_active": true,
  "last_review_posted_at": ISODate("2024-09-15T10:30:00Z")
}
```

### レビューアクセス権限の仕様

- **last_review_posted_at**: 最終レビュー投稿日時
  - 値が存在し、かつ **1年以内** の場合: レビュー一覧への **フルアクセス可能**
  - 値が存在するが、**1年以上前** の場合: アクセス **拒否**
  - 値が `null` または存在しない場合: アクセス **拒否**
  - レビュー投稿時に現在時刻で **自動更新**

---

## 3. Companies コレクション

企業情報を管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "name": String,                          // 企業名
  "name_en": String | null,                // 英語名
  "description": String | null,            // 企業説明
  "industry": String | null,               // 業界
  "size": String | null,                   // 企業規模 ("1-50" | "51-200" | "201-500" | "501+")
  "founded_year": Number | null,           // 設立年
  "location": {                            // 所在地
    "country": String,
    "city": String | null,
    "address": String | null
  },
  "website": String | null,                // ウェブサイトURL
  "logo_url": String | null,               // ロゴURL
  "review_summary": {                      // レビューサマリー
    "total_reviews": Number,               // 総レビュー数
    "overall_average": Number,             // 総合平均評価
    "category_averages": {                 // カテゴリー別平均
      "recommendation": Number,
      "foreign_support": Number,
      "company_culture": Number,
      "employee_relations": Number,
      "evaluation_system": Number,
      "promotion_treatment": Number
    },
    "last_updated": ISODate               // 最終更新日時
  },
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_active": Boolean
}
```

### インデックス

```javascript
{ "name": 1 }                              // 企業名検索用
{ "industry": 1 }                          // 業界別取得用
{ "location.country": 1, "location.city": 1 } // 地域別取得用
```

---

## 4. Jobs コレクション

求人情報を管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "company_id": String,                    // 企業ID
  "title": String,                         // 求人タイトル
  "description": String,                   // 求人詳細
  "requirements": Array<String>,           // 必須スキル
  "preferred_skills": Array<String>,       // 歓迎スキル
  "job_type": String,                      // "full-time" | "part-time" | "contract"
  "location": {
    "country": String,
    "city": String | null,
    "remote_ok": Boolean                   // リモート可否
  },
  "salary": {
    "min": Number | null,                  // 最低給与
    "max": Number | null,                  // 最高給与
    "currency": String                     // 通貨コード (例: "JPY", "USD")
  },
  "posted_at": ISODate,                    // 投稿日時
  "expires_at": ISODate | null,            // 有効期限
  "is_active": Boolean,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### インデックス

```javascript
{ "company_id": 1 }                        // 企業別求人取得用
{ "posted_at": -1 }                        // 最新順取得用
{ "job_type": 1 }                          // 雇用形態別取得用
```

---

## 5. Sessions コレクション

ユーザーセッションを管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "session_id": String,                    // セッションID (ユニーク)
  "user_id": String,                       // ユーザーID
  "created_at": ISODate,                   // 作成日時
  "expires_at": ISODate,                   // 有効期限
  "data": Object                           // セッションデータ
}
```

### インデックス

```javascript
{ "session_id": 1 }                        // ユニーク、セッション検索用
{ "expires_at": 1 }                        // TTLインデックス（自動削除）
{ "user_id": 1 }                           // ユーザー別セッション取得用
```

---

## 6. Email Verifications コレクション

メールアドレス認証トークンを管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "email": String,                         // 認証対象メールアドレス
  "verification_code": String,             // 認証コード (暗号化)
  "expires_at": ISODate,                   // 有効期限
  "verified": Boolean,                     // 認証済みフラグ
  "created_at": ISODate
}
```

### インデックス

```javascript
{ "email": 1 }                             // メールアドレス検索用
{ "expires_at": 1 }                        // TTLインデックス
```

---

## 7. Review History コレクション

レビュー編集履歴を管理。

### スキーマ構造

```javascript
{
  "_id": ObjectId("..."),
  "review_id": String,                     // レビューID
  "user_id": String,                       // 編集者ID
  "previous_data": Object,                 // 編集前データ
  "edited_at": ISODate,                    // 編集日時
  "changes": {                             // 変更内容
    "field": String,
    "old_value": Any,
    "new_value": Any
  }
}
```

### インデックス

```javascript
{ "review_id": 1, "edited_at": -1 }       // レビュー別履歴取得用
```

---

## データ整合性ルール

### Reviews

1. `company_id` は `companies._id` を参照
2. `user_id` は `users._id` を参照
3. `employment_status` が `"former"` の場合、`employment_period.end_year` が必須
4. `language` は `"en"`, `"ja"`, `"zh"` のいずれか
5. 元言語のコメントは `comments` フィールドに格納
6. 翻訳は元言語以外の2言語分が `comments_XX` フィールドに格納（オプショナル）

### Users

1. `email` はユニーク
2. `last_review_posted_at` はレビュー投稿時に自動更新
3. レビューアクセス権限は `last_review_posted_at` が1年以内の場合のみ有効

### Companies

1. `review_summary` はレビュー投稿・編集時に自動更新
2. `total_reviews` は `reviews` コレクションのドキュメント数と一致

---

## マイグレーション履歴

### 2025-10-10: 多言語対応データモデル拡張

- **Reviews**: `language`, `comments_ja`, `comments_zh`, `comments_en` フィールド追加
- **Users**: `last_review_posted_at` フィールド追加
- **インデックス追加**:
  - `reviews.language`
  - `users.last_review_posted_at`

詳細は `docs/MIGRATION_MULTILINGUAL.md` を参照。

---

## データベース操作例

### レビュー検索

```javascript
// 日本語のレビューを取得
db.reviews.find({ language: "ja" })

// 特定企業の最新レビュー
db.reviews.find({ company_id: "company_123" })
  .sort({ created_at: -1 })
  .limit(10)
```

### ユーザー検索

```javascript
// レビューアクセス権限があるユーザー
const oneYearAgo = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
db.users.find({
  last_review_posted_at: { $gte: oneYearAgo }
})

// レビュー投稿履歴がないユーザー
db.users.find({
  $or: [
    { last_review_posted_at: { $exists: false } },
    { last_review_posted_at: null }
  ]
})
```

---

## 参考資料

- **マイグレーションガイド**: `docs/MIGRATION_MULTILINGUAL.md`
- **データ構造表示ツール**: `src/tools/show_mongodb_structure.py`
- **モデル定義**:
  - Review: `src/models/review.py`
  - User: `src/models/user.py`
  - Company: `src/models/company.py`
