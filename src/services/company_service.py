"""
企業管理サービス
"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..models.company import Company, IndustryType, CompanySize
from ..utils.result import Result

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """バリデーションエラー"""
    
    def __init__(self, field_errors: Dict[str, List[str]]):
        self.field_errors = field_errors
        super().__init__(f"Validation failed: {field_errors}")


class CompanyService:
    """企業管理サービス"""
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def validate_company_data(self, company_data: dict) -> Result[bool, ValidationError]:
        """企業データの検証"""
        errors = {}
        
        # 企業名検証
        name = company_data.get('name', '').strip()
        if not name:
            errors['name'] = ['Company name is required']
        elif len(name) < 2:
            errors['name'] = ['Company name must be at least 2 characters']
        
        # 業界検証
        industry = company_data.get('industry')
        try:
            IndustryType(industry)
        except (ValueError, TypeError):
            errors['industry'] = ['Invalid industry type']
        
        # 企業規模検証
        size = company_data.get('size')
        try:
            CompanySize(size)
        except (ValueError, TypeError):
            errors['size'] = ['Invalid company size']
        
        # ウェブサイトURL検証（任意）
        website = company_data.get('website')
        if website and not self._is_valid_url(website):
            errors['website'] = ['Invalid website URL format']
        
        # 設立年検証（任意）
        founded_year = company_data.get('founded_year')
        if founded_year is not None:
            current_year = datetime.now().year
            if not isinstance(founded_year, int) or founded_year < 1800 or founded_year > current_year:
                errors['founded_year'] = [f'Founded year must be between 1800 and {current_year}']
        
        # 従業員数検証（任意）
        employee_count = company_data.get('employee_count')
        if employee_count is not None:
            if not isinstance(employee_count, int) or employee_count < 0:
                errors['employee_count'] = ['Employee count must be a positive integer']

        # 所在地・国名検証（必須）
        location = company_data.get('location', '').strip()
        country = company_data.get('country', '').strip()

        if not country:
            errors['country'] = ['Country information is required for all companies']

        if not location:
            errors['location'] = ['Location information is required for all companies']
        elif not self._validate_location_includes_country(location, country):
            errors['location'] = ['Location must include country information or be consistent with country field']

        if errors:
            return Result.failure(ValidationError(errors))

        return Result.success(True)
    
    async def create_company(self, company_data: dict) -> Result[Company, ValidationError]:
        """企業を作成"""
        # バリデーション
        validation_result = self.validate_company_data(company_data)
        if not validation_result.is_success:
            return Result.failure(validation_result.error)
        
        # 企業名重複チェック
        name = company_data['name'].strip()
        existing_company = await self.db_service.find_one('companies', {'name': name})
        if existing_company:
            return Result.failure(ValidationError({'name': ['Company name already exists']}))
        
        # 企業データ作成
        company_doc = {
            'name': name,
            'industry': company_data['industry'],
            'size': company_data['size'],
            'country': company_data['country'],
            'description': company_data.get('description'),
            'website': company_data.get('website'),
            'location': company_data.get('location'),
            'founded_year': company_data.get('founded_year'),
            'employee_count': company_data.get('employee_count'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }
        
        # データベースに保存
        company_id = await self.db_service.create('companies', company_doc)
        
        # Companyオブジェクト作成
        company = Company(
            id=str(company_id),
            name=name,
            industry=IndustryType(company_data['industry']),
            size=CompanySize(company_data['size']),
            country=company_data['country'],
            description=company_data.get('description'),
            website=company_data.get('website'),
            location=company_data.get('location'),
            founded_year=company_data.get('founded_year'),
            employee_count=company_data.get('employee_count'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return Result.success(company)
    
    async def get_company(self, company_id: str) -> Optional[Company]:
        """企業IDで企業を取得"""
        try:
            from bson import ObjectId

            # ObjectId に変換
            object_id = ObjectId(company_id)
            company_doc = await self.db_service.find_one('companies', {'_id': object_id})
            if company_doc:
                # 安全なデータ変換
                industry_value = company_doc.get('industry', 'other')
                size_value = company_doc.get('size', 'startup')

                # 有効なenumかチェック
                try:
                    IndustryType(industry_value)
                except ValueError:
                    industry_value = 'other'

                try:
                    CompanySize(size_value)
                except ValueError:
                    size_value = 'startup'

                # docをコピーして安全な値を設定
                safe_doc = dict(company_doc)
                safe_doc['industry'] = industry_value
                safe_doc['size'] = size_value

                return Company.from_dict(safe_doc)
            return None
        except Exception as e:
            logger.error(f"get_company エラー: {e}")
            return None
    
    async def search_companies(self,
                             industry: Optional[str] = None,
                             location: Optional[str] = None,
                             size: Optional[str] = None,
                             limit: int = 10) -> List[Company]:
        """企業を検索"""
        try:
            filter_dict = {'is_active': True}

            if industry:
                filter_dict['industry'] = industry
            if location:
                filter_dict['location'] = {'$regex': location, '$options': 'i'}
            if size:
                filter_dict['size'] = size

            company_docs = await self.db_service.find_many('companies', filter_dict, limit=limit)
            companies = [Company.from_dict(doc) for doc in company_docs]
            return companies

        except Exception:
            return []

    async def search_companies_with_pagination(self,
                                             filters: dict,
                                             skip: int = 0,
                                             limit: int = 30,
                                             sort: Optional[list] = None) -> List[Company]:
        """ページネーション付きで企業を検索"""
        try:
            if sort is None:
                sort = [('name', 1)]  # デフォルトは企業名昇順

            company_docs = await self.db_service.find_many(
                'companies',
                filters,
                skip=skip,
                limit=limit,
                sort=sort
            )
            companies = []
            for doc in company_docs:
                try:
                    # 安全なデータ変換
                    industry_value = doc.get('industry', 'other')
                    size_value = doc.get('size', 'startup')

                    # 有効なenumかチェック
                    try:
                        IndustryType(industry_value)
                    except ValueError:
                        industry_value = 'other'

                    try:
                        CompanySize(size_value)
                    except ValueError:
                        size_value = 'startup'

                    # docをコピーして安全な値を設定
                    safe_doc = dict(doc)
                    safe_doc['industry'] = industry_value
                    safe_doc['size'] = size_value

                    company = Company.from_dict(safe_doc)
                    companies.append(company)
                except Exception as conversion_error:
                    logger.warning(f"Company conversion error for {doc.get('name', 'unknown')}: {conversion_error}")
                    continue

            return companies

        except Exception as e:
            logger.error(f"search_companies_with_pagination エラー: {e}")
            return []

    async def count_companies_with_filters(self, filters: dict) -> int:
        """フィルター条件に一致する企業数を取得"""
        try:
            return await self.db_service.count_documents('companies', filters)
        except Exception as e:
            logger.error(f"count_companies_with_filters エラー: {e}")
            return 0
    
    async def update_company(self, company_id: str, update_data: dict) -> Result[Company, ValidationError]:
        """企業情報を更新"""
        # バリデーション
        validation_result = self.validate_company_data(update_data)
        if not validation_result.is_success:
            return Result.failure(validation_result.error)

        # 企業名重複チェック（自分以外）
        name = update_data.get('name', '').strip()
        if name:
            existing_company = await self.db_service.find_one('companies', {
                'name': name,
                '_id': {'$ne': company_id}
            })
            if existing_company:
                return Result.failure(ValidationError({'name': ['Company name already exists']}))

        # 更新データ準備
        update_doc = {**update_data, 'updated_at': datetime.utcnow()}

        # データベース更新
        update_success = await self.db_service.update_one('companies', {'_id': company_id}, update_doc)
        if not update_success:
            return Result.failure(ValidationError({'id': ['Company not found or update failed']}))

        # 更新された企業を取得
        updated_company = await self.get_company(company_id)
        if updated_company:
            return Result.success(updated_company)
        else:
            return Result.failure(ValidationError({'id': ['Company not found']}))

    async def delete_company(self, company_id: str) -> bool:
        """企業を削除（論理削除）"""
        try:
            # 論理削除: is_active を False に設定
            return await self.db_service.update_one(
                'companies',
                {'_id': company_id},
                {'is_active': False, 'updated_at': datetime.utcnow()}
            )
        except Exception:
            return False

    async def create_company_indexes(self) -> bool:
        """企業コレクションのインデックスを作成"""
        try:
            # 企業名の一意インデックス
            await self.db_service.create_index(
                'companies',
                [('name', 1)],
                unique=True
            )

            # 業界による検索インデックス
            await self.db_service.create_index(
                'companies',
                [('industry', 1)]
            )

            # 地域による検索インデックス
            await self.db_service.create_index(
                'companies',
                [('location', 1)]
            )

            # 企業規模インデックス
            await self.db_service.create_index(
                'companies',
                [('size', 1)]
            )

            # 設立年インデックス
            await self.db_service.create_index(
                'companies',
                [('founded_year', 1)]
            )

            # 従業員数インデックス
            await self.db_service.create_index(
                'companies',
                [('employee_count', 1)]
            )

            # テキスト検索インデックス
            await self.db_service.create_index(
                'companies',
                [('name', 'text'), ('description', 'text')]
            )

            # 複合インデックス（業界 + 企業規模 + 所在地）
            await self.db_service.create_index(
                'companies',
                [('industry', 1), ('size', 1), ('location', 1)]
            )

            # ページネーション最適化インデックス
            await self.db_service.create_index(
                'companies',
                [('created_at', -1)]
            )

            # 名前＋作成日時インデックス（ソート最適化）
            await self.db_service.create_index(
                'companies',
                [('name', 1), ('created_at', -1)]
            )

            # アクティブ企業フィルターインデックス
            await self.db_service.create_index(
                'companies',
                [('is_active', 1)]
            )

            return True

        except Exception as e:
            logger.error(f"インデックス作成エラー: {e}")
            return False

    async def create_review_summary_indexes(self) -> bool:
        """
        レビュー集計データ用のインデックスを作成

        レビュー一覧ページの検索・ソート機能を最適化するためのインデックス:
        - review_summary.overall_average: 評価順ソート用
        - review_summary.total_reviews: レビュー数順ソート用
        - review_summary.last_updated: 最新レビュー順ソート用
        - 複合インデックス: 評価範囲フィルタ + レビュー数ソートの最適化

        Returns:
            bool: インデックス作成が成功した場合True、失敗した場合False
        """
        try:
            # 総合評価平均の降順インデックス（評価順ソート用）
            await self.db_service.create_index(
                'companies',
                [('review_summary.overall_average', -1)]
            )

            # レビュー総数の降順インデックス（レビュー数順ソート用）
            await self.db_service.create_index(
                'companies',
                [('review_summary.total_reviews', -1)]
            )

            # 最終更新日時の降順インデックス（最新レビュー順ソート用）
            await self.db_service.create_index(
                'companies',
                [('review_summary.last_updated', -1)]
            )

            # 複合インデックス（評価範囲フィルタ + レビュー数ソート最適化）
            await self.db_service.create_index(
                'companies',
                [('review_summary.overall_average', -1), ('review_summary.total_reviews', -1)]
            )

            logger.info("レビュー集計データ用のインデックスを作成しました（4件）")
            return True

        except Exception as e:
            logger.exception("レビュー集計インデックス作成エラー: %s", e)
            return False

    async def search_companies_by_text(self, search_text: str, limit: int = 10) -> List[Company]:
        """テキスト検索による企業検索"""
        try:
            pipeline = [
                {
                    '$match': {
                        '$text': {'$search': search_text},
                        'is_active': True
                    }
                },
                {
                    '$addFields': {
                        'score': {'$meta': 'textScore'}
                    }
                },
                {
                    '$sort': {'score': {'$meta': 'textScore'}}
                },
                {
                    '$limit': limit
                }
            ]

            company_docs = await self.db_service.aggregate('companies', pipeline)
            companies = [Company.from_dict(doc) for doc in company_docs]
            return companies

        except Exception:
            return []

    async def bulk_create_companies(self, companies_data: List[dict]) -> Result[List[Company], ValidationError]:
        """複数企業の一括作成"""
        try:
            # 全データのバリデーション
            for company_data in companies_data:
                validation_result = self.validate_company_data(company_data)
                if not validation_result.is_success:
                    return Result.failure(validation_result.error)

            # 企業名重複チェック
            for company_data in companies_data:
                name = company_data['name'].strip()
                existing_company = await self.db_service.find_one('companies', {'name': name})
                if existing_company:
                    return Result.failure(ValidationError({
                        'name': [f'Company name "{name}" already exists']
                    }))

            # 一括挿入用ドキュメント準備
            docs = []
            for company_data in companies_data:
                doc = {
                    'name': company_data['name'].strip(),
                    'industry': company_data['industry'],
                    'size': company_data['size'],
                    'description': company_data.get('description'),
                    'website': company_data.get('website'),
                    'location': company_data.get('location'),
                    'founded_year': company_data.get('founded_year'),
                    'employee_count': company_data.get('employee_count'),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'is_active': True
                }
                docs.append(doc)

            # 一括挿入
            inserted_ids = await self.db_service.bulk_insert('companies', docs)

            # Companyオブジェクトリスト作成
            companies = []
            for i, company_data in enumerate(companies_data):
                company = Company(
                    id=str(inserted_ids[i]),
                    name=company_data['name'].strip(),
                    industry=IndustryType(company_data['industry']),
                    size=CompanySize(company_data['size']),
                    description=company_data.get('description'),
                    website=company_data.get('website'),
                    location=company_data.get('location'),
                    founded_year=company_data.get('founded_year'),
                    employee_count=company_data.get('employee_count'),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                companies.append(company)

            return Result.success(companies)

        except Exception as e:
            logger.error(f"bulk_create_companies エラー: {e}")
            return Result.failure(ValidationError({'bulk': ['Bulk creation failed']}))

    async def bulk_update_companies(self, updates: List[dict]) -> int:
        """複数企業の一括更新"""
        try:
            # UpdateOneオペレーション形式に変換
            bulk_updates = []
            for update in updates:
                company_id = update['company_id']
                update_data = update['update_data']

                bulk_updates.append({
                    'filter': {'_id': company_id},
                    'update': {'$set': {**update_data, 'updated_at': datetime.utcnow()}}
                })

            return await self.db_service.bulk_update('companies', bulk_updates)

        except Exception as e:
            logger.error(f"bulk_update_companies エラー: {e}")
            return 0

    async def get_import_statistics(self) -> dict:
        """インポート統計情報を取得"""
        try:
            # 総企業数
            total_companies = await self.db_service.count_documents('companies', {})

            # アクティブな企業数
            active_companies = await self.db_service.count_documents('companies', {'is_active': True})

            # 業界別企業数
            industry_pipeline = [
                {'$match': {'is_active': True}},
                {'$group': {'_id': '$industry', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            industry_stats = await self.db_service.aggregate('companies', industry_pipeline)

            # 企業規模別企業数
            size_pipeline = [
                {'$match': {'is_active': True}},
                {'$group': {'_id': '$size', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            size_stats = await self.db_service.aggregate('companies', size_pipeline)

            # ソースファイル別企業数
            source_pipeline = [
                {'$match': {'is_active': True}},
                {'$unwind': '$source_files'},
                {'$group': {'_id': '$source_files', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            source_stats = await self.db_service.aggregate('companies', source_pipeline)

            # 最新更新日時
            latest_update_pipeline = [
                {'$match': {'is_active': True}},
                {'$sort': {'updated_at': -1}},
                {'$limit': 1},
                {'$project': {'updated_at': 1}}
            ]
            latest_update = await self.db_service.aggregate('companies', latest_update_pipeline)
            latest_update_time = latest_update[0]['updated_at'] if latest_update else None

            return {
                'total_companies': total_companies,
                'active_companies': active_companies,
                'inactive_companies': total_companies - active_companies,
                'industry_distribution': {item['_id']: item['count'] for item in industry_stats},
                'size_distribution': {item['_id']: item['count'] for item in size_stats},
                'source_file_distribution': {item['_id']: item['count'] for item in source_stats},
                'latest_update': latest_update_time
            }

        except Exception as e:
            logger.error(f"get_import_statistics エラー: {e}")
            return {}

    async def log_import_completion(self, import_result, source_file: str) -> None:
        """インポート完了ログの記録"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow(),
                'source_file': source_file,
                'status': import_result.status.value,
                'processed_count': import_result.processed_count,
                'error_count': import_result.error_count,
                'errors': import_result.errors[:10],  # 最大10件のエラーのみ記録
                'statistics': await self.get_import_statistics()
            }

            # ログをコレクションに保存
            await self.db_service.create('import_logs', log_entry)

            # 構造化ログ出力
            logger.info(
                f"CSV Import Completed",
                extra={
                    'source_file': source_file,
                    'status': import_result.status.value,
                    'processed_count': import_result.processed_count,
                    'error_count': import_result.error_count,
                    'success_rate': (import_result.processed_count /
                                   (import_result.processed_count + import_result.error_count) * 100
                                   if (import_result.processed_count + import_result.error_count) > 0 else 0)
                }
            )

        except Exception as e:
            logger.error(f"log_import_completion エラー: {e}")

    async def validate_data_integrity(self) -> dict:
        """データ整合性の検証"""
        try:
            validation_results = {
                'valid': True,
                'issues': []
            }

            # 企業名の重複チェック
            duplicate_names_pipeline = [
                {'$group': {'_id': '$name', 'count': {'$sum': 1}}},
                {'$match': {'count': {'$gt': 1}}}
            ]
            duplicates = await self.db_service.aggregate('companies', duplicate_names_pipeline)

            if duplicates:
                validation_results['valid'] = False
                validation_results['issues'].append({
                    'type': 'duplicate_names',
                    'count': len(duplicates),
                    'details': [item['_id'] for item in duplicates[:10]]
                })

            # 不正な業界値チェック
            invalid_industry_pipeline = [
                {'$match': {'industry': {'$nin': [item.value for item in IndustryType]}}},
                {'$group': {'_id': '$industry', 'count': {'$sum': 1}}}
            ]
            invalid_industries = await self.db_service.aggregate('companies', invalid_industry_pipeline)

            if invalid_industries:
                validation_results['valid'] = False
                validation_results['issues'].append({
                    'type': 'invalid_industries',
                    'count': len(invalid_industries),
                    'details': [item['_id'] for item in invalid_industries]
                })

            # 不正な企業規模値チェック
            invalid_size_pipeline = [
                {'$match': {'size': {'$nin': [item.value for item in CompanySize]}}},
                {'$group': {'_id': '$size', 'count': {'$sum': 1}}}
            ]
            invalid_sizes = await self.db_service.aggregate('companies', invalid_size_pipeline)

            if invalid_sizes:
                validation_results['valid'] = False
                validation_results['issues'].append({
                    'type': 'invalid_sizes',
                    'count': len(invalid_sizes),
                    'details': [item['_id'] for item in invalid_sizes]
                })

            # 設立年の範囲チェック
            current_year = datetime.now().year
            invalid_founded_year_pipeline = [
                {
                    '$match': {
                        'founded_year': {
                            '$exists': True,
                            '$not': {
                                '$gte': 1800,
                                '$lte': current_year
                            }
                        }
                    }
                },
                {'$count': 'invalid_count'}
            ]
            invalid_years = await self.db_service.aggregate('companies', invalid_founded_year_pipeline)

            if invalid_years and invalid_years[0].get('invalid_count', 0) > 0:
                validation_results['valid'] = False
                validation_results['issues'].append({
                    'type': 'invalid_founded_years',
                    'count': invalid_years[0]['invalid_count']
                })

            return validation_results

        except Exception as e:
            logger.error(f"validate_data_integrity エラー: {e}")
            return {'valid': False, 'issues': [{'type': 'validation_error', 'message': str(e)}]}
    
    async def upsert_company_from_csv(self, csv_data: dict) -> Result[Company, ValidationError]:
        """CSVデータから企業をUpsert（作成または更新）"""
        try:
            # 正規化された企業名で既存データを検索
            normalized_name = csv_data['name_normalized']
            existing_company = await self.db_service.find_one('companies', {'name': normalized_name})

            # 企業データ構築
            company_doc = {
                'name': normalized_name,
                'name_original': csv_data['name_original'],
                'industry': csv_data.get('industry', 'other'),
                'size': csv_data.get('size', 'other'),
                'country': csv_data.get('country', ''),
                'description': csv_data.get('description', ''),
                'website': csv_data.get('website', ''),
                'location': csv_data.get('location', ''),
                'founded_year': csv_data.get('founded_year'),
                'employee_count': self._get_max_employee_count(csv_data),
                'source_files': csv_data.get('source_files', []),
                'foreign_company_data': csv_data.get('foreign_company_data', {}),
                'construction_data': csv_data.get('construction_data', {}),
                'updated_at': datetime.utcnow(),
                'is_active': True
            }

            if existing_company:
                # 既存データの更新
                company_doc['created_at'] = existing_company.get('created_at', datetime.utcnow())

                # データをマージ
                merged_foreign_data = {**existing_company.get('foreign_company_data', {}), **company_doc['foreign_company_data']}
                merged_construction_data = {**existing_company.get('construction_data', {}), **company_doc['construction_data']}

                company_doc['foreign_company_data'] = merged_foreign_data
                company_doc['construction_data'] = merged_construction_data

                # 既存のソースファイルリストに追加
                existing_sources = set(existing_company.get('source_files', []))
                new_sources = set(csv_data.get('source_files', []))
                company_doc['source_files'] = list(existing_sources.union(new_sources))

                # データベース更新
                update_success = await self.db_service.update_one(
                    'companies',
                    {'_id': existing_company['_id']},
                    company_doc
                )

                if update_success:
                    # 更新された企業を取得
                    updated_company = await self.get_company(str(existing_company['_id']))
                    return Result.success(updated_company)
                else:
                    return Result.failure(ValidationError({'update': ['Failed to update company']}))

            else:
                # 新規作成
                company_doc['created_at'] = datetime.utcnow()

                # データベースに保存
                company_id = await self.db_service.create('companies', company_doc)

                # Companyオブジェクト作成
                company = Company(
                    id=str(company_id),
                    name=normalized_name,
                    industry=IndustryType(csv_data.get('industry', 'other')),
                    size=CompanySize(csv_data.get('size', 'other')),
                    country=csv_data.get('country', ''),
                    description=company_doc.get('description'),
                    website=company_doc.get('website'),
                    location=company_doc.get('location'),
                    founded_year=company_doc.get('founded_year'),
                    employee_count=company_doc.get('employee_count'),
                    created_at=company_doc['created_at'],
                    updated_at=company_doc['updated_at']
                )

                return Result.success(company)

        except Exception as e:
            logger.error(f"upsert_company_from_csv エラー: {e}")
            return Result.failure(ValidationError({'csv': [f'Failed to upsert company: {str(e)}']}))

    def _get_max_employee_count(self, csv_data: dict) -> Optional[int]:
        """CSVデータから最大従業員数を取得"""
        foreign_count = csv_data.get('foreign_company_data', {}).get('employee_count', 0)
        construction_count = csv_data.get('construction_data', {}).get('employee_count', 0)

        max_count = max(foreign_count or 0, construction_count or 0)
        return max_count if max_count > 0 else None

    def _validate_location_includes_country(self, location: str, country: str) -> bool:
        """所在地に国名情報が含まれているかを検証"""
        if not location or not country:
            return False

        location_lower = location.lower()
        country_lower = country.lower()

        # 所在地に国名が含まれている場合
        if country_lower in location_lower:
            return True

        # カンマ区切りで最後の部分が国名の場合
        parts = [part.strip().lower() for part in location.split(',')]
        if len(parts) >= 2 and parts[-1] == country_lower:
            return True

        # 日本の都市名の場合は特別扱い
        if country_lower == 'japan':
            japanese_cities = [
                '東京', '大阪', '名古屋', '横浜', '札幌', '神戸', '京都', '福岡', '広島', '仙台',
                'tokyo', 'osaka', 'nagoya', 'yokohama', 'sapporo', 'kobe', 'kyoto',
                'fukuoka', 'hiroshima', 'sendai'
            ]

            for city in japanese_cities:
                if city in location_lower:
                    return True

        return False

    def _is_valid_url(self, url: str) -> bool:
        """URL形式の検証"""
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None

    async def validate_data_integrity(self) -> Dict[str, any]:
        """データ整合性チェック"""
        try:
            validation_errors = []
            missing_required_fields = 0
            duplicate_entries = 0

            # 全企業データを取得
            companies = await self.db_service.find_many('companies', {})

            seen_names = set()
            for company in companies:
                # 必須フィールドチェック
                if not company.get('name'):
                    missing_required_fields += 1
                    validation_errors.append(f"Company missing name field: {company.get('_id')}")

                if not company.get('country'):
                    missing_required_fields += 1
                    validation_errors.append(f"Company missing country field: {company.get('name', company.get('_id'))}")

                # 重複チェック
                name = company.get('name', '').lower().strip()
                if name:
                    if name in seen_names:
                        duplicate_entries += 1
                        validation_errors.append(f"Duplicate company name: {company.get('name')}")
                    else:
                        seen_names.add(name)

                # 業界データの整合性チェック
                industry = company.get('industry')
                if industry:
                    try:
                        IndustryType(industry)
                    except ValueError:
                        validation_errors.append(f"Invalid industry type '{industry}' for company: {company.get('name')}")

                # 企業規模データの整合性チェック
                size = company.get('size')
                if size:
                    try:
                        CompanySize(size)
                    except ValueError:
                        validation_errors.append(f"Invalid company size '{size}' for company: {company.get('name')}")

            # 整合性判定
            is_valid = (
                len(validation_errors) == 0 and
                missing_required_fields == 0 and
                duplicate_entries == 0
            )

            return {
                'is_valid': is_valid,
                'validation_errors': validation_errors,
                'missing_required_fields': missing_required_fields,
                'duplicate_entries': duplicate_entries,
                'total_companies_checked': len(companies),
                'check_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
            return {
                'is_valid': False,
                'validation_errors': [f"Integrity check failed: {str(e)}"],
                'missing_required_fields': 0,
                'duplicate_entries': 0,
                'total_companies_checked': 0,
                'check_timestamp': datetime.utcnow().isoformat()
            }