# API ドキュメント

## レビュー投稿と一覧API

このドキュメントは、レビュー投稿・一覧・多言語対応機能のAPIエンドポイントを定義します。

---

## 目次

1. [レビュー投稿API](#レビュー投稿api)
   - [POST /companies/{company_id}/reviews/new - レビュー投稿フォーム](#post-companiescompany_idreviewsnew---レビュー投稿フォーム)
   - [POST /companies/{company_id}/reviews/new - 確認画面表示](#post-companiescompany_idreviewsnew---確認画面表示)
   - [POST /companies/{company_id}/reviews/new - レビュー投稿](#post-companiescompany_idreviewsnew---レビュー投稿-1)
2. [レビュー一覧API](#レビュー一覧api)
   - [GET /reviews - レビュー一覧](#get-reviews---レビュー一覧)

---

## レビュー投稿API

### POST /companies/{company_id}/reviews/new - レビュー投稿フォーム

レビュー投稿フォームを表示します。

**エンドポイント**: `POST /companies/{company_id}/reviews/new`

**パラメータ**:
- `company_id` (path, required): 会社ID

**レスポンス**:
- `200 OK`: レビュー投稿フォームHTML

**機能**:
- 多言語フォーム（日本語・英語・中国語）
- 言語選択ドロップダウン
- ブラウザ言語の自動検出
- 雇用期間バリデーション
- 雇用状態による自動入力（現従業員選択時）

**Requirements**: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 6.5

---

### POST /companies/{company_id}/reviews/new - 確認画面表示

レビュー投稿の確認画面を表示します。

**エンドポイント**: `POST /companies/{company_id}/reviews/new?mode=confirm`

**パラメータ**:
- `company_id` (path, required): 会社ID
- `mode=confirm` (query, required): 確認モード指定

**リクエストボディ** (application/x-www-form-urlencoded):

```
language: ja | en | zh
employment_status: current | former
employment_period_start_year: YYYY
employment_period_end_year: YYYY | present
ratings[recommendation]: 1-5
ratings[salary]: 1-5
ratings[benefits]: 1-5
ratings[career_growth]: 1-5
ratings[work_life_balance]: 1-5
ratings[management]: 1-5
ratings[culture]: 1-5
comments[salary]: テキスト
comments[benefits]: テキスト
comments[career_growth]: テキスト
comments[work_life_balance]: テキスト
comments[management]: テキスト
comments[culture]: テキスト
```

**レスポンス**:
- `200 OK`: 確認画面HTML
- `400 Bad Request`: バリデーションエラー

**機能**:
- 入力内容のバリデーション
- DeepL APIを使用した並列翻訳（元言語から他2言語へ）
- 3言語のレビューコメントプレビュー
- 翻訳失敗時のGraceful Degradation（翻訳なしで確認画面表示）

**翻訳処理**:
- 元言語: ユーザーが選択した言語（ja/en/zh）
- ターゲット言語: 元言語以外の2言語
- 並列実行: asyncio.gather による同時翻訳
- タイムアウト: 5秒
- エラーハンドリング: 翻訳失敗時はNoneを設定

**Requirements**: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.5

---

### POST /companies/{company_id}/reviews/new - レビュー投稿

レビューをデータベースに保存します。

**エンドポイント**: `POST /companies/{company_id}/reviews/new?mode=submit`

**パラメータ**:
- `company_id` (path, required): 会社ID
- `mode=submit` (query, required): 投稿モード指定

**リクエストボディ** (application/x-www-form-urlencoded):

確認画面と同じフィールド + 翻訳済みコメント:

```
（確認画面のフィールドに加えて）
translated_comments[en][category]: 英語翻訳テキスト
translated_comments[ja][category]: 日本語翻訳テキスト
translated_comments[zh][category]: 中国語翻訳テキスト
```

**レスポンス**:
- `303 See Other`: 成功時、会社詳細ページへリダイレクト
- `400 Bad Request`: バリデーションエラー

**保存データ構造** (MongoDB):

```javascript
{
  _id: ObjectId,
  company_id: String,
  user_id: String,
  language: "ja" | "en" | "zh",  // 元言語
  employment_status: "current" | "former",
  employment_period: {
    start_year: Number,
    end_year: Number | null
  },
  ratings: {
    recommendation: Number (1-5),
    salary: Number (1-5),
    benefits: Number (1-5),
    career_growth: Number (1-5),
    work_life_balance: Number (1-5),
    management: Number (1-5),
    culture: Number (1-5)
  },
  comments: {
    salary: String,
    benefits: String,
    career_growth: String,
    work_life_balance: String,
    management: String,
    culture: String
  },
  comments_ja: {  // 日本語翻訳（元言語が日本語の場合は不要）
    salary: String | null,
    benefits: String | null,
    // ...
  },
  comments_en: {  // 英語翻訳（元言語が英語の場合は不要）
    salary: String | null,
    benefits: String | null,
    // ...
  },
  comments_zh: {  // 中国語翻訳（元言語が中国語の場合は不要）
    salary: String | null,
    benefits: String | null,
    // ...
  },
  created_at: ISODate,
  updated_at: ISODate,
  is_active: Boolean
}
```

**副作用**:
- User.last_review_posted_at を現在時刻に更新
- 会社の平均評価を再計算

**Requirements**: 4.1, 4.2, 4.3, 4.4, 4.5, 1.8, 5.1, 5.2, 5.3, 5.4

---

## レビュー一覧API

### GET /reviews - レビュー一覧

レビュー一覧を取得します。アクセス制御とフィルター機能をサポートします。

**エンドポイント**: `GET /reviews`

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 | アクセスレベル |
|----------|-----|-----|------|--------------|
| `company_id` | String | No | 会社IDでフィルター | full |
| `region` | String | No | 地域でフィルター | full |
| `min_rating` | Number (1-5) | No | 最低評価でフィルター | full |
| `page` | Number | No | ページ番号（デフォルト: 1） | all |
| `per_page` | Number | No | 1ページあたりの件数（デフォルト: 20） | all |

**レスポンス**:
- `200 OK`: レビュー一覧HTML

**アクセス制御**:

システムは以下の4つのアクセスレベルを判定します：

| アクセスレベル | 条件 | 表示内容 | フィルター |
|-------------|------|---------|----------|
| `full` | 1年以内にレビュー投稿済み | 全文表示 | 利用可能 |
| `preview` | 未認証ユーザー | プレビュー表示（128文字+伏せ字） | 利用不可 |
| `crawler` | Webクローラー（User-Agent検出） | 最小限テキスト | 利用不可 |
| `denied` | 認証済み・レビュー未投稿 or 1年以上経過 | アクセス拒否メッセージ | 利用不可 |

**プレビュー表示ルール**:
- 最初の1行 または 最初の128文字を表示
- 残りの部分を「●●●●●」で伏せ字
- has_more フラグで続きがあることを示す

**Webクローラー検出パターン**:
- googlebot, bingbot, slurp (Yahoo), duckduckbot
- baiduspider, yandexbot, facebookexternalhit, twitterbot
- 一般的な "bot", "crawler", "spider" パターン
- 大文字小文字を区別しない

**レスポンス例** (JSON形式の場合):

```json
{
  "access_level": "full",
  "can_filter": true,
  "reviews": [
    {
      "id": "review_123",
      "company_name": "サンプル株式会社",
      "language": "ja",
      "ratings": {
        "recommendation": 4,
        "salary": 5,
        // ...
      },
      "comments": {
        "salary": "給与水準は業界平均より高く、満足しています。",
        // ...
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

**Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8

---

## エラーレスポンス

### バリデーションエラー (400 Bad Request)

```json
{
  "status": "error",
  "errors": [
    "雇用開始年を入力してください",
    "開始年は終了年より前である必要があります"
  ]
}
```

### 認証エラー (401 Unauthorized)

```json
{
  "status": "error",
  "message": "Authentication required"
}
```

### アクセス拒否 (403 Forbidden)

```json
{
  "status": "error",
  "message": "Reviewを投稿いただいた方に閲覧権限を付与しています"
}
```

---

## セキュリティ

### SQL Injection 対策
- パラメータ化クエリを使用
- ユーザー入力を直接SQL文に埋め込まない

### XSS 対策
- 全てのユーザー入力をエスケープ
- HTMLエンティティエンコーディング

### CSRF 対策
- CSRFトークンの検証
- SameSite Cookie属性の使用

### センシティブ情報の保護
- APIキー（DEEPL_API_KEY）をログに出力しない
- セッションIDをマスキング
- ユーザーIDをマスキング

---

## パフォーマンス

### 翻訳API
- 並列実行: asyncio.gather による2言語の同時翻訳
- タイムアウト: 5秒
- 最大リトライ: 2回（タイムアウトエラーのみ）
- 文字数制限: 5000文字/リクエスト

### キャッシング
- レビュー一覧: 1分間キャッシュ（検討中）
- 会社情報: 5分間キャッシュ（検討中）

### ページネーション
- デフォルト: 20件/ページ
- 最大: 100件/ページ

---

## 変更履歴

### v2.0.0 (2024-11-04)
- 多言語レビュー投稿機能の追加
- 確認画面モードの追加
- DeepL API統合（並列翻訳）
- アクセス制御機能の追加
- フィルター機能の追加

### v1.0.0 (2024-10-01)
- 初回リリース
- 基本的なレビュー投稿・一覧機能
