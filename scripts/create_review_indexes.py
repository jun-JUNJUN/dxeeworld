#!/usr/bin/env python3
"""
レビューコレクションのインデックス作成スクリプト

このスクリプトは、review-detail-pages機能で使用されるMongoDBインデックスを作成します。
既にインデックスが存在する場合は、スキップされます。

使用方法:
    python scripts/create_review_indexes.py

または:
    uv run python scripts/create_review_indexes.py
"""
import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_tornado import MotorClient
from src.config import Config


async def create_indexes():
    """レビューコレクションにインデックスを作成"""
    config = Config()
    client = MotorClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    collection = db["reviews"]

    print("レビューコレクションのインデックスを作成中...")

    try:
        # 既存のインデックスを取得
        existing_indexes = await collection.list_indexes().to_list(length=None)
        existing_index_names = {index["name"] for index in existing_indexes}

        # 作成するインデックスのリスト
        indexes_to_create = []

        # 1. 基本インデックス: company_id + is_active + created_at
        basic_index_name = "company_id_1_is_active_1_created_at_-1"
        if basic_index_name not in existing_index_names:
            indexes_to_create.append({
                "keys": [("company_id", 1), ("is_active", 1), ("created_at", -1)],
                "name": basic_index_name,
                "description": "個別レビュー詳細および質問別レビュー一覧クエリの最適化"
            })
        else:
            print(f"  ✓ {basic_index_name} - 既に存在します")

        # 2. 各評価項目の複合インデックス
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment"
        ]

        for category in categories:
            index_name = f"company_id_1_ratings.{category}_1_is_active_1_created_at_-1"
            if index_name not in existing_index_names:
                indexes_to_create.append({
                    "keys": [
                        ("company_id", 1),
                        (f"ratings.{category}", 1),
                        ("is_active", 1),
                        ("created_at", -1)
                    ],
                    "name": index_name,
                    "description": f"{category}評価項目の質問別レビュー一覧クエリの最適化"
                })
            else:
                print(f"  ✓ {index_name} - 既に存在します")

        # インデックスを作成
        if indexes_to_create:
            print(f"\n{len(indexes_to_create)}個の新しいインデックスを作成します...")
            for index_info in indexes_to_create:
                keys = index_info["keys"]
                name = index_info["name"]
                description = index_info["description"]

                print(f"\n  作成中: {name}")
                print(f"  説明: {description}")

                await collection.create_index(keys, name=name)
                print(f"  ✓ 作成完了")

            print(f"\n✓ {len(indexes_to_create)}個のインデックスを作成しました")
        else:
            print("\n✓ すべての必要なインデックスは既に存在します")

        # 作成後のインデックス一覧を表示
        print("\n現在のインデックス一覧:")
        all_indexes = await collection.list_indexes().to_list(length=None)
        for index in all_indexes:
            print(f"  - {index['name']}")

        print("\n✓ インデックス作成処理が完了しました")

    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        raise
    finally:
        client.close()


async def verify_indexes():
    """インデックスが正しく作成されているかを検証"""
    config = Config()
    client = MotorClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    collection = db["reviews"]

    print("\nインデックスの検証中...")

    try:
        indexes = await collection.list_indexes().to_list(length=None)
        index_names = {index["name"] for index in indexes}

        # 必須インデックスのリスト
        required_indexes = [
            "company_id_1_is_active_1_created_at_-1",
            "company_id_1_ratings.recommendation_1_is_active_1_created_at_-1",
            "company_id_1_ratings.foreign_support_1_is_active_1_created_at_-1",
            "company_id_1_ratings.company_culture_1_is_active_1_created_at_-1",
            "company_id_1_ratings.employee_relations_1_is_active_1_created_at_-1",
            "company_id_1_ratings.evaluation_system_1_is_active_1_created_at_-1",
            "company_id_1_ratings.promotion_treatment_1_is_active_1_created_at_-1"
        ]

        all_present = True
        for required_index in required_indexes:
            if required_index in index_names:
                print(f"  ✓ {required_index}")
            else:
                print(f"  ✗ {required_index} - 見つかりません")
                all_present = False

        if all_present:
            print("\n✓ すべての必須インデックスが存在します")
            return True
        else:
            print("\n✗ 一部のインデックスが見つかりません")
            return False

    except Exception as e:
        print(f"\n✗ 検証中にエラーが発生しました: {e}")
        return False
    finally:
        client.close()


async def main():
    """メイン処理"""
    print("=" * 70)
    print("レビューコレクション インデックス作成スクリプト")
    print("=" * 70)
    print()

    # インデックスを作成
    await create_indexes()

    # インデックスを検証
    success = await verify_indexes()

    print()
    print("=" * 70)
    if success:
        print("✓ 処理が正常に完了しました")
    else:
        print("✗ 処理中にエラーが発生しました")
        sys.exit(1)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
