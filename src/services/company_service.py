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
            company_doc = await self.db_service.find_one('companies', {'_id': company_id})
            if company_doc:
                return Company.from_dict(company_doc)
            return None
        except Exception:
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

            # テキスト検索インデックス
            await self.db_service.create_index(
                'companies',
                [('name', 'text'), ('description', 'text')]
            )

            # 複合インデックス（業界 + 企業規模）
            await self.db_service.create_index(
                'companies',
                [('industry', 1), ('size', 1)]
            )

            return True

        except Exception as e:
            logger.error(f"インデックス作成エラー: {e}")
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
    
    def _is_valid_url(self, url: str) -> bool:
        """URL形式の検証"""
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None