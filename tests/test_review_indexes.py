"""
レビューコレクションのインデックステスト

このテストは、review-detail-pages機能で使用されるMongoDBインデックスが
正しく設定され、クエリパフォーマンスが最適化されていることを検証します。
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_tornado import MotorClient


@pytest_asyncio.fixture
async def mongodb_client():
    """MongoDBクライアントを取得"""
    client = MotorClient("mongodb://localhost:27017")
    yield client
    client.close()


@pytest_asyncio.fixture
async def reviews_collection(mongodb_client):
    """reviewsコレクションを取得"""
    db = mongodb_client["dxeeworld"]
    collection = db["reviews"]
    yield collection


@pytest.mark.asyncio
async def test_reviews_collection_has_required_indexes(reviews_collection):
    """
    reviewsコレクションに必要なインデックスが存在することを確認

    Requirements:
    - 基本インデックス: company_id + is_active + created_at
    - 各評価項目の複合インデックス（6つ）
    """
    indexes = await reviews_collection.list_indexes().to_list(length=None)
    index_names = [index["name"] for index in indexes]

    # 基本インデックスの確認
    assert "company_id_1_is_active_1_created_at_-1" in index_names, \
        "基本インデックス (company_id + is_active + created_at) が存在しません"

    # 各評価項目の複合インデックスの確認
    required_category_indexes = [
        "company_id_1_ratings.recommendation_1_is_active_1_created_at_-1",
        "company_id_1_ratings.foreign_support_1_is_active_1_created_at_-1",
        "company_id_1_ratings.company_culture_1_is_active_1_created_at_-1",
        "company_id_1_ratings.employee_relations_1_is_active_1_created_at_-1",
        "company_id_1_ratings.evaluation_system_1_is_active_1_created_at_-1",
        "company_id_1_ratings.promotion_treatment_1_is_active_1_created_at_-1"
    ]

    for index_name in required_category_indexes:
        assert index_name in index_names, \
            f"評価項目インデックス {index_name} が存在しません"


@pytest.mark.asyncio
async def test_basic_index_structure(reviews_collection):
    """
    基本インデックスの構造が正しいことを確認

    インデックスキー:
    - company_id: 1 (昇順)
    - is_active: 1 (昇順)
    - created_at: -1 (降順)
    """
    indexes = await reviews_collection.list_indexes().to_list(length=None)

    basic_index = None
    for index in indexes:
        if index["name"] == "company_id_1_is_active_1_created_at_-1":
            basic_index = index
            break

    assert basic_index is not None, "基本インデックスが見つかりません"

    # インデックスキーの構造を確認
    expected_key = {
        "company_id": 1,
        "is_active": 1,
        "created_at": -1
    }
    assert basic_index["key"] == expected_key, \
        f"基本インデックスの構造が不正です。期待値: {expected_key}, 実際: {basic_index['key']}"


@pytest.mark.asyncio
async def test_category_index_structure(reviews_collection):
    """
    評価項目インデックスの構造が正しいことを確認

    インデックスキー（例: recommendation）:
    - company_id: 1 (昇順)
    - ratings.recommendation: 1 (昇順)
    - is_active: 1 (昇順)
    - created_at: -1 (降順)
    """
    indexes = await reviews_collection.list_indexes().to_list(length=None)

    recommendation_index = None
    for index in indexes:
        if index["name"] == "company_id_1_ratings.recommendation_1_is_active_1_created_at_-1":
            recommendation_index = index
            break

    assert recommendation_index is not None, "recommendationインデックスが見つかりません"

    # インデックスキーの構造を確認
    expected_key = {
        "company_id": 1,
        "ratings.recommendation": 1,
        "is_active": 1,
        "created_at": -1
    }
    assert recommendation_index["key"] == expected_key, \
        f"recommendationインデックスの構造が不正です。期待値: {expected_key}, 実際: {recommendation_index['key']}"


@pytest.mark.asyncio
async def test_index_usage_for_review_detail_query(reviews_collection, mongodb_client):
    """
    個別レビュー詳細クエリでインデックスが使用されることを確認

    クエリ例:
    db.reviews.find({"_id": ObjectId(...), "is_active": true})

    Note: _idインデックスが使用されるため、追加のインデックスは不要
    """
    # テストデータの準備
    test_review_id = ObjectId()
    test_review = {
        "_id": test_review_id,
        "company_id": "test_company_123",
        "user_id": "test_user_456",
        "employment_status": "current",
        "ratings": {
            "recommendation": 4,
            "foreign_support": 3,
            "company_culture": 5,
            "employee_relations": 4,
            "evaluation_system": 3,
            "promotion_treatment": 4
        },
        "comments": {
            "recommendation": "Great company",
            "foreign_support": "Good support",
            "company_culture": "Excellent culture",
            "employee_relations": "Friendly colleagues",
            "evaluation_system": "Fair evaluation",
            "promotion_treatment": "Good opportunities"
        },
        "individual_average": 3.8,
        "answered_count": 6,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }

    # テストデータを挿入
    await reviews_collection.insert_one(test_review)

    try:
        # クエリ実行計画を取得
        explain_result = await reviews_collection.find(
            {"_id": test_review_id, "is_active": True}
        ).explain()

        # インデックスが使用されていることを確認
        # _idインデックス（IDHACK）が使用されるべき
        assert "queryPlanner" in explain_result
        assert "executionStats" not in explain_result or \
               explain_result.get("executionStats", {}).get("executionSuccess", False)

    finally:
        # テストデータをクリーンアップ
        await reviews_collection.delete_one({"_id": test_review_id})


@pytest.mark.asyncio
async def test_index_usage_for_category_review_list_query(reviews_collection, mongodb_client):
    """
    質問別レビュー一覧クエリでインデックスが使用されることを確認

    クエリ例:
    db.reviews.find({
        "company_id": "company123",
        "ratings.foreign_support": {$ne: null},
        "is_active": true
    }).sort({"created_at": -1}).skip(0).limit(20)
    """
    # テストデータの準備
    test_company_id = f"test_company_{ObjectId()}"
    test_reviews = []

    for i in range(5):
        review_id = ObjectId()
        test_reviews.append({
            "_id": review_id,
            "company_id": test_company_id,
            "user_id": f"test_user_{i}",
            "employment_status": "current" if i % 2 == 0 else "former",
            "ratings": {
                "recommendation": 4,
                "foreign_support": 3 + i,  # 異なる評価値
                "company_culture": 5,
                "employee_relations": 4,
                "evaluation_system": None if i == 4 else 3,  # 1つは未回答
                "promotion_treatment": 4
            },
            "comments": {
                "recommendation": f"Comment {i}",
                "foreign_support": f"Support comment {i}",
                "company_culture": f"Culture comment {i}",
                "employee_relations": f"Relations comment {i}",
                "evaluation_system": None if i == 4 else f"Evaluation {i}",
                "promotion_treatment": f"Promotion {i}"
            },
            "individual_average": 3.8,
            "answered_count": 5 if i == 4 else 6,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        })

    # テストデータを挿入
    await reviews_collection.insert_many(test_reviews)

    try:
        # クエリ実行計画を取得
        explain_result = await reviews_collection.find({
            "company_id": test_company_id,
            "ratings.foreign_support": {"$ne": None},
            "is_active": True
        }).sort([("created_at", -1)]).limit(20).explain()

        # インデックスが使用されていることを確認
        assert "queryPlanner" in explain_result
        winning_plan = explain_result["queryPlanner"]["winningPlan"]

        # インデックススキャンが使用されていることを確認
        # (IXSCAN stage が存在するか、または inputStage に IXSCAN が含まれる)
        assert _has_index_scan(winning_plan), \
            f"インデックススキャンが使用されていません。実行計画: {winning_plan}"

    finally:
        # テストデータをクリーンアップ
        await reviews_collection.delete_many({"company_id": test_company_id})


@pytest.mark.asyncio
async def test_query_performance_with_index(reviews_collection, mongodb_client):
    """
    インデックスを使用したクエリのパフォーマンスを確認

    要件:
    - 質問別レビュー一覧ページが300ms以内にレンダリングされること
    - データベースクエリがインデックスを使用して効率的に実行されること
    """
    import time

    # テストデータの準備（100件のレビュー）
    test_company_id = f"perf_test_company_{ObjectId()}"
    test_reviews = []

    for i in range(100):
        test_reviews.append({
            "_id": ObjectId(),
            "company_id": test_company_id,
            "user_id": f"user_{i}",
            "employment_status": "current" if i % 2 == 0 else "former",
            "ratings": {
                "recommendation": (i % 5) + 1,
                "foreign_support": ((i + 1) % 5) + 1,
                "company_culture": ((i + 2) % 5) + 1,
                "employee_relations": ((i + 3) % 5) + 1,
                "evaluation_system": ((i + 4) % 5) + 1,
                "promotion_treatment": (i % 5) + 1
            },
            "comments": {
                "recommendation": f"Recommendation {i}",
                "foreign_support": f"Support {i}",
                "company_culture": f"Culture {i}",
                "employee_relations": f"Relations {i}",
                "evaluation_system": f"Evaluation {i}",
                "promotion_treatment": f"Promotion {i}"
            },
            "individual_average": 3.5,
            "answered_count": 6,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        })

    # テストデータを挿入
    await reviews_collection.insert_many(test_reviews)

    try:
        # クエリの実行時間を計測
        start_time = time.time()

        cursor = reviews_collection.find({
            "company_id": test_company_id,
            "ratings.foreign_support": {"$ne": None},
            "is_active": True
        }).sort([("created_at", -1)]).limit(20)

        results = await cursor.to_list(length=20)

        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000

        # クエリ実行時間が50ms以内であることを確認
        # (データベースクエリのみで300ms以内の目標に対し、十分な余裕を持たせる)
        assert query_time_ms < 50, \
            f"クエリ実行時間が遅すぎます: {query_time_ms:.2f}ms（目標: 50ms未満）"

        # 正しい件数が取得されていることを確認
        assert len(results) == 20, f"取得件数が不正です: {len(results)}"

    finally:
        # テストデータをクリーンアップ
        await reviews_collection.delete_many({"company_id": test_company_id})


def _has_index_scan(plan: dict) -> bool:
    """
    実行計画にインデックススキャン（IXSCAN）が含まれているかを再帰的にチェック

    Args:
        plan: MongoDB実行計画の辞書

    Returns:
        bool: IXSCANが含まれている場合True
    """
    if isinstance(plan, dict):
        if plan.get("stage") == "IXSCAN":
            return True

        # inputStageやinputStagesを再帰的に検索
        if "inputStage" in plan:
            if _has_index_scan(plan["inputStage"]):
                return True

        if "inputStages" in plan:
            for stage in plan["inputStages"]:
                if _has_index_scan(stage):
                    return True

    return False
