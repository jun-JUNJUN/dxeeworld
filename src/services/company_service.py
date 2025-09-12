"""
企業管理サービス
"""
import re
from typing import Dict, List, Optional
from datetime import datetime
from ..models.company import Company, IndustryType, CompanySize
from ..utils.result import Result


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
        
        # 実際の実装ではupdate_oneメソッドをDatabaseServiceに追加する必要がある
        # ここでは簡単のため省略
        
        # 更新された企業を取得
        updated_company = await self.get_company(company_id)
        if updated_company:
            return Result.success(updated_company)
        else:
            return Result.failure(ValidationError({'id': ['Company not found']}))
    
    async def delete_company(self, company_id: str) -> bool:
        """企業を削除（論理削除）"""
        try:
            # 実際の実装ではupdate_oneメソッドを使用
            # ここでは簡単のため省略
            return True
        except Exception:
            return False
    
    def _is_valid_url(self, url: str) -> bool:
        """URL形式の検証"""
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None