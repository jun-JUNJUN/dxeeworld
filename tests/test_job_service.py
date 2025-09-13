"""
求人サービスの拡張機能テスト
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from bson import ObjectId
from src.services.job_service import JobService, ValidationError
from src.models.job import Job, JobType, ExperienceLevel
from src.utils.result import Result


class TestJobServiceAdvancedSearch:
    """高度な求人検索機能テスト"""

    @pytest.mark.asyncio
    async def test_search_jobs_by_skills(self):
        """スキルによる求人検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Python Developer',
                'company_id': str(ObjectId()),
                'company_name': 'Tech Company',
                'description': 'Python development position',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'location': 'Tokyo',
                'requirements': {
                    'required_skills': ['Python', 'Django'],
                    'preferred_skills': ['React'],
                    'experience_years': 3
                },
                'posted_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=30),
                'is_active': True
            }
        ]

        service = JobService(mock_db)

        jobs = await service.search_jobs_by_skills(['Python'], limit=10)
        assert len(jobs) == 1
        assert jobs[0]['title'] == 'Python Developer'

    @pytest.mark.asyncio
    async def test_search_jobs_by_salary_range(self):
        """給与範囲による求人検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Senior Developer',
                'company_id': str(ObjectId()),
                'company_name': 'High Paying Company',
                'salary_range': {
                    'min_amount': 8000000,
                    'max_amount': 12000000,
                    'currency': 'JPY',
                    'period': 'annual'
                },
                'posted_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=30),
                'is_active': True
            }
        ]

        service = JobService(mock_db)

        jobs = await service.search_jobs_by_salary_range(
            min_salary=7000000,
            max_salary=15000000
        )
        assert len(jobs) == 1
        assert jobs[0]['title'] == 'Senior Developer'

    @pytest.mark.asyncio
    async def test_search_jobs_with_pagination(self):
        """ページネーション付き求人検索テスト"""
        mock_db = AsyncMock()
        mock_db.find_paginated.return_value = {
            'items': [
                {
                    '_id': str(ObjectId()),
                    'title': f'Job {i}',
                    'company_name': f'Company {i}'
                } for i in range(5)
            ],
            'page': 1,
            'page_size': 5,
            'total_count': 20,
            'total_pages': 4
        }

        service = JobService(mock_db)

        result = await service.search_jobs_paginated(
            filters={'location': 'Tokyo'},
            page=1,
            page_size=5
        )

        assert len(result['items']) == 5
        assert result['total_count'] == 20
        assert result['total_pages'] == 4

    @pytest.mark.asyncio
    async def test_search_jobs_by_text(self):
        """テキスト検索による求人検索テスト"""
        mock_db = AsyncMock()
        mock_db.aggregate.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Full Stack Developer',
                'company_name': 'Software Company',
                'description': 'Full stack development using React and Node.js',
                'score': 2.5
            }
        ]

        service = JobService(mock_db)

        jobs = await service.search_jobs_by_text('full stack developer')
        assert len(jobs) == 1
        assert jobs[0]['title'] == 'Full Stack Developer'


class TestJobServiceStatistics:
    """求人統計機能テスト"""

    @pytest.mark.asyncio
    async def test_get_job_statistics_by_company(self):
        """企業別求人統計テスト"""
        company_id = str(ObjectId())

        mock_db = AsyncMock()
        mock_db.aggregate.return_value = [
            {
                '_id': None,
                'total_jobs': 15,
                'active_jobs': 12,
                'avg_salary': 8500000,
                'top_skills': ['Python', 'JavaScript', 'React']
            }
        ]

        service = JobService(mock_db)

        stats = await service.get_job_statistics_by_company(company_id)
        assert stats['total_jobs'] == 15
        assert stats['active_jobs'] == 12
        assert 'Python' in stats['top_skills']

    @pytest.mark.asyncio
    async def test_get_trending_skills(self):
        """トレンドスキル統計テスト"""
        mock_db = AsyncMock()
        mock_db.aggregate.return_value = [
            {'_id': 'Python', 'count': 25},
            {'_id': 'JavaScript', 'count': 20},
            {'_id': 'React', 'count': 18}
        ]

        service = JobService(mock_db)

        trending_skills = await service.get_trending_skills(limit=5)
        assert len(trending_skills) == 3
        assert trending_skills[0]['_id'] == 'Python'
        assert trending_skills[0]['count'] == 25

    @pytest.mark.asyncio
    async def test_get_salary_statistics(self):
        """給与統計テスト"""
        mock_db = AsyncMock()
        mock_db.aggregate.return_value = [
            {
                '_id': None,
                'avg_min_salary': 5500000,
                'avg_max_salary': 8500000,
                'median_salary': 7000000,
                'salary_distribution': {
                    '3000000-5000000': 15,
                    '5000000-8000000': 35,
                    '8000000-12000000': 25,
                    '12000000+': 10
                }
            }
        ]

        service = JobService(mock_db)

        stats = await service.get_salary_statistics()
        assert stats['avg_min_salary'] == 5500000
        assert stats['avg_max_salary'] == 8500000
        assert stats['salary_distribution']['5000000-8000000'] == 35


class TestJobServiceBulkOperations:
    """求人一括操作テスト"""

    @pytest.mark.asyncio
    async def test_bulk_create_jobs(self):
        """複数求人の一括作成テスト"""
        mock_db = AsyncMock()
        mock_db.bulk_insert.return_value = ['id1', 'id2', 'id3']

        service = JobService(mock_db)

        jobs_data = [
            {
                'title': 'Developer 1',
                'company_id': str(ObjectId()),
                'company_name': 'Company 1',
                'description': 'Development position at company 1 with exciting opportunities',
                'job_type': 'full_time',
                'experience_level': 'junior',
                'location': 'Tokyo',
                'posted_by': str(ObjectId())
            },
            {
                'title': 'Developer 2',
                'company_id': str(ObjectId()),
                'company_name': 'Company 2',
                'description': 'Development position at company 2 with great benefits package',
                'job_type': 'contract',
                'experience_level': 'mid',
                'location': 'Osaka',
                'posted_by': str(ObjectId())
            }
        ]

        result = await service.bulk_create_jobs(jobs_data)
        assert result.is_success
        assert len(result.data) == 2

    @pytest.mark.asyncio
    async def test_bulk_update_job_status(self):
        """複数求人の状態一括更新テスト"""
        mock_db = AsyncMock()
        mock_db.bulk_update.return_value = 3

        service = JobService(mock_db)

        job_ids = ['id1', 'id2', 'id3']
        result = await service.bulk_update_job_status(job_ids, is_active=False)
        assert result == 3

    @pytest.mark.asyncio
    async def test_bulk_extend_job_expiry(self):
        """複数求人の有効期限一括延長テスト"""
        mock_db = AsyncMock()
        mock_db.bulk_update.return_value = 2

        service = JobService(mock_db)

        job_ids = ['id1', 'id2']
        extension_days = 30

        result = await service.bulk_extend_job_expiry(job_ids, extension_days)
        assert result == 2


class TestJobServiceIndexing:
    """求人検索インデックス機能テスト"""

    @pytest.mark.asyncio
    async def test_create_job_indexes(self):
        """求人コレクションのインデックス作成テスト"""
        mock_db = AsyncMock()
        mock_db.create_index.return_value = "index_name"

        service = JobService(mock_db)

        result = await service.create_job_indexes()
        assert result is True

        # インデックス作成が複数回呼ばれることを確認
        assert mock_db.create_index.call_count >= 5


class TestJobServiceExpiredJobs:
    """期限切れ求人管理テスト"""

    @pytest.mark.asyncio
    async def test_get_expired_jobs(self):
        """期限切れ求人取得テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Expired Job',
                'expires_at': datetime.utcnow() - timedelta(days=5),
                'is_active': True
            }
        ]

        service = JobService(mock_db)

        expired_jobs = await service.get_expired_jobs()
        assert len(expired_jobs) == 1
        assert expired_jobs[0]['title'] == 'Expired Job'

    @pytest.mark.asyncio
    async def test_deactivate_expired_jobs(self):
        """期限切れ求人の自動非アクティブ化テスト"""
        mock_db = AsyncMock()
        mock_db.bulk_update.return_value = 5

        service = JobService(mock_db)

        result = await service.deactivate_expired_jobs()
        assert result == 5

    @pytest.mark.asyncio
    async def test_send_expiry_notifications(self):
        """有効期限通知送信テスト"""
        mock_db = AsyncMock()
        mock_db.find_many.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Job Expiring Soon',
                'posted_by': str(ObjectId()),
                'expires_at': datetime.utcnow() + timedelta(days=2)
            }
        ]

        service = JobService(mock_db)

        jobs_to_notify = await service.get_jobs_expiring_soon(days_before=3)
        assert len(jobs_to_notify) == 1
        assert jobs_to_notify[0]['title'] == 'Job Expiring Soon'


class TestJobServiceRecommendations:
    """求人推薦機能テスト"""

    @pytest.mark.asyncio
    async def test_recommend_jobs_for_user(self):
        """ユーザー向け求人推薦テスト"""
        user_id = str(ObjectId())

        mock_db = AsyncMock()
        # ユーザープロファイル取得のモック
        mock_db.find_one.return_value = {
            '_id': user_id,
            'profile': {
                'skills': ['Python', 'Django'],
                'experience_years': 3,
                'location': 'Tokyo'
            }
        }

        # 推薦求人のモック
        mock_db.aggregate.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Python Developer',
                'company_name': 'Matching Company',
                'requirements': {
                    'required_skills': ['Python'],
                    'experience_years': 2
                },
                'match_score': 0.85
            }
        ]

        service = JobService(mock_db)

        recommendations = await service.recommend_jobs_for_user(user_id, limit=5)
        assert len(recommendations) == 1
        assert recommendations[0]['match_score'] == 0.85

    @pytest.mark.asyncio
    async def test_similar_jobs(self):
        """類似求人検索テスト"""
        job_id = str(ObjectId())

        mock_db = AsyncMock()
        # 基準求人取得のモック
        mock_db.find_one.return_value = {
            '_id': job_id,
            'title': 'Python Developer',
            'job_type': 'full_time',
            'requirements': {
                'required_skills': ['Python', 'Django']
            },
            'location': 'Tokyo'
        }

        # 類似求人のモック
        mock_db.aggregate.return_value = [
            {
                '_id': str(ObjectId()),
                'title': 'Backend Developer',
                'requirements': {
                    'required_skills': ['Python', 'Flask']
                },
                'similarity_score': 0.75
            }
        ]

        service = JobService(mock_db)

        similar_jobs = await service.get_similar_jobs(job_id, limit=5)
        assert len(similar_jobs) == 1
        assert similar_jobs[0]['similarity_score'] == 0.75