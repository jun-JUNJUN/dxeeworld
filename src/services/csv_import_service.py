"""
CSVインポートサービス
"""
import os
import re
import logging
import pandas as pd
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ImportStatus(Enum):
    """インポート状態"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ImportResult:
    """インポート結果"""
    status: ImportStatus
    processed_count: int
    error_count: int
    errors: List[str]


class CSVImportService:
    """CSVインポートサービス"""

    def __init__(self, db_service, company_service):
        self.db_service = db_service
        self.company_service = company_service

    async def import_foreign_companies_csv(self, file_path: str) -> ImportResult:
        """外資系企業CSVファイルのインポート"""
        try:
            # ファイル存在チェック
            if not os.path.exists(file_path):
                return ImportResult(
                    status=ImportStatus.FAILED,
                    processed_count=0,
                    error_count=1,
                    errors=[f"CSV file not found: {file_path}"]
                )

            # CSVファイル読み込み
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                return ImportResult(
                    status=ImportStatus.FAILED,
                    processed_count=0,
                    error_count=1,
                    errors=[f"Failed to read CSV file: {str(e)}"]
                )

            # データクリーニング
            cleaned_data = self.clean_foreign_companies_data(df)

            # データベースへの挿入
            processed_count = 0
            error_count = 0
            errors = []

            for company_data in cleaned_data:
                try:
                    await self.company_service.upsert_company_from_csv(company_data)
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Failed to import {company_data.get('name_original', 'unknown')}: {str(e)}")

            # 結果判定
            if error_count == 0:
                status = ImportStatus.SUCCESS
            elif processed_count > 0:
                status = ImportStatus.PARTIAL
            else:
                status = ImportStatus.FAILED

            result = ImportResult(
                status=status,
                processed_count=processed_count,
                error_count=error_count,
                errors=errors
            )

            # インポート完了ログを記録
            await self.company_service.log_import_completion(result, file_path)

            return result

        except Exception as e:
            logger.error(f"外資系企業CSVインポートエラー: {e}")
            return ImportResult(
                status=ImportStatus.FAILED,
                processed_count=0,
                error_count=1,
                errors=[f"Unexpected error: {str(e)}"]
            )

    async def import_japan_construction_csv(self, file_path: str) -> ImportResult:
        """日本建設業CSVファイルのインポート"""
        try:
            # ファイル存在チェック
            if not os.path.exists(file_path):
                return ImportResult(
                    status=ImportStatus.FAILED,
                    processed_count=0,
                    error_count=1,
                    errors=[f"CSV file not found: {file_path}"]
                )

            # CSVファイル読み込み
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except Exception as e:
                return ImportResult(
                    status=ImportStatus.FAILED,
                    processed_count=0,
                    error_count=1,
                    errors=[f"Failed to read CSV file: {str(e)}"]
                )

            # データクリーニング
            cleaned_data = self.clean_japan_construction_data(df)

            # データベースへの挿入
            processed_count = 0
            error_count = 0
            errors = []

            for company_data in cleaned_data:
                try:
                    await self.company_service.upsert_company_from_csv(company_data)
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Failed to import {company_data.get('name_original', 'unknown')}: {str(e)}")

            # 結果判定
            if error_count == 0:
                status = ImportStatus.SUCCESS
            elif processed_count > 0:
                status = ImportStatus.PARTIAL
            else:
                status = ImportStatus.FAILED

            result = ImportResult(
                status=status,
                processed_count=processed_count,
                error_count=error_count,
                errors=errors
            )

            # インポート完了ログを記録
            await self.company_service.log_import_completion(result, file_path)

            return result

        except Exception as e:
            logger.error(f"日本建設業CSVインポートエラー: {e}")
            return ImportResult(
                status=ImportStatus.FAILED,
                processed_count=0,
                error_count=1,
                errors=[f"Unexpected error: {str(e)}"]
            )

    async def merge_company_data(self, foreign_data: List[Dict], japan_data: List[Dict]) -> List[Dict]:
        """企業データの統合"""
        merged_data = []

        # 外資系データを基準に統合
        for foreign_company in foreign_data:
            normalized_name = foreign_company['name_normalized']

            # 対応する日本データを検索
            matching_japan = None
            for japan_company in japan_data:
                if japan_company['name_normalized'] == normalized_name:
                    matching_japan = japan_company
                    break

            # データ統合
            merged_company = {
                'name_normalized': normalized_name,
                'name_original': foreign_company['name_original'],
                'industry': foreign_company.get('industry', 'other'),
                'size': self._estimate_company_size(
                    foreign_company.get('foreign_company_data', {}).get('employee_count', 0)
                ),
                'foreign_company_data': foreign_company.get('foreign_company_data', {}),
                'construction_data': matching_japan['construction_data'] if matching_japan else {
                    'license_type': '',
                    'project_types': [],
                    'annual_revenue': 0.0
                }
            }

            merged_data.append(merged_company)

        # 日本データで外資系にないものを追加
        for japan_company in japan_data:
            normalized_name = japan_company['name_normalized']

            # 既に追加済みかチェック
            already_added = any(
                company['name_normalized'] == normalized_name
                for company in merged_data
            )

            if not already_added:
                merged_company = {
                    'name_normalized': normalized_name,
                    'name_original': japan_company['name_original'],
                    'industry': japan_company.get('industry', 'construction'),
                    'size': self._estimate_company_size(
                        japan_company.get('construction_data', {}).get('employee_count', 0)
                    ),
                    'foreign_company_data': {
                        'region': '',
                        'country': '',
                        'market_cap': 0.0
                    },
                    'construction_data': japan_company.get('construction_data', {})
                }

                merged_data.append(merged_company)

        return merged_data

    def normalize_company_name(self, name: str) -> str:
        """企業名の正規化"""
        if not name:
            return ''

        # 前後の空白を削除
        normalized = name.strip()

        # 英語の場合は小文字変換
        if re.match(r'^[a-zA-Z0-9\s\.\,\&\-\(\)]+$', normalized):
            normalized = normalized.lower()
            # 企業形態の略語を削除（inc., corp., corporation, ltd., limited, llc）
            normalized = re.sub(r'\b(inc\.?|corp\.?|corporation|ltd\.?|limited|llc)\b', '', normalized)
            # 余分なピリオドとカンマを削除
            normalized = re.sub(r'[.,]+', '', normalized)
            # 複数の空白を1つに統一
            normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def extract_country_from_origin(self, country_origin: str) -> Optional[str]:
        """Country_of_Origin列から国名を抽出"""
        if not country_origin or country_origin.lower() in ['nan', 'none', '', 'unknown']:
            return None

        country_origin = country_origin.strip()

        # よく知られた国名のマッピング
        country_mapping = {
            'united states': 'United States',
            'usa': 'United States',
            'us': 'United States',
            'south korea': 'South Korea',
            'korea': 'South Korea',
            'japan': 'Japan',
            'china': 'China',
            'united kingdom': 'United Kingdom',
            'uk': 'United Kingdom',
            'germany': 'Germany',
            'france': 'France',
            'italy': 'Italy',
            'spain': 'Spain',
            'canada': 'Canada',
            'australia': 'Australia',
            'india': 'India',
            'singapore': 'Singapore',
            'thailand': 'Thailand',
            'malaysia': 'Malaysia',
            'indonesia': 'Indonesia',
            'philippines': 'Philippines',
            'vietnam': 'Vietnam'
        }

        # 正規化された検索
        normalized_origin = country_origin.lower().strip()
        if normalized_origin in country_mapping:
            return country_mapping[normalized_origin]

        # 直接マッチしない場合は、元の文字列をタイトルケースで返す
        if len(country_origin) >= 2:
            return country_origin.title()

        return None

    def extract_country_from_location(self, location: str) -> Optional[str]:
        """Headquarters Location列から国名を抽出"""
        if not location or location.lower() in ['nan', 'none', '', 'unknown']:
            return None

        location = location.strip()

        # カンマで分割して最後の部分が国名と仮定
        parts = [part.strip() for part in location.split(',')]

        if len(parts) >= 2:
            potential_country = parts[-1]

            # 国名のマッピングを使用
            country_mapping = {
                'japan': 'Japan',
                'south korea': 'South Korea',
                'korea': 'South Korea',
                'united states': 'United States',
                'usa': 'United States',
                'us': 'United States',
                'china': 'China',
                'thailand': 'Thailand',
                'singapore': 'Singapore',
                'malaysia': 'Malaysia',
                'indonesia': 'Indonesia',
                'philippines': 'Philippines',
                'vietnam': 'Vietnam',
                'united kingdom': 'United Kingdom',
                'uk': 'United Kingdom',
                'germany': 'Germany',
                'france': 'France',
                'italy': 'Italy',
                'spain': 'Spain',
                'canada': 'Canada',
                'australia': 'Australia',
                'india': 'India'
            }

            normalized_country = potential_country.lower().strip()
            if normalized_country in country_mapping:
                return country_mapping[normalized_country]

            # マッピングにない場合は元の文字列をタイトルケースで返す
            if len(potential_country) >= 2:
                return potential_country.title()

        # 日本の都市名の場合は自動的にJapanを返す
        japanese_cities = [
            '東京', '大阪', '名古屋', '横浜', '札幌', '神戸', '京都', '福岡', '広島', '仙台',
            'tokyo', 'osaka', 'nagoya', 'yokohama', 'sapporo', 'kobe', 'kyoto',
            'fukuoka', 'hiroshima', 'sendai'
        ]

        location_lower = location.lower()
        for city in japanese_cities:
            if city in location_lower:
                return 'Japan'

        return None

    def validate_location_has_country(self, location: str) -> bool:
        """所在地に国名が含まれているかを検証"""
        if not location:
            return False

        # カンマ区切りで複数の部分がある場合、最後の部分が国名と仮定
        parts = [part.strip() for part in location.split(',')]
        if len(parts) >= 2:
            return True

        # 日本の都市名の場合は有効とする
        japanese_cities = [
            '東京', '大阪', '名古屋', '横浜', '札幌', '神戸', '京都', '福岡', '広島', '仙台'
        ]

        location_lower = location.lower()
        for city in japanese_cities:
            if city in location_lower:
                return True

        return False

    def clean_foreign_companies_data(self, df: pd.DataFrame) -> List[Dict]:
        """外資系企業CSVデータのクリーニング"""
        cleaned_data = []

        for _, row in df.iterrows():
            # 実際のCSV列名に合わせて修正 ('Company'列を使用)
            company_name = str(row.get('Company', '')).strip()

            # 企業名が空の場合はスキップ
            if not company_name or company_name.lower() in ['nan', 'none', '']:
                continue

            # データクリーニング
            industry = str(row.get('Industry_Sector', 'technology')).lower()
            if industry in ['nan', 'none', '', 'unknown']:
                industry = 'technology'  # デフォルト値

            # 国名の抽出と検証
            country_origin = str(row.get('Country_of_Origin', '')).strip()
            country = self.extract_country_from_origin(country_origin)

            # 国名が見つからない場合は警告ログを出力してスキップ
            if not country:
                logger.warning(f"No valid country found for company '{company_name}' - Country_of_Origin: '{country_origin}'")
                continue

            # 数値データの処理
            try:
                revenue = float(row.get('Estimated_Revenue_Million_USD', 0))
            except (ValueError, TypeError):
                revenue = 0.0

            # 従業員数は推定値として処理（実際のCSVにEmployees列がない場合）
            employee_count = 0

            company_data = {
                'name_normalized': self.normalize_company_name(company_name),
                'name_original': company_name,
                'industry': industry,
                'location': country,  # locationフィールドに国名を設定
                'country': country,   # 明示的にcountryフィールドも設定
                'foreign_company_data': {
                    'country': country,
                    'estimated_revenue_million_usd': revenue,
                    'employee_count': employee_count
                }
            }

            cleaned_data.append(company_data)

        return cleaned_data

    def clean_japan_construction_data(self, df: pd.DataFrame) -> List[Dict]:
        """日本建設業CSVデータのクリーニング"""
        cleaned_data = []

        for _, row in df.iterrows():
            # 実際のCSV列名に合わせて修正 ('Organization Name'列を使用)
            company_name = str(row.get('Organization Name', '')).strip()

            # 企業名が空の場合はスキップ
            if not company_name or company_name.lower() in ['nan', 'none', '']:
                continue

            # 本社所在地から国名を抽出
            headquarters_location = str(row.get('Headquarters Location', '')).strip()
            if headquarters_location in ['nan', 'none', '']:
                headquarters_location = ''

            # 国名の抽出と検証
            country = self.extract_country_from_location(headquarters_location)

            # 国名が見つからない場合は警告ログを出力してスキップ
            if not country:
                logger.warning(f"No valid country found for company '{company_name}' - Headquarters Location: '{headquarters_location}'")
                continue

            # 業界情報の処理
            industry_groups = str(row.get('Industry Groups', 'technology')).strip()
            if industry_groups in ['nan', 'none', '']:
                industry_groups = 'technology'

            # 数値データの処理
            try:
                funding_amount_usd = float(row.get('Total Funding Amount (in USD)', 0))
            except (ValueError, TypeError):
                funding_amount_usd = 0.0

            try:
                employee_range = str(row.get('Number of Employees', '0')).strip()
                # 範囲形式（例：101-250）から中央値を推定
                if '-' in employee_range:
                    parts = employee_range.split('-')
                    if len(parts) == 2:
                        try:
                            min_emp = int(parts[0])
                            max_emp = int(parts[1])
                            employee_count = (min_emp + max_emp) // 2
                        except:
                            employee_count = 0
                    else:
                        employee_count = 0
                else:
                    try:
                        employee_count = int(employee_range)
                    except:
                        employee_count = 0
            except (ValueError, TypeError):
                employee_count = 0

            company_data = {
                'name_normalized': self.normalize_company_name(company_name),
                'name_original': company_name,
                'industry': 'technology',  # 実際のデータは技術系企業が多い
                'location': headquarters_location,  # 完全な所在地情報
                'country': country,  # 抽出された国名
                'construction_data': {
                    'industry_groups': industry_groups,
                    'total_funding_usd': funding_amount_usd,
                    'employee_count': employee_count
                }
            }

            cleaned_data.append(company_data)

        return cleaned_data

    def _estimate_company_size(self, employee_count: int) -> str:
        """従業員数から企業規模を推定"""
        if employee_count <= 0:
            return 'other'
        elif employee_count <= 10:
            return 'startup'
        elif employee_count <= 50:
            return 'small'
        elif employee_count <= 200:
            return 'medium'
        elif employee_count <= 1000:
            return 'large'
        else:
            return 'enterprise'