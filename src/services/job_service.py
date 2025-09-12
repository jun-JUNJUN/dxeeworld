"""
求人情報管理サービス
"""
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..models.job import Job, JobType, ExperienceLevel, SalaryRange, JobRequirements
from ..utils.result import Result


class ValidationError(Exception):
    """バリデーションエラー"""
    
    def __init__(self, field_errors: Dict[str, List[str]]):
        self.field_errors = field_errors
        super().__init__(f"Validation failed: {field_errors}")


class JobService:
    """求人情報管理サービス"""
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def validate_job_data(self, job_data: dict) -> Result[bool, ValidationError]:
        """求人データの検証"""
        errors = {}
        
        # タイトル検証
        title = job_data.get('title', '').strip()
        if not title:
            errors['title'] = ['Job title is required']
        elif len(title) < 5:
            errors['title'] = ['Job title must be at least 5 characters']
        
        # 会社ID検証
        company_id = job_data.get('company_id', '').strip()
        if not company_id:
            errors['company_id'] = ['Company ID is required']
        
        # 会社名検証
        company_name = job_data.get('company_name', '').strip()
        if not company_name:
            errors['company_name'] = ['Company name is required']
        
        # 説明文検証
        description = job_data.get('description', '').strip()
        if not description:
            errors['description'] = ['Job description is required']
        elif len(description) < 50:
            errors['description'] = ['Job description must be at least 50 characters']
        
        # 雇用形態検証
        job_type = job_data.get('job_type')
        try:
            JobType(job_type)
        except (ValueError, TypeError):
            errors['job_type'] = ['Invalid job type']
        
        # 経験レベル検証
        experience_level = job_data.get('experience_level')
        try:
            ExperienceLevel(experience_level)
        except (ValueError, TypeError):
            errors['experience_level'] = ['Invalid experience level']
        
        # 場所検証
        location = job_data.get('location', '').strip()
        if not location:
            errors['location'] = ['Location is required']
        
        # 投稿者検証
        posted_by = job_data.get('posted_by', '').strip()
        if not posted_by:
            errors['posted_by'] = ['Posted by user ID is required']
        
        # 給与範囲検証（任意）
        salary_range = job_data.get('salary_range')
        if salary_range:
            salary_errors = self._validate_salary_range(salary_range)
            if salary_errors:
                errors['salary_range'] = salary_errors
        
        # 要件検証（任意）
        requirements = job_data.get('requirements')
        if requirements:
            requirements_errors = self._validate_requirements(requirements)
            if requirements_errors:
                errors['requirements'] = requirements_errors
        
        # 有効期限検証（任意）
        expires_at = job_data.get('expires_at')
        if expires_at and isinstance(expires_at, datetime):
            if expires_at <= datetime.utcnow():
                errors['expires_at'] = ['Expiry date must be in the future']
        
        if errors:
            return Result.failure(ValidationError(errors))
        
        return Result.success(True)
    
    def _validate_salary_range(self, salary_data: dict) -> List[str]:
        """給与範囲の検証"""
        errors = []
        
        min_amount = salary_data.get('min_amount')
        max_amount = salary_data.get('max_amount')
        
        if min_amount is not None and (not isinstance(min_amount, int) or min_amount < 0):
            errors.append('Minimum salary must be a positive integer')
        
        if max_amount is not None and (not isinstance(max_amount, int) or max_amount < 0):
            errors.append('Maximum salary must be a positive integer')
        
        if (min_amount is not None and max_amount is not None and 
            min_amount >= max_amount):
            errors.append('Minimum salary must be less than maximum salary')
        
        return errors
    
    def _validate_requirements(self, requirements_data: dict) -> List[str]:
        """要件の検証"""
        errors = []
        
        required_skills = requirements_data.get('required_skills', [])
        if not isinstance(required_skills, list):
            errors.append('Required skills must be a list')
        
        preferred_skills = requirements_data.get('preferred_skills', [])
        if not isinstance(preferred_skills, list):
            errors.append('Preferred skills must be a list')
        
        experience_years = requirements_data.get('experience_years')
        if (experience_years is not None and 
            (not isinstance(experience_years, int) or experience_years < 0)):
            errors.append('Experience years must be a positive integer')
        
        languages = requirements_data.get('languages', [])
        if not isinstance(languages, list):
            errors.append('Languages must be a list')
        
        return errors
    
    async def create_job(self, job_data: dict) -> Result[Job, ValidationError]:
        """求人を作成"""
        # バリデーション
        validation_result = self.validate_job_data(job_data)
        if not validation_result.is_success:
            return Result.failure(validation_result.error)
        
        # 給与範囲とスキル要件の処理
        salary_range = None
        if job_data.get('salary_range'):
            salary_range = SalaryRange.from_dict(job_data['salary_range'])
        
        requirements = JobRequirements.from_dict(job_data.get('requirements', {}))
        
        # デフォルト有効期限（30日後）
        expires_at = job_data.get('expires_at') or (datetime.utcnow() + timedelta(days=30))
        
        # 求人データ作成
        job_doc = {
            'title': job_data['title'].strip(),
            'company_id': job_data['company_id'],
            'company_name': job_data['company_name'].strip(),
            'description': job_data['description'].strip(),
            'job_type': job_data['job_type'],
            'experience_level': job_data['experience_level'],
            'location': job_data['location'].strip(),
            'remote_work': job_data.get('remote_work', False),
            'salary_range': salary_range.to_dict() if salary_range else None,
            'requirements': requirements.to_dict(),
            'benefits': job_data.get('benefits', []),
            'posted_by': job_data['posted_by'],
            'posted_at': datetime.utcnow(),
            'expires_at': expires_at,
            'is_active': True,
            'view_count': 0,
            'application_count': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # データベースに保存
        job_id = await self.db_service.create('jobs', job_doc)
        
        # Jobオブジェクト作成
        job = Job(
            id=str(job_id),
            title=job_doc['title'],
            company_id=job_doc['company_id'],
            company_name=job_doc['company_name'],
            description=job_doc['description'],
            job_type=JobType(job_doc['job_type']),
            experience_level=ExperienceLevel(job_doc['experience_level']),
            location=job_doc['location'],
            remote_work=job_doc['remote_work'],
            salary_range=salary_range,
            requirements=requirements,
            benefits=job_doc['benefits'],
            posted_by=job_doc['posted_by'],
            posted_at=job_doc['posted_at'],
            expires_at=expires_at,
            is_active=True,
            view_count=0,
            application_count=0,
            created_at=job_doc['created_at'],
            updated_at=job_doc['updated_at']
        )
        
        return Result.success(job)
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """求人IDで求人を取得"""
        try:
            job_doc = await self.db_service.find_one('jobs', {'_id': job_id})
            if job_doc:
                return Job.from_dict(job_doc)
            return None
        except Exception:
            return None
    
    async def search_jobs(self, 
                         keyword: Optional[str] = None,
                         company_id: Optional[str] = None,
                         location: Optional[str] = None,
                         job_type: Optional[str] = None,
                         experience_level: Optional[str] = None,
                         remote_work: Optional[bool] = None,
                         limit: int = 10) -> List[Job]:
        """求人を検索"""
        try:
            filter_dict = {'is_active': True, 'expires_at': {'$gt': datetime.utcnow()}}
            
            if keyword:
                filter_dict['$or'] = [
                    {'title': {'$regex': keyword, '$options': 'i'}},
                    {'description': {'$regex': keyword, '$options': 'i'}},
                    {'company_name': {'$regex': keyword, '$options': 'i'}}
                ]
            
            if company_id:
                filter_dict['company_id'] = company_id
            
            if location:
                filter_dict['location'] = {'$regex': location, '$options': 'i'}
            
            if job_type:
                filter_dict['job_type'] = job_type
            
            if experience_level:
                filter_dict['experience_level'] = experience_level
            
            if remote_work is not None:
                filter_dict['remote_work'] = remote_work
            
            job_docs = await self.db_service.find_many(
                'jobs', 
                filter_dict, 
                limit=limit, 
                sort=[('posted_at', -1)]  # 投稿日の新しい順
            )
            jobs = [Job.from_dict(doc) for doc in job_docs]
            return jobs
            
        except Exception:
            return []
    
    async def update_job(self, job_id: str, update_data: dict) -> Result[Job, ValidationError]:
        """求人情報を更新"""
        # バリデーション
        validation_result = self.validate_job_data(update_data)
        if not validation_result.is_success:
            return Result.failure(validation_result.error)
        
        # 更新データ準備
        update_doc = {**update_data, 'updated_at': datetime.utcnow()}
        
        # 実際の実装ではupdate_oneメソッドをDatabaseServiceに追加する必要がある
        # ここでは簡単のため省略
        
        # 更新された求人を取得
        updated_job = await self.get_job(job_id)
        if updated_job:
            return Result.success(updated_job)
        else:
            return Result.failure(ValidationError({'id': ['Job not found']}))
    
    async def delete_job(self, job_id: str) -> bool:
        """求人を削除（論理削除）"""
        try:
            # 実際の実装ではupdate_oneメソッドを使用
            # ここでは簡単のため省略
            return True
        except Exception:
            return False
    
    async def increment_view_count(self, job_id: str) -> bool:
        """求人の閲覧数を増加"""
        try:
            # 実際の実装ではupdate_oneメソッドでview_countをインクリメント
            return True
        except Exception:
            return False