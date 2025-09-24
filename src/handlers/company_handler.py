"""
企業一覧表示ハンドラー
"""
import logging
from typing import Optional
from tornado.web import HTTPError
from .base_handler import BaseHandler
from ..services.company_service import CompanyService
from ..services.job_service import JobService
from ..database import get_db_service

logger = logging.getLogger(__name__)


class CompanyListHandler(BaseHandler):
    """企業一覧表示ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.db_service = get_db_service()
        self.company_service = CompanyService(self.db_service)

    async def get(self):
        """企業一覧ページ表示"""
        try:
            # ページネーション設定
            page = int(self.get_query_argument('page', '1'))
            page_size = 30  # 要件に従って30社/ページ
            skip = (page - 1) * page_size

            # フィルター条件の取得
            industry = self.get_query_argument('industry', None)
            size = self.get_query_argument('size', None)
            location = self.get_query_argument('location', None)
            founded_year_min = self.get_query_argument('founded_year_min', None)
            founded_year_max = self.get_query_argument('founded_year_max', None)
            employee_count_min = self.get_query_argument('employee_count_min', None)
            employee_count_max = self.get_query_argument('employee_count_max', None)

            # フィルター条件を辞書にまとめる
            filters = self._build_filter_dict(
                industry=industry,
                size=size,
                location=location,
                founded_year_min=founded_year_min,
                founded_year_max=founded_year_max,
                employee_count_min=employee_count_min,
                employee_count_max=employee_count_max
            )

            # 企業データの取得
            company_objects = await self.company_service.search_companies_with_pagination(
                filters, skip, page_size, sort=[('name', 1)]
            )

            # Company オブジェクトを表示用辞書に変換
            companies = []
            for company in company_objects:
                try:
                    # Companyオブジェクトの場合
                    industry_value = company.industry.value
                    size_value = company.size.value

                    company_dict = {
                        'id': company.id,
                        'name': company.name,
                        'industry': industry_value,
                        'industry_label': self._get_industry_label(industry_value),
                        'size': size_value,
                        'size_label': self._get_size_label(size_value),
                        'country': company.country,
                        'location': company.location,
                        'founded_year': company.founded_year,
                        'employee_count': company.employee_count,
                        'description': company.description,
                        'website': company.website,
                    }
                    companies.append(company_dict)
                except Exception as e:
                    logger.error(f"Error processing company {getattr(company, 'name', 'unknown')}: {e}")
                    continue

            # 総数の取得（ページネーション用）
            total_companies = await self.company_service.count_companies_with_filters(filters)

            # ページネーション情報の計算
            total_pages = (total_companies + page_size - 1) // page_size
            has_previous = page > 1
            has_next = page < total_pages

            # フィルター選択肢の取得
            filter_options = await self._get_filter_options()

            # テンプレートに渡すデータ
            template_data = {
                'companies': companies,
                'current_page': page,
                'total_pages': total_pages,
                'total_companies': total_companies,
                'has_previous': has_previous,
                'has_next': has_next,
                'previous_page': page - 1 if has_previous else None,
                'next_page': page + 1 if has_next else None,
                'filters': {
                    'industry': industry,
                    'size': size,
                    'location': location,
                    'founded_year_min': founded_year_min,
                    'founded_year_max': founded_year_max,
                    'employee_count_min': employee_count_min,
                    'employee_count_max': employee_count_max,
                },
                'filter_options': filter_options,
                'page_title': '企業一覧',
            }

            self.render('companies/list.html', **template_data)

        except ValueError as e:
            logger.error(f"Invalid parameter error: {e}")
            raise HTTPError(400, "無効なパラメータが指定されました")
        except Exception as e:
            import traceback
            logger.error(f"Company list display error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPError(500, "企業一覧の表示でエラーが発生しました")

    def _build_filter_dict(self, **kwargs) -> dict:
        """フィルター条件辞書を構築"""
        filters = {'is_active': True}  # アクティブな企業のみ

        # 業界フィルター
        if kwargs.get('industry'):
            filters['industry'] = kwargs['industry']

        # 企業規模フィルター
        if kwargs.get('size'):
            filters['size'] = kwargs['size']

        # 所在地フィルター（部分一致）
        if kwargs.get('location'):
            filters['location'] = {'$regex': kwargs['location'], '$options': 'i'}

        # 設立年範囲フィルター
        founded_year_filter = {}
        if kwargs.get('founded_year_min'):
            try:
                founded_year_filter['$gte'] = int(kwargs['founded_year_min'])
            except ValueError:
                pass
        if kwargs.get('founded_year_max'):
            try:
                founded_year_filter['$lte'] = int(kwargs['founded_year_max'])
            except ValueError:
                pass
        if founded_year_filter:
            filters['founded_year'] = founded_year_filter

        # 従業員数範囲フィルター
        employee_count_filter = {}
        if kwargs.get('employee_count_min'):
            try:
                employee_count_filter['$gte'] = int(kwargs['employee_count_min'])
            except ValueError:
                pass
        if kwargs.get('employee_count_max'):
            try:
                employee_count_filter['$lte'] = int(kwargs['employee_count_max'])
            except ValueError:
                pass
        if employee_count_filter:
            filters['employee_count'] = employee_count_filter

        return filters


    async def _get_filter_options(self) -> dict:
        """フィルター選択肢を取得"""
        try:
            # 業界一覧
            industry_pipeline = [
                {'$match': {'is_active': True}},
                {'$group': {'_id': '$industry', 'count': {'$sum': 1}}},
                {'$sort': {'_id': 1}}
            ]
            industry_results = await self.db_service.aggregate('companies', industry_pipeline)
            industries = [
                {'value': item['_id'], 'label': self._get_industry_label(item['_id']), 'count': item['count']}
                for item in industry_results if item['_id']
            ]

            # 企業規模一覧
            size_pipeline = [
                {'$match': {'is_active': True}},
                {'$group': {'_id': '$size', 'count': {'$sum': 1}}},
                {'$sort': {'_id': 1}}
            ]
            size_results = await self.db_service.aggregate('companies', size_pipeline)
            sizes = [
                {'value': item['_id'], 'label': self._get_size_label(item['_id']), 'count': item['count']}
                for item in size_results if item['_id']
            ]

            # 所在地一覧（トップ20）
            location_pipeline = [
                {'$match': {'is_active': True, 'location': {'$ne': None, '$ne': ''}}},
                {'$group': {'_id': '$location', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 20}
            ]
            location_results = await self.db_service.aggregate('companies', location_pipeline)
            locations = [
                {'value': item['_id'], 'label': item['_id'], 'count': item['count']}
                for item in location_results
            ]

            return {
                'industries': industries,
                'sizes': sizes,
                'locations': locations
            }

        except Exception as e:
            logger.error(f"Failed to get filter options: {e}")
            return {'industries': [], 'sizes': [], 'locations': []}


    def _get_industry_label(self, industry_value: str) -> str:
        """業界値から表示ラベルを取得"""
        industry_labels = {
            'technology': 'テクノロジー',
            'finance': '金融',
            'healthcare': 'ヘルスケア',
            'education': '教育',
            'retail': '小売',
            'manufacturing': '製造業',
            'consulting': 'コンサルティング',
            'media': 'メディア',
            'real_estate': '不動産',
            'construction': '建設業',
            'other': 'その他'
        }
        return industry_labels.get(industry_value, industry_value)

    def _get_size_label(self, size_value: str) -> str:
        """企業規模値から表示ラベルを取得"""
        size_labels = {
            'startup': 'スタートアップ (1-10名)',
            'small': '小企業 (11-50名)',
            'medium': '中企業 (51-200名)',
            'large': '大企業 (201-1000名)',
            'enterprise': '大企業 (1000名以上)',
            'other': 'その他'
        }
        return size_labels.get(size_value, size_value)


class JobsListHandler(BaseHandler):
    """全求人一覧表示ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.db_service = get_db_service()
        self.company_service = CompanyService(self.db_service)
        self.job_service = JobService(self.db_service)

    async def get(self):
        """全求人一覧ページ表示"""
        try:
            # ページネーション設定
            page = int(self.get_query_argument('page', '1'))
            page_size = 20  # 1ページあたり20件の求人
            skip = (page - 1) * page_size

            # 検索条件の取得
            keyword = self.get_query_argument('keyword', None)
            company_id = self.get_query_argument('company_id', None)
            location = self.get_query_argument('location', None)
            job_type = self.get_query_argument('job_type', None)
            experience_level = self.get_query_argument('experience_level', None)
            remote_work = self.get_query_argument('remote_work', None)

            # 検索条件を辞書にまとめる
            filters = {}
            if keyword:
                filters['keyword'] = keyword
            if company_id:
                filters['company_id'] = company_id
            if location:
                filters['location'] = location
            if job_type:
                filters['job_type'] = job_type
            if experience_level:
                filters['experience_level'] = experience_level
            if remote_work:
                filters['remote_work'] = remote_work.lower() == 'true'

            # 求人データの取得
            all_jobs = await self.job_service.search_jobs_paginated(
                filters=filters if filters else None,
                page=page,
                page_size=page_size
            )

            # 求人情報を表示用に変換
            jobs_data = []
            for job in all_jobs.get('items', []):
                jobs_data.append({
                    'id': job.id,
                    'title': job.title,
                    'company_name': job.company_name,
                    'job_type': job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                    'experience_level': job.experience_level.value if hasattr(job.experience_level, 'value') else str(job.experience_level),
                    'location': job.location,
                    'remote_work': job.remote_work,
                    'salary_range': job.salary_range.to_dict() if job.salary_range else None,
                    'posted_at': job.posted_at.isoformat() if job.posted_at else None,
                    'expires_at': job.expires_at.isoformat() if job.expires_at else None,
                    'description': job.description[:150] + '...' if job.description and len(job.description) > 150 else job.description,
                })

            # ページネーション情報の計算
            total_jobs = all_jobs.get('total_count', 0)
            total_pages = (total_jobs + page_size - 1) // page_size
            has_previous = page > 1
            has_next = page < total_pages

            template_data = {
                'jobs': jobs_data,
                'current_page': page,
                'total_pages': total_pages,
                'total_jobs': total_jobs,
                'has_previous': has_previous,
                'has_next': has_next,
                'previous_page': page - 1 if has_previous else None,
                'next_page': page + 1 if has_next else None,
                'filters': filters,
                'page_title': '求人情報一覧',
            }

            self.render('jobs/list.html', **template_data)

        except ValueError as e:
            logger.error(f"Invalid parameter error: {e}")
            raise HTTPError(400, "無効なパラメータが指定されました")
        except Exception as e:
            import traceback
            logger.error(f"Jobs list display error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPError(500, "求人一覧の表示でエラーが発生しました")

    def _get_size_label(self, size_value: str) -> str:
        """企業規模値から表示ラベルを取得"""
        size_labels = {
            'startup': 'スタートアップ (1-10名)',
            'small': '小企業 (11-50名)',
            'medium': '中企業 (51-200名)',
            'large': '大企業 (201-1000名)',
            'enterprise': '大企業 (1000名以上)',
            'other': 'その他'
        }
        return size_labels.get(size_value, size_value)


class CompanyJobsHandler(BaseHandler):
    """企業別求人一覧表示ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.db_service = get_db_service()
        self.company_service = CompanyService(self.db_service)
        self.job_service = JobService(self.db_service)

    async def get(self, company_id: str):
        """企業別求人一覧ページ表示"""
        try:
            # 企業データの取得
            company = await self.company_service.get_company(company_id)

            if not company:
                raise HTTPError(404, "企業が見つかりません")

            # ページネーション設定
            page = int(self.get_query_argument('page', '1'))
            page_size = 10  # 1ページあたり10件の求人
            skip = (page - 1) * page_size

            # 該当企業の全求人情報を取得
            all_jobs = await self.job_service.search_jobs_paginated(
                filters={'company_id': company_id},
                page=page,
                page_size=page_size
            )

            # 求人情報を表示用に変換
            jobs_data = []
            for job in all_jobs.get('items', []):
                jobs_data.append({
                    'id': job.id,
                    'title': job.title,
                    'job_type': job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                    'experience_level': job.experience_level.value if hasattr(job.experience_level, 'value') else str(job.experience_level),
                    'location': job.location,
                    'remote_work': job.remote_work,
                    'salary_range': job.salary_range.to_dict() if job.salary_range else None,
                    'posted_at': job.posted_at.isoformat() if job.posted_at else None,
                    'expires_at': job.expires_at.isoformat() if job.expires_at else None,
                    'description': job.description[:200] + '...' if job.description and len(job.description) > 200 else job.description,
                })

            # ページネーション情報の計算
            total_jobs = all_jobs.get('total_count', 0)
            total_pages = (total_jobs + page_size - 1) // page_size
            has_previous = page > 1
            has_next = page < total_pages

            template_data = {
                'company': {
                    'id': company.id,
                    'name': company.name,
                    'industry': company.industry.value,
                    'industry_label': self._get_industry_label(company.industry.value),
                },
                'jobs': jobs_data,
                'current_page': page,
                'total_pages': total_pages,
                'total_jobs': total_jobs,
                'has_previous': has_previous,
                'has_next': has_next,
                'previous_page': page - 1 if has_previous else None,
                'next_page': page + 1 if has_next else None,
                'page_title': f'{company.name} - 求人情報',
            }

            self.render('companies/jobs.html', **template_data)

        except HTTPError:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Company jobs display error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPError(500, "求人情報の表示でエラーが発生しました")

    def _get_industry_label(self, industry_value: str) -> str:
        """業界値から表示ラベルを取得"""
        industry_labels = {
            'technology': 'テクノロジー',
            'finance': '金融',
            'healthcare': 'ヘルスケア',
            'education': '教育',
            'retail': '小売',
            'manufacturing': '製造業',
            'consulting': 'コンサルティング',
            'media': 'メディア',
            'real_estate': '不動産',
            'construction': '建設業',
            'other': 'その他'
        }
        return industry_labels.get(industry_value, industry_value)


class CompanyDetailHandler(BaseHandler):
    """企業詳細表示ハンドラー"""

    def initialize(self):
        """ハンドラー初期化"""
        self.db_service = get_db_service()
        self.company_service = CompanyService(self.db_service)
        self.job_service = JobService(self.db_service)

    async def get(self, company_id: str):
        """企業詳細ページ表示"""
        try:
            # 企業データの取得
            company = await self.company_service.get_company(company_id)

            if not company:
                raise HTTPError(404, "企業が見つかりません")

            # 企業詳細表示用データの準備
            company_data = {
                'id': company.id,
                'name': company.name,
                'industry': company.industry.value,
                'industry_label': self._get_industry_label(company.industry.value),
                'size': company.size.value,
                'size_label': self._get_size_label(company.size.value),
                'country': company.country,
                'location': company.location,
                'founded_year': company.founded_year,
                'employee_count': company.employee_count,
                'description': company.description,
                'website': company.website,
                'foreign_company_data': company.foreign_company_data or {},
                'construction_data': company.construction_data or {},
                'source_files': company.source_files or [],
            }

            # 関連求人情報を取得（最大3件）
            related_jobs = await self.job_service.search_jobs(
                company_id=company_id,
                limit=3
            )

            # 求人情報を表示用に変換
            jobs_data = []
            for job in related_jobs:
                jobs_data.append({
                    'id': job.id,
                    'title': job.title,
                    'job_type': job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                    'experience_level': job.experience_level.value if hasattr(job.experience_level, 'value') else str(job.experience_level),
                    'location': job.location,
                    'remote_work': job.remote_work,
                    'salary_range': job.salary_range.to_dict() if job.salary_range else None,
                    'posted_at': job.posted_at.isoformat() if job.posted_at else None,
                    'expires_at': job.expires_at.isoformat() if job.expires_at else None,
                })

            # 追加求人情報へのリンク用URL
            jobs_url = f"/companies/{company_id}/jobs"

            template_data = {
                'company': company_data,
                'related_jobs': jobs_data,
                'jobs_url': jobs_url,
                'page_title': f'{company_data["name"]} - 企業詳細',
            }

            self.render('companies/detail.html', **template_data)

        except HTTPError:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Company detail display error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPError(500, "企業詳細の表示でエラーが発生しました")

    def _get_industry_label(self, industry_value: str) -> str:
        """業界値から表示ラベルを取得"""
        industry_labels = {
            'technology': 'テクノロジー',
            'finance': '金融',
            'healthcare': 'ヘルスケア',
            'education': '教育',
            'retail': '小売',
            'manufacturing': '製造業',
            'consulting': 'コンサルティング',
            'media': 'メディア',
            'real_estate': '不動産',
            'construction': '建設業',
            'other': 'その他'
        }
        return industry_labels.get(industry_value, industry_value)

    def _get_size_label(self, size_value: str) -> str:
        """企業規模値から表示ラベルを取得"""
        size_labels = {
            'startup': 'スタートアップ (1-10名)',
            'small': '小企業 (11-50名)',
            'medium': '中企業 (51-200名)',
            'large': '大企業 (201-1000名)',
            'enterprise': '大企業 (1000名以上)',
            'other': 'その他'
        }
        return size_labels.get(size_value, size_value)
