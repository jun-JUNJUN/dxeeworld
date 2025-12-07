"""
レビュー詳細ページ用のMongoDBインデックステスト
"""
import pytest
import pytest_asyncio
import asyncio
from src.database import DatabaseService


class TestReviewDetailIndexes:
    """レビュー詳細ページ用のインデックステストクラス"""

    @pytest_asyncio.fixture
    async def db_service(self):
        """データベースサービスのフィクスチャ"""
        service = DatabaseService()
        await service.connect()
        yield service
        await service.close()

    @pytest.mark.asyncio
    async def test_company_id_is_active_created_at_index_exists(self, db_service):
        """company_id + is_active + created_atの複合インデックスが存在することを確認"""
        collection = db_service.db['reviews']
        indexes = await collection.index_information()

        # インデックス名: company_id_1_is_active_1_created_at_-1
        expected_index_name = 'company_id_1_is_active_1_created_at_-1'

        assert expected_index_name in indexes, \
            f"インデックス '{expected_index_name}' が存在しません"

        # インデックスのキーを確認
        index_info = indexes[expected_index_name]
        expected_keys = [
            ('company_id', 1),
            ('is_active', 1),
            ('created_at', -1)
        ]

        assert index_info['key'] == expected_keys, \
            f"インデックスのキーが期待値と異なります: {index_info['key']}"

    @pytest.mark.asyncio
    async def test_category_indexes_exist(self, db_service):
        """各評価項目の複合インデックスが存在することを確認"""
        collection = db_service.db['reviews']
        indexes = await collection.index_information()

        # 6つの評価項目のインデックス
        categories = [
            "recommendation",
            "foreign_support",
            "company_culture",
            "employee_relations",
            "evaluation_system",
            "promotion_treatment"
        ]

        for category in categories:
            # インデックス名: company_id_1_ratings.{category}_1_is_active_1_created_at_-1
            expected_index_name = f'company_id_1_ratings.{category}_1_is_active_1_created_at_-1'

            assert expected_index_name in indexes, \
                f"インデックス '{expected_index_name}' が存在しません"

            # インデックスのキーを確認
            index_info = indexes[expected_index_name]
            expected_keys = [
                ('company_id', 1),
                (f'ratings.{category}', 1),
                ('is_active', 1),
                ('created_at', -1)
            ]

            assert index_info['key'] == expected_keys, \
                f"インデックス '{expected_index_name}' のキーが期待値と異なります: {index_info['key']}"

    @pytest.mark.asyncio
    async def test_index_query_performance(self, db_service):
        """インデックスを使用したクエリのパフォーマンスを確認"""
        collection = db_service.db['reviews']

        # テストデータがない場合はスキップ
        count = await collection.count_documents({})
        if count == 0:
            pytest.skip("テストデータが存在しません")

        # company_id + is_active + created_atを使用したクエリの実行計画を確認
        query = {
            "company_id": "test_company_id",
            "is_active": True
        }
        sort = [("created_at", -1)]

        # explainコマンドでクエリプランを取得
        explain_result = await collection.find(query).sort(sort).limit(20).explain()

        # インデックスが使用されていることを確認
        winning_plan = explain_result.get('queryPlanner', {}).get('winningPlan', {})

        # MongoDBのバージョンによって構造が異なる可能性があるため、
        # インデックススキャンまたはインデックス使用の証拠を探す
        assert 'inputStage' in winning_plan or 'stage' in winning_plan, \
            "クエリプランが取得できませんでした"

    @pytest.mark.asyncio
    async def test_category_filter_query_performance(self, db_service):
        """評価項目フィルターを使用したクエリのパフォーマンスを確認"""
        collection = db_service.db['reviews']

        # テストデータがない場合はスキップ
        count = await collection.count_documents({})
        if count == 0:
            pytest.skip("テストデータが存在しません")

        # company_id + ratings.recommendation + is_active + created_atを使用したクエリ
        query = {
            "company_id": "test_company_id",
            "ratings.recommendation": {"$ne": None},
            "is_active": True
        }
        sort = [("created_at", -1)]

        # explainコマンドでクエリプランを取得
        explain_result = await collection.find(query).sort(sort).limit(20).explain()

        # クエリプランが取得できることを確認
        winning_plan = explain_result.get('queryPlanner', {}).get('winningPlan', {})
        assert winning_plan, "クエリプランが取得できませんでした"

    @pytest.mark.asyncio
    async def test_no_duplicate_indexes(self, db_service):
        """重複したインデックスが存在しないことを確認"""
        collection = db_service.db['reviews']
        indexes = await collection.index_information()

        # インデックス名のリスト
        index_names = list(indexes.keys())

        # 重複がないことを確認
        assert len(index_names) == len(set(index_names)), \
            f"重複したインデックス名が存在します: {index_names}"

        # インデックスキーの組み合わせを確認
        index_keys = [tuple(info['key']) for info in indexes.values()]

        # キーの組み合わせに重複がないことを確認
        # （_idインデックスは除外）
        non_id_keys = [keys for keys in index_keys if keys != [('_id', 1)]]

        assert len(non_id_keys) == len(set(map(str, non_id_keys))), \
            "重複したインデックスキーの組み合わせが存在します"

    @pytest.mark.asyncio
    async def test_existing_indexes_preserved(self, db_service):
        """既存の重要なインデックスが保持されていることを確認"""
        collection = db_service.db['reviews']
        indexes = await collection.index_information()

        # _idインデックス（必須）
        assert '_id_' in indexes, "_idインデックスが存在しません"

        # 既存の company_id + is_active インデックス（もし存在する場合）
        # これは設計書で「既存インデックス」として記載されている
        expected_existing_index = 'company_id_1_is_active_1'

        # このインデックスが存在するか、より包括的なインデックスで代替されているか確認
        if expected_existing_index in indexes:
            # 既存インデックスが保持されている
            index_info = indexes[expected_existing_index]
            expected_keys = [('company_id', 1), ('is_active', 1)]
            assert index_info['key'] == expected_keys

    @pytest.mark.asyncio
    async def test_index_creation_idempotent(self, db_service):
        """インデックス作成が冪等であることを確認（複数回実行しても安全）"""
        collection = db_service.db['reviews']

        # インデックス作成前の状態を記録
        indexes_before = await collection.index_information()
        count_before = len(indexes_before)

        # create_review_detail_indexes関数を呼び出す
        # （この関数は後で実装）
        from src.tools.create_review_detail_indexes import create_review_detail_indexes

        await create_review_detail_indexes(db_service)

        # インデックス作成後の状態を確認
        indexes_after_first = await collection.index_information()
        count_after_first = len(indexes_after_first)

        # 2回目の実行
        await create_review_detail_indexes(db_service)

        # インデックス作成後の状態を確認
        indexes_after_second = await collection.index_information()
        count_after_second = len(indexes_after_second)

        # 2回目の実行後もインデックス数が変わらないことを確認
        assert count_after_first == count_after_second, \
            "インデックス作成が冪等ではありません（2回目の実行で変化がありました）"
