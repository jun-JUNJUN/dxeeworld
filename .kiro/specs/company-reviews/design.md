# 技術設計書 - 企業レビューシステム

## 1. システム概要

### 1.1 機能概要
企業レビューシステムは、外国人労働者が勤務経験のある企業に対して6つのカテゴリーで評価とコメントを投稿できるレビュープラットフォームです。企業ごとに集約された評価データを検索・閲覧でき、外国人労働者の就職活動の意思決定を支援します。

### 1.2 技術スタック
- **バックエンド**: Python 3.x + Tornado Web Framework
- **データベース**: MongoDB（Motor AsyncIO Driver使用）
- **フロントエンド**: HTML5, CSS3, JavaScript (ES6+)
- **認証**: セッションベース認証
- **デプロイ**: 既存インフラストラクチャに統合

## 2. アーキテクチャ設計

### 2.1 システム構成図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ユーザー       │    │   Webアプリ     │    │   MongoDB      │
│   (ブラウザ)     │◄──►│   (Tornado)     │◄──►│               │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Background     │
                       │  Jobs (平均計算) │
                       └─────────────────┘
```

### 2.2 レイヤー構成

```
┌─────────────────────────────────────────┐
│         プレゼンテーション層              │
│  (HTMLテンプレート, JavaScript, CSS)     │
├─────────────────────────────────────────┤
│            アプリケーション層            │
│     (Tornado Handlers, Business Logic)  │
├─────────────────────────────────────────┤
│             サービス層                  │
│  (ReviewService, CompanyService, etc.)   │
├─────────────────────────────────────────┤
│            データアクセス層              │
│      (MongoDB Collections, Models)      │
└─────────────────────────────────────────┘
```

## 3. データベース設計

### 3.1 コレクション設計

#### 3.1.1 companies コレクション（拡張）
既存のcompaniesコレクションにレビュー関連フィールドを追加：

```javascript
{
  "_id": ObjectId,
  "name": "株式会社サンプル",
  "industry": "technology",
  "size": "medium",
  "country": "Japan",
  "location": "東京都",
  "description": "...",
  // 既存フィールド...

  // 新規追加フィールド
  "review_summary": {
    "total_reviews": 15,
    "overall_average": 3.2,
    "category_averages": {
      "recommendation": 3.5,
      "foreign_support": 2.8,
      "company_culture": 3.1,
      "employee_relations": 3.4,
      "evaluation_system": 3.0,
      "promotion_treatment": 2.9
    },
    "last_updated": ISODate
  }
}
```

#### 3.1.2 reviews コレクション（新規作成）

```javascript
{
  "_id": ObjectId,
  "company_id": ObjectId,    // companies._id への参照
  "user_id": ObjectId,       // users._id への参照
  "employment_status": "current|former",  // 現従業員|元従業員

  // 評価データ
  "ratings": {
    "recommendation": 4,           // 1-5 or null（回答しない）
    "foreign_support": 3,          // 外国人受け入れ制度
    "company_culture": null,       // 会社風土（回答しない例）
    "employee_relations": 4,       // 社員との関係性
    "evaluation_system": 3,        // 成果・評価制度
    "promotion_treatment": 2       // 昇進・昇給・待遇
  },

  // コメントデータ
  "comments": {
    "recommendation": "外国人にとって働きやすい環境です。",
    "foreign_support": "",         // ノーコメント
    "company_culture": null,       // 未回答項目
    "employee_relations": "同僚との関係は良好です。",
    "evaluation_system": null,
    "promotion_treatment": "昇進機会は限定的でした。"
  },

  // 計算済み平均点
  "individual_average": 3.0,     // この1件のレビューの平均点
  "answered_count": 4,           // 回答した項目数

  // メタデータ
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_active": true
}
```

#### 3.1.3 review_history コレクション（新規作成）
レビューの更新履歴を追跡：

```javascript
{
  "_id": ObjectId,
  "review_id": ObjectId,         // reviews._id への参照
  "user_id": ObjectId,
  "company_id": ObjectId,
  "action": "create|update",
  "previous_data": {...},        // 更新前のデータ
  "timestamp": ISODate
}
```

### 3.2 インデックス設計

```javascript
// reviews コレクション
db.reviews.createIndex({"company_id": 1, "user_id": 1})
db.reviews.createIndex({"company_id": 1, "created_at": -1})
db.reviews.createIndex({"user_id": 1, "created_at": -1})
db.reviews.createIndex({"individual_average": -1})

// companies コレクション（追加）
db.companies.createIndex({"review_summary.overall_average": -1})
db.companies.createIndex({"name": "text", "location": "text"})

// review_history コレクション
db.review_history.createIndex({"review_id": 1, "timestamp": -1})
```

## 4. APIエンドポイント設計

### 4.1 レビュー関連API

#### 4.1.1 レビュー一覧取得
```
GET /api/reviews
Query Parameters:
  - company_id: 企業ID（任意）
  - page: ページ番号（デフォルト: 1）
  - limit: 1ページあたりの件数（デフォルト: 20）
  - sort: ソート順（newest|oldest|rating_high|rating_low）

Response:
{
  "reviews": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### 4.1.2 レビュー投稿
```
POST /api/reviews
Content-Type: application/json

Request Body:
{
  "company_id": "64a1b2c3d4e5f6789abc123",
  "employment_status": "former",
  "ratings": {
    "recommendation": 4,
    "foreign_support": 3,
    "company_culture": null,
    "employee_relations": 4,
    "evaluation_system": 3,
    "promotion_treatment": 2
  },
  "comments": {
    "recommendation": "良い会社です",
    "foreign_support": "",
    "company_culture": null,
    "employee_relations": "良好な関係",
    "evaluation_system": null,
    "promotion_treatment": "昇進は難しい"
  }
}

Response:
{
  "status": "success",
  "review_id": "64a1b2c3d4e5f6789abc456",
  "individual_average": 3.0
}
```

#### 4.1.3 レビュー更新
```
PUT /api/reviews/{review_id}
Content-Type: application/json

Request Body: (投稿と同じ形式)

Response:
{
  "status": "success",
  "individual_average": 3.2
}
```

### 4.2 検索API

#### 4.2.1 企業検索（レビュー付き）
```
GET /api/companies/search
Query Parameters:
  - name: 企業名（部分一致）
  - location: 所在地
  - min_rating: 最低評価点
  - max_rating: 最高評価点
  - page: ページ番号
  - limit: 1ページあたりの件数
  - sort: ソート順（rating_high|rating_low|review_count|name）

Response:
{
  "companies": [
    {
      "id": "...",
      "name": "株式会社サンプル",
      "location": "東京都",
      "overall_average": 3.2,
      "total_reviews": 15,
      "category_averages": {...}
    }
  ],
  "pagination": {...}
}
```

## 5. データモデル設計

### 5.1 新規モデルクラス

#### 5.1.1 Review モデル
```python
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

class EmploymentStatus(Enum):
    CURRENT = "current"
    FORMER = "former"

class ReviewCategory(Enum):
    RECOMMENDATION = "recommendation"
    FOREIGN_SUPPORT = "foreign_support"
    COMPANY_CULTURE = "company_culture"
    EMPLOYEE_RELATIONS = "employee_relations"
    EVALUATION_SYSTEM = "evaluation_system"
    PROMOTION_TREATMENT = "promotion_treatment"

@dataclass
class Review:
    id: str
    company_id: str
    user_id: str
    employment_status: EmploymentStatus
    ratings: Dict[str, Optional[int]]  # 1-5 or None
    comments: Dict[str, Optional[str]]
    individual_average: float
    answered_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
```

#### 5.1.2 ReviewSummary モデル
```python
@dataclass
class ReviewSummary:
    total_reviews: int
    overall_average: float
    category_averages: Dict[str, float]
    last_updated: datetime
```

#### 5.1.3 Company モデル拡張
```python
# 既存のCompanyモデルに追加
@dataclass
class Company:
    # 既存フィールド...
    review_summary: Optional[ReviewSummary] = None
```

## 6. サービス層設計

### 6.1 ReviewService クラス

```python
class ReviewService:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    async def create_review(self, review_data: dict) -> str:
        """レビューを作成し、企業の平均点を更新"""

    async def update_review(self, review_id: str, review_data: dict) -> bool:
        """レビューを更新し、企業の平均点を再計算"""

    async def get_reviews_by_company(self, company_id: str,
                                   page: int = 1, limit: int = 20) -> dict:
        """企業のレビュー一覧を取得"""

    async def check_review_permission(self, user_id: str,
                                    company_id: str) -> dict:
        """レビュー投稿・更新権限をチェック"""

    async def calculate_individual_average(self, ratings: dict) -> tuple:
        """個別レビューの平均点を計算"""

    async def update_company_averages(self, company_id: str):
        """企業の平均点を再計算・更新"""
```

### 6.2 計算ロジック

#### 6.2.1 個別レビュー平均点計算
```python
def calculate_individual_average(ratings: Dict[str, Optional[int]]) -> tuple[float, int]:
    """
    個別レビューの平均点を計算

    Args:
        ratings: 各項目の評価（1-5 or None）

    Returns:
        tuple: (平均点, 回答項目数)
    """
    valid_ratings = [score for score in ratings.values() if score is not None]

    if not valid_ratings:
        return 0.0, 0

    average = sum(valid_ratings) / len(valid_ratings)
    return round(average, 1), len(valid_ratings)
```

#### 6.2.2 企業別平均点計算
```python
async def calculate_company_averages(self, company_id: str) -> ReviewSummary:
    """
    企業の全項目平均と項目別平均を計算
    """
    # 全項目平均の計算
    reviews = await self.db.reviews.find(
        {"company_id": company_id, "is_active": True}
    ).to_list(None)

    if not reviews:
        return ReviewSummary(0, 0.0, {}, datetime.utcnow())

    # 全項目平均
    individual_averages = [r["individual_average"] for r in reviews]
    overall_average = round(sum(individual_averages) / len(individual_averages), 1)

    # 項目別平均
    category_averages = {}
    for category in ReviewCategory:
        category_ratings = []
        for review in reviews:
            rating = review["ratings"].get(category.value)
            if rating is not None:
                category_ratings.append(rating)

        if category_ratings:
            category_averages[category.value] = round(
                sum(category_ratings) / len(category_ratings), 1
            )
        else:
            category_averages[category.value] = 0.0

    return ReviewSummary(
        total_reviews=len(reviews),
        overall_average=overall_average,
        category_averages=category_averages,
        last_updated=datetime.utcnow()
    )
```

## 7. ハンドラー設計

### 7.1 ReviewHandler クラス

```python
class ReviewHandler(BaseHandler):
    def initialize(self, review_service: ReviewService):
        self.review_service = review_service

    async def get(self):
        """レビュー一覧表示 (/review)"""

    async def post(self):
        """レビュー投稿処理"""

class ReviewCreateHandler(BaseHandler):
    async def get(self, company_id: str):
        """レビュー投稿フォーム表示"""

    async def post(self, company_id: str):
        """レビュー投稿処理"""

class ReviewUpdateHandler(BaseHandler):
    async def get(self, review_id: str):
        """レビュー編集フォーム表示"""

    async def put(self, review_id: str):
        """レビュー更新処理"""

class ReviewAPIHandler(BaseHandler):
    async def get(self):
        """API: レビュー一覧取得"""

    async def post(self):
        """API: レビュー投稿"""
```

### 7.2 URL ルーティング拡張

```python
# app.py に追加
handlers = [
    # 既存のルート...
    (r"/review", ReviewHandler),
    (r"/companies/([^/]+)/reviews/new", ReviewCreateHandler),
    (r"/reviews/([^/]+)/edit", ReviewUpdateHandler),

    # API エンドポイント
    (r"/api/reviews", ReviewAPIHandler),
    (r"/api/reviews/([^/]+)", ReviewUpdateAPIHandler),
    (r"/api/companies/search", CompanySearchAPIHandler),
]
```

## 8. フロントエンド設計

### 8.1 画面構成

#### 8.1.1 レビュー一覧画面 (/review)
```
┌─────────────────────────────────────────┐
│ ヘッダー (ナビゲーション)                │
├─────────────────────────────────────────┤
│ 検索フォーム                           │
│ [企業名] [所在地] [評価範囲] [検索]      │
├─────────────────────────────────────────┤
│ 検索結果リスト                         │
│ ┌─────────────────────────────────────┐ │
│ │ 企業A  ★3.2 (15件)  東京都          │ │
│ │ 推薦度3.5 受入3.0 風土3.1 ...       │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 企業B  ★2.8 (8件)   大阪府          │ │
│ │ 推薦度2.9 受入2.5 風土2.7 ...       │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ ページネーション                        │
└─────────────────────────────────────────┘
```

#### 8.1.2 レビュー投稿画面
```
┌─────────────────────────────────────────┐
│ 企業情報: 株式会社サンプル               │
├─────────────────────────────────────────┤
│ 在職状況: ○現従業員 ○元従業員            │
├─────────────────────────────────────────┤
│ 評価項目                               │
│                                        │
│ 1. 推薦度合い                          │
│ 他の外国人に就業を推薦したい会社ですか？ │
│ ○1 ○2 ○3 ○4 ○5 ○回答しない            │
│ [コメント入力欄]                        │
│                                        │
│ 2. 外国人の受け入れ制度                 │
│ ...                                    │
├─────────────────────────────────────────┤
│ [プレビュー] [投稿]                     │
└─────────────────────────────────────────┘
```

### 8.2 JavaScript コンポーネント

#### 8.2.1 ReviewForm クラス
```javascript
class ReviewForm {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.ratings = {};
        this.comments = {};
        this.init();
    }

    init() {
        this.renderRatingInputs();
        this.bindEvents();
    }

    renderRatingInputs() {
        // 6つのカテゴリーの評価入力を生成
    }

    validateForm() {
        // フォームバリデーション
    }

    async submitReview() {
        // レビュー投稿処理
    }

    calculatePreviewAverage() {
        // プレビュー用の平均点計算
    }
}
```

#### 8.2.2 SearchInterface クラス
```javascript
class SearchInterface {
    constructor() {
        this.filters = {
            name: '',
            location: '',
            minRating: null,
            maxRating: null
        };
        this.init();
    }

    init() {
        this.bindSearchEvents();
        this.initializePagination();
    }

    async performSearch() {
        // 検索API呼び出し
    }

    renderResults(companies) {
        // 検索結果の表示
    }
}
```

## 9. セキュリティ設計

### 9.1 認証・認可

#### 9.1.1 レビュー投稿権限
```python
async def check_review_permission(self, user_id: str, company_id: str) -> dict:
    """
    レビュー投稿・更新権限をチェック

    Returns:
        {
            "can_create": bool,      # 新規投稿可能
            "can_update": bool,      # 更新可能
            "existing_review_id": str,  # 既存レビューID
            "days_until_next": int   # 次回投稿可能まで日数
        }
    """
```

#### 9.1.2 データアクセス制御
- レビューの編集は投稿者本人のみ
- 1年以内の重複投稿制限
- 論理削除による履歴保持

### 9.2 入力検証

#### 9.2.1 サーバーサイド検証
```python
class ReviewValidator:
    @staticmethod
    def validate_ratings(ratings: dict) -> list:
        """評価データの検証"""
        errors = []

        for category, rating in ratings.items():
            if rating is not None:
                if not isinstance(rating, int) or rating < 1 or rating > 5:
                    errors.append(f"Invalid rating for {category}")

        return errors

    @staticmethod
    def validate_comments(comments: dict) -> list:
        """コメントデータの検証"""
        errors = []

        for category, comment in comments.items():
            if comment is not None and len(comment) > 1000:
                errors.append(f"Comment too long for {category}")

        return errors
```

### 9.3 XSS/CSRF対策

```python
# HTMLエスケープ
import html

def escape_comment(comment: str) -> str:
    """コメントのHTMLエスケープ"""
    return html.escape(comment) if comment else ""

# CSRFトークン
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def check_xsrf_cookie(self):
        """CSRF保護"""
        super().check_xsrf_cookie()
```

## 10. パフォーマンス設計

### 10.1 キャッシュ戦略

#### 10.1.1 企業平均点キャッシュ
```python
import asyncio
from datetime import datetime, timedelta

class ReviewCacheService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)

    async def get_company_summary(self, company_id: str) -> Optional[ReviewSummary]:
        """キャッシュされた企業サマリーを取得"""

    async def invalidate_company_cache(self, company_id: str):
        """企業キャッシュを無効化"""
```

#### 10.1.2 バックグラウンド処理
```python
class ReviewAggregationTask:
    """レビューの集計処理を非同期で実行"""

    async def process_review_aggregation(self, company_id: str):
        """企業の平均点を再計算"""
        try:
            # 重い計算処理を非同期で実行
            summary = await self.calculate_company_averages(company_id)
            await self.update_company_summary(company_id, summary)

        except Exception as e:
            logger.error(f"Aggregation failed for company {company_id}: {e}")
```

### 10.2 データベース最適化

#### 10.2.1 集約クエリ最適化
```python
async def get_company_reviews_aggregated(self, company_id: str) -> dict:
    """MongoDB Aggregation Pipelineを使用した効率的な集計"""

    pipeline = [
        {"$match": {"company_id": company_id, "is_active": True}},
        {"$group": {
            "_id": None,
            "total_reviews": {"$sum": 1},
            "avg_overall": {"$avg": "$individual_average"},
            "avg_recommendation": {"$avg": "$ratings.recommendation"},
            "avg_foreign_support": {"$avg": "$ratings.foreign_support"},
            # ... 他のカテゴリー
        }}
    ]

    result = await self.db.reviews.aggregate(pipeline).to_list(1)
    return result[0] if result else {}
```

## 11. エラーハンドリング

### 11.1 エラーコード定義

```python
class ReviewError(Exception):
    """レビュー関連エラー"""

class DuplicateReviewError(ReviewError):
    """重複投稿エラー"""

class ReviewNotFoundError(ReviewError):
    """レビュー未発見エラー"""

class InvalidRatingError(ReviewError):
    """無効な評価エラー"""
```

### 11.2 エラーレスポンス設計

```python
async def handle_review_error(self, error: Exception) -> dict:
    """エラーレスポンスの生成"""

    if isinstance(error, DuplicateReviewError):
        return {
            "status": "error",
            "code": "DUPLICATE_REVIEW",
            "message": "この会社には既にレビューを投稿済みです。1年後に新規投稿が可能です。",
            "details": {"next_submission_date": "2024-09-21"}
        }

    # その他のエラーハンドリング...
```

## 12. テスト設計

### 12.1 単体テスト

```python
import pytest
from unittest.mock import AsyncMock

class TestReviewService:
    @pytest.fixture
    async def review_service(self):
        mock_db = AsyncMock()
        return ReviewService(mock_db)

    async def test_calculate_individual_average(self, review_service):
        """個別レビュー平均点計算のテスト"""
        ratings = {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": None,  # 回答しない
            "employee_relations": 5,
            "evaluation_system": 2,
            "promotion_treatment": None
        }

        average, count = await review_service.calculate_individual_average(ratings)
        assert average == 3.5  # (4+3+5+2)/4
        assert count == 4

    async def test_duplicate_review_check(self, review_service):
        """重複投稿チェックのテスト"""
        # テストケース実装
```

### 12.2 統合テスト

```python
class TestReviewIntegration:
    async def test_review_submission_flow(self):
        """レビュー投稿フローの統合テスト"""
        # 1. レビュー投稿
        # 2. 企業平均点更新確認
        # 3. 検索結果への反映確認
```

## 13. 監視・ロギング

### 13.1 ログ設計

```python
import logging

# レビュー操作専用ロガー
review_logger = logging.getLogger('review_system')

async def log_review_operation(self, operation: str, user_id: str,
                              company_id: str, success: bool, **kwargs):
    """レビュー操作のログ記録"""
    review_logger.info(
        f"Review {operation} - User: {user_id}, Company: {company_id}, "
        f"Success: {success}, Details: {kwargs}"
    )
```

### 13.2 メトリクス

```python
class ReviewMetrics:
    """レビューシステムのメトリクス収集"""

    @staticmethod
    async def record_review_submission(company_id: str, user_id: str):
        """レビュー投稿メトリクス"""

    @staticmethod
    async def record_search_query(query_params: dict):
        """検索メトリクス"""
```

## 14. デプロイメント

### 14.1 段階的リリース計画

1. **フェーズ1**: データベーススキーマ追加
2. **フェーズ2**: バックエンドAPI実装
3. **フェーズ3**: フロントエンド実装
4. **フェーズ4**: 本格稼働・求人情報削除

### 14.2 マイグレーション

```python
async def migrate_company_schema():
    """既存企業データにレビューサマリーフィールドを追加"""

    update_doc = {
        "$set": {
            "review_summary": {
                "total_reviews": 0,
                "overall_average": 0.0,
                "category_averages": {
                    "recommendation": 0.0,
                    "foreign_support": 0.0,
                    "company_culture": 0.0,
                    "employee_relations": 0.0,
                    "evaluation_system": 0.0,
                    "promotion_treatment": 0.0
                },
                "last_updated": datetime.utcnow()
            }
        }
    }

    await db.companies.update_many({}, update_doc)
```

## 15. 今後の拡張可能性

### 15.1 機能拡張
- レビューに対する「参考になった」機能
- レビューの返信・コメント機能
- 業界別・規模別の比較機能
- レビューのモデレーション機能

### 15.2 技術的拡張
- Elasticsearch導入による高度な検索機能
- Redis導入によるキャッシュ強化
- 機械学習によるレビューの自動分類
- APIの外部公開

この技術設計書に基づいて実装を進めることで、要件を満たす堅牢で拡張性のある企業レビューシステムを構築できます。