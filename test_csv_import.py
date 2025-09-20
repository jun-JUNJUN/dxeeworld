#!/usr/bin/env python3
"""
CSVインポートテストスクリプト
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# プロジェクトパスを追加
sys.path.append('/Users/jun77/Documents/Dropbox/a_root/code/dxeeworld')

from src.services.csv_import_service import CSVImportService
from src.services.company_service import CompanyService
from src.database import DatabaseService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockDbService:
    """モックデータベースサービス（テスト用）"""
    def __init__(self):
        self.companies = {}
        self.import_logs = []
        self.counters = {'companies': 0, 'import_logs': 0}

    async def find_one(self, collection, query):
        if collection == 'companies':
            name = query.get('name')
            return self.companies.get(name)
        return None

    async def create(self, collection, document):
        if collection == 'companies':
            self.counters['companies'] += 1
            doc_id = f"company_{self.counters['companies']}"
            document['_id'] = doc_id
            self.companies[document['name']] = document
            return doc_id
        elif collection == 'import_logs':
            self.counters['import_logs'] += 1
            doc_id = f"log_{self.counters['import_logs']}"
            document['_id'] = doc_id
            self.import_logs.append(document)
            return doc_id
        return None

    async def update_one(self, collection, query, update_doc):
        if collection == 'companies':
            name = query.get('name') or query.get('_id')
            if name in self.companies:
                self.companies[name].update(update_doc)
                return True
        return False

    async def count_documents(self, collection, query):
        if collection == 'companies':
            count = 0
            for company in self.companies.values():
                if not query or all(
                    company.get(k) == v for k, v in query.items()
                ):
                    count += 1
            return count
        return 0

    async def aggregate(self, collection, pipeline):
        if collection == 'companies':
            results = []
            companies = list(self.companies.values())

            # 簡単な集約処理（実際のMongoDBより簡略化）
            for step in pipeline:
                if '$match' in step:
                    # フィルタリング
                    match_conditions = step['$match']
                    filtered_companies = []
                    for company in companies:
                        if all(company.get(k) == v for k, v in match_conditions.items()):
                            filtered_companies.append(company)
                    companies = filtered_companies

                elif '$group' in step:
                    # グループ化
                    group_by = step['$group']['_id']
                    if group_by.startswith('$'):
                        field = group_by[1:]
                        groups = {}
                        for company in companies:
                            key = company.get(field, 'unknown')
                            if key not in groups:
                                groups[key] = 0
                            groups[key] += 1
                        results = [{'_id': k, 'count': v} for k, v in groups.items()]

                elif '$unwind' in step:
                    # 配列の展開
                    field = step['$unwind'][1:]  # $を除去
                    unwound = []
                    for company in companies:
                        array_field = company.get(field, [])
                        if isinstance(array_field, list):
                            for item in array_field:
                                new_company = company.copy()
                                new_company[field] = item
                                unwound.append(new_company)
                    companies = unwound

                elif '$sort' in step:
                    # ソート（簡略化）
                    sort_field = list(step['$sort'].keys())[0]
                    reverse = step['$sort'][sort_field] == -1
                    if results:
                        results.sort(key=lambda x: x.get('count', 0), reverse=reverse)

                elif '$limit' in step:
                    # 制限
                    limit = step['$limit']
                    if results:
                        results = results[:limit]
                    else:
                        companies = companies[:limit]
                        results = [{'updated_at': comp.get('updated_at')} for comp in companies]

            return results
        return []

async def main():
    """メイン実行関数"""
    logger.info("CSVインポートテスト開始")

    # モックサービス初期化
    db_service = MockDbService()
    company_service = CompanyService(db_service)
    csv_import_service = CSVImportService(db_service, company_service)

    # 開始時統計
    initial_stats = await company_service.get_import_statistics()
    logger.info(f"開始時統計: {initial_stats}")

    print("=" * 60)
    print("CSV IMPORT TEST - STARTING")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    print(f"初期企業数: {initial_stats.get('total_companies', 0)}")
    print()

    # 外資系企業CSVインポート
    logger.info("外資系企業CSVインポート開始")
    foreign_csv_path = "/Users/jun77/Documents/Dropbox/a_root/code/dxeeworld/foreign_companies_101_300_japan_asia_complete.csv"

    if os.path.exists(foreign_csv_path):
        print("1. 外資系企業CSVインポート実行中...")
        foreign_result = await csv_import_service.import_foreign_companies_csv(foreign_csv_path)
        print(f"   ステータス: {foreign_result.status.value}")
        print(f"   処理件数: {foreign_result.processed_count}")
        print(f"   エラー件数: {foreign_result.error_count}")
        if foreign_result.errors:
            print(f"   エラー例: {foreign_result.errors[:3]}")
        print()
    else:
        print(f"外資系企業CSVファイルが見つかりません: {foreign_csv_path}")

    # 日本建設業CSVインポート
    logger.info("日本建設業CSVインポート開始")
    japan_csv_path = "/Users/jun77/Documents/Dropbox/a_root/code/dxeeworld/japan-construction-2025-8-26.csv"

    if os.path.exists(japan_csv_path):
        print("2. 日本建設業CSVインポート実行中...")
        japan_result = await csv_import_service.import_japan_construction_csv(japan_csv_path)
        print(f"   ステータス: {japan_result.status.value}")
        print(f"   処理件数: {japan_result.processed_count}")
        print(f"   エラー件数: {japan_result.error_count}")
        if japan_result.errors:
            print(f"   エラー例: {japan_result.errors[:3]}")
        print()
    else:
        print(f"日本建設業CSVファイルが見つかりません: {japan_csv_path}")

    # 最終統計
    final_stats = await company_service.get_import_statistics()
    logger.info(f"最終統計: {final_stats}")

    print("=" * 60)
    print("MONGODB統計情報")
    print("=" * 60)
    print(f"総企業数: {final_stats.get('total_companies', 0)}")
    print(f"アクティブ企業数: {final_stats.get('active_companies', 0)}")
    print(f"非アクティブ企業数: {final_stats.get('inactive_companies', 0)}")
    print()

    print("業界別分布:")
    industry_dist = final_stats.get('industry_distribution', {})
    for industry, count in sorted(industry_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {industry}: {count}社")
    print()

    print("企業規模別分布:")
    size_dist = final_stats.get('size_distribution', {})
    for size, count in sorted(size_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {size}: {count}社")
    print()

    print("ソースファイル別分布:")
    source_dist = final_stats.get('source_file_distribution', {})
    for source, count in source_dist.items():
        print(f"  {source}: {count}社")
    print()

    print("インポートログ:")
    for i, log in enumerate(db_service.import_logs, 1):
        print(f"  ログ{i}:")
        print(f"    ファイル: {log.get('source_file', 'N/A')}")
        print(f"    ステータス: {log.get('status', 'N/A')}")
        print(f"    処理件数: {log.get('processed_count', 0)}")
        print(f"    エラー件数: {log.get('error_count', 0)}")
        print(f"    タイムスタンプ: {log.get('timestamp', 'N/A')}")
        print()

    print("=" * 60)
    print("インポート完了")
    print("=" * 60)

    # サンプル企業データ表示
    print("サンプル企業データ (最初の5社):")
    count = 0
    for name, company in db_service.companies.items():
        if count >= 5:
            break
        print(f"  {count + 1}. {company.get('name_original', name)}")
        print(f"     国: {company.get('country', 'N/A')}")
        print(f"     業界: {company.get('industry', 'N/A')}")
        print(f"     所在地: {company.get('location', 'N/A')}")
        print()
        count += 1

if __name__ == "__main__":
    asyncio.run(main())