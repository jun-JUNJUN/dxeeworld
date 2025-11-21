"""
企業データCSVインポートツール（設計書準拠版）

Usage:
    uv run python src/tools/import_companies_simple.py foreign_companies_101_300_japan_asia_complete.csv
    uv run python src/tools/import_companies_simple.py japan-construction-2025-8-26.csv
    uv run python src/tools/import_companies_simple.py --all
"""
import asyncio
import csv
import sys
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from src.database import DatabaseService
from src.models.company import IndustryType, CompanySize

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CompanyNameNormalizer:
    """企業名正規化クラス"""

    @staticmethod
    def normalize(name: str) -> str:
        """
        企業名を正規化して重複検出を容易にする

        Args:
            name: 正規化対象の企業名

        Returns:
            正規化された企業名
        """
        if not name:
            return ""

        # 1. Unicode正規化 (NFKC: 全角→半角、カタカナ統一)
        normalized = unicodedata.normalize('NFKC', name)

        # 2. 小文字化（英語企業名の大文字/小文字の違いを吸収）
        normalized = normalized.lower()

        # 3. 前後の空白削除
        normalized = normalized.strip()

        # 4. 連続する空白を1つにまとめる
        normalized = re.sub(r'\s+', ' ', normalized)

        # 5. 一般的な会社接尾辞の統一（株式会社、Inc.、Ltd.など）
        # 注: 完全削除ではなく統一（検索性を保つため）
        normalized = re.sub(r'株式会社', 'KK', normalized)
        normalized = re.sub(r'\binc\.?$', 'inc', normalized)
        normalized = re.sub(r'\bltd\.?$', 'ltd', normalized)
        normalized = re.sub(r'\bcorp\.?$', 'corp', normalized)
        normalized = re.sub(r'\bco\.?,?\s*ltd\.?$', 'co ltd', normalized)

        # 6. 特殊文字の削除（ハイフン、アンダースコアは残す）
        normalized = re.sub(r'[^\w\s\-_]', '', normalized)

        return normalized


class SimpleCSVImporter:
    """設計書準拠のCSVインポーター"""

    def __init__(self, db: DatabaseService):
        self.db = db
        self.normalizer = CompanyNameNormalizer()
        self.stats = {
            'total': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': 0
        }

    def validate_enum_value(self, enum_class, value: str, default) -> Any:
        """Enum値のバリデーション"""
        try:
            return enum_class(value)
        except ValueError:
            logger.warning("Invalid %s value: %s, using default: %s",
                         enum_class.__name__, value, default.value)
            return default

    def map_industry(self, industry_text: str) -> IndustryType:
        """業界テキストをIndustryType列挙型にマッピング"""
        if not industry_text:
            return IndustryType.OTHER

        industry_lower = industry_text.lower()

        # キーワードベースのマッピング（設計書準拠）
        industry_mapping = {
            IndustryType.TECHNOLOGY: ['software', 'technology', 'it', 'ai', 'saas', 'tech', 'information technology', 'data', 'virtualization', 'crm'],
            IndustryType.FINANCE: ['finance', 'bank', 'investment', 'fintech', 'financial'],
            IndustryType.HEALTHCARE: ['health', 'medical', 'healthcare', 'pharma', 'pharmaceutical', 'biotech'],
            IndustryType.EDUCATION: ['education', 'learning', 'school', 'training', 'edtech'],
            IndustryType.RETAIL: ['retail', 'e-commerce', 'commerce', 'consumer goods', 'consumer electronics'],
            IndustryType.MANUFACTURING: ['manufacturing', 'production', 'factory', 'automotive', 'industrial'],
            IndustryType.CONSULTING: ['consulting', 'advisory', 'professional services'],
            IndustryType.MEDIA: ['media', 'entertainment', 'publishing', 'advertising', 'marketing'],
            IndustryType.REAL_ESTATE: ['real estate', 'property', 'construction', 'building'],
            IndustryType.CONSTRUCTION: ['construction', 'building', 'engineering', 'infrastructure']
        }

        for industry_type, keywords in industry_mapping.items():
            if any(kw in industry_lower for kw in keywords):
                return industry_type

        return IndustryType.OTHER

    def map_company_size(self, employee_text: str) -> CompanySize:
        """従業員数テキストをCompanySize列挙型にマッピング"""
        if not employee_text or employee_text == '':
            return CompanySize.MEDIUM  # デフォルト

        # 範囲表記の処理 (例: "101-250", "11-50")
        if '-' in employee_text:
            parts = employee_text.split('-')
            try:
                max_employees = int(parts[1].strip())
                return self._size_from_count(max_employees)
            except (ValueError, IndexError):
                logger.warning("Invalid employee range format: %s", employee_text)
                return CompanySize.MEDIUM

        # 数値のみの場合
        try:
            count = int(employee_text.replace(',', '').strip())
            return self._size_from_count(count)
        except ValueError:
            logger.warning("Invalid employee count format: %s", employee_text)
            return CompanySize.MEDIUM

    def _size_from_count(self, count: int) -> CompanySize:
        """従業員数から企業規模を判定（設計書準拠）"""
        if count <= 10:
            return CompanySize.STARTUP
        elif count <= 50:
            return CompanySize.SMALL
        elif count <= 200:
            return CompanySize.MEDIUM
        elif count <= 1000:
            return CompanySize.LARGE
        else:
            return CompanySize.ENTERPRISE

    def parse_employee_count(self, employee_text: str) -> Optional[int]:
        """従業員数テキストを数値に変換"""
        if not employee_text or employee_text == '':
            return None

        # 範囲表記の場合は最大値を取得
        if '-' in employee_text:
            parts = employee_text.split('-')
            try:
                return int(parts[1].strip())
            except (ValueError, IndexError):
                return None

        # 数値のみの場合
        try:
            return int(employee_text.replace(',', '').strip())
        except ValueError:
            return None

    def parse_founded_year(self, date_text: str) -> Optional[int]:
        """設立日テキストから年を抽出"""
        if not date_text or date_text == '':
            return None

        try:
            # ISO形式の日付 (2018-01-01)
            if '-' in date_text:
                return int(date_text.split('-')[0])
            # 年のみ
            return int(date_text)
        except (ValueError, IndexError):
            return None

    def parse_float(self, value_text: str) -> Optional[float]:
        """文字列をfloatに変換"""
        if not value_text or value_text == '':
            return None
        try:
            return float(value_text.replace(',', '').strip())
        except ValueError:
            return None

    async def import_foreign_companies(self, csv_path: str) -> Dict[str, int]:
        """
        外資系企業CSVをインポート

        設計書準拠の構造:
        foreign_company_data: {region, country, market_cap}
        """
        logger.info("外資系企業CSVインポート開始: %s", csv_path)

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['total'] += 1

                try:
                    # 企業名の正規化と重複チェック
                    company_name = row['Company'].strip()
                    normalized_name = self.normalizer.normalize(company_name)

                    # 正規化名での重複チェック
                    existing = await self.db.find_one('companies', {
                        '$or': [
                            {'name': company_name},
                            {'name': normalized_name}
                        ]
                    })

                    if existing:
                        logger.debug("スキップ (既存): %s", company_name)
                        self.stats['skipped'] += 1
                        continue

                    # 業界マッピングとバリデーション
                    industry = self.map_industry(row.get('Industry_Sector', ''))
                    industry = self.validate_enum_value(IndustryType, industry.value, IndustryType.OTHER)

                    # 企業規模（外資系大企業として扱う）
                    size = CompanySize.ENTERPRISE
                    size = self.validate_enum_value(CompanySize, size.value, CompanySize.ENTERPRISE)

                    # 国名バリデーション
                    country = row.get('Country_of_Origin', '').strip()
                    if not country:
                        logger.error("必須フィールド 'country' が空: %s", company_name)
                        self.stats['errors'] += 1
                        continue

                    # 設計書準拠: foreign_company_data構造
                    foreign_company_data = {
                        'region': row.get('Asian_Manufacturing_Presence', '').strip() or None,
                        'country': country,
                        'market_cap': self.parse_float(row.get('Estimated_Revenue_Million_USD', ''))
                        # 注: CSV には market_cap がないため、revenue を使用
                    }

                    # Companyドキュメント作成（設計書準拠）
                    company_doc = {
                        'name': normalized_name,  # 正規化名を使用
                        'name_original': company_name,  # 元の名前を保存
                        'industry': industry.value,
                        'size': size.value,
                        'country': country,
                        'location': '日本',  # Japan Operations
                        'description': row.get('Japan_Operations', '').strip() or None,
                        'website': None,
                        'founded_year': None,
                        'employee_count': None,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc),
                        'is_active': True,
                        'source_files': [Path(csv_path).name],
                        'foreign_company_data': foreign_company_data,
                        'construction_data': {}  # 空の辞書（設計書準拠）
                    }

                    # データベースに挿入
                    await self.db.create('companies', company_doc)
                    self.stats['inserted'] += 1
                    logger.info("✓ インポート成功: %s → %s", company_name, normalized_name)

                except Exception:
                    self.stats['errors'] += 1
                    company_name_for_log = row.get('Company', 'Unknown')
                    logger.exception("✗ インポートエラー: %s", company_name_for_log)

        return self.stats

    async def import_construction_companies(self, csv_path: str) -> Dict[str, int]:
        """
        日本スタートアップCSVをインポート

        設計書準拠の構造:
        construction_data: {license_type, project_types, annual_revenue}
        """
        logger.info("日本スタートアップCSVインポート開始: %s", csv_path)

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['total'] += 1

                try:
                    # 企業名の正規化と重複チェック
                    company_name = row['Organization Name'].strip()
                    normalized_name = self.normalizer.normalize(company_name)

                    # 正規化名での重複チェック
                    existing = await self.db.find_one('companies', {
                        '$or': [
                            {'name': company_name},
                            {'name': normalized_name}
                        ]
                    })

                    if existing:
                        logger.debug("スキップ (既存): %s", company_name)
                        self.stats['skipped'] += 1
                        continue

                    # 従業員数とサイズの決定
                    employee_text = row.get('Number of Employees', '').strip()
                    company_size = self.map_company_size(employee_text)
                    company_size = self.validate_enum_value(CompanySize, company_size.value, CompanySize.MEDIUM)
                    employee_count = self.parse_employee_count(employee_text)

                    # 業界マッピングとバリデーション
                    industry = self.map_industry(row.get('Industry Groups', ''))
                    industry = self.validate_enum_value(IndustryType, industry.value, IndustryType.OTHER)

                    # 所在地から国名を抽出（"Tokyo, Tokyo, Japan" → "Japan"）
                    location = row.get('Headquarters Location', '').strip()
                    country = '日本'  # デフォルト
                    if location and ',' in location:
                        parts = [p.strip() for p in location.split(',')]
                        if len(parts) >= 3:
                            country = parts[-1]  # 最後の部分が国名

                    # 設計書準拠: construction_data構造
                    # 注: CSVはスタートアップデータなので、建設業フィールドにマッピング
                    industry_groups = row.get('Industry Groups', '').strip()
                    project_types = [p.strip() for p in industry_groups.split(',')] if industry_groups else []

                    construction_data = {
                        'license_type': row.get('Company Type', '').strip() or None,  # For Profit, etc.
                        'project_types': project_types,  # 業界グループをプロジェクトタイプとして使用
                        'annual_revenue': self.parse_float(row.get('Total Funding Amount (in USD)', ''))
                        # 注: 資金調達額を年間収益として使用（実際のデータに近い）
                    }

                    # Companyドキュメント作成（設計書準拠）
                    company_doc = {
                        'name': normalized_name,  # 正規化名を使用
                        'name_original': company_name,  # 元の名前を保存
                        'industry': industry.value,
                        'size': company_size.value,
                        'country': country,
                        'location': location or None,
                        'description': row.get('Description', '').strip() or None,
                        'website': row.get('Organization Name URL', '').strip() or None,
                        'founded_year': self.parse_founded_year(row.get('Founded Date', '')),
                        'employee_count': employee_count,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc),
                        'is_active': True,
                        'source_files': [Path(csv_path).name],
                        'foreign_company_data': {},  # 空の辞書（設計書準拠）
                        'construction_data': construction_data
                    }

                    # データベースに挿入
                    await self.db.create('companies', company_doc)
                    self.stats['inserted'] += 1
                    logger.info("✓ インポート成功: %s → %s", company_name, normalized_name)

                except Exception:
                    self.stats['errors'] += 1
                    company_name_for_log = row.get('Organization Name', 'Unknown')
                    logger.exception("✗ インポートエラー: %s", company_name_for_log)

        return self.stats


async def create_indexes(db: DatabaseService):
    """設計書に従ったインデックスを作成"""
    logger.info("インデックスを作成中...")

    companies_collection = db.db['companies']

    try:
        # 1. 企業名による一意性確保（設計書: line 356）
        await companies_collection.create_index(
            [("name", 1)],
            unique=True,
            name="name_unique"
        )
        logger.info("✓ インデックス作成: name (unique)")

        # 2. フィルター検索最適化（設計書: line 359）
        await companies_collection.create_index(
            [("industry", 1), ("size", 1), ("location", 1)],
            name="filter_search"
        )
        logger.info("✓ インデックス作成: industry + size + location")

        # 3. 設立年インデックス（設計書: line 360）
        await companies_collection.create_index(
            [("founded_year", 1)],
            name="founded_year"
        )
        logger.info("✓ インデックス作成: founded_year")

        # 4. 従業員数インデックス（設計書: line 361）
        await companies_collection.create_index(
            [("employee_count", 1)],
            name="employee_count"
        )
        logger.info("✓ インデックス作成: employee_count")

        # 5. ページネーション最適化（設計書: line 364-365）
        await companies_collection.create_index(
            [("created_at", -1)],
            name="created_at_desc"
        )
        logger.info("✓ インデックス作成: created_at (desc)")

        await companies_collection.create_index(
            [("name", 1), ("created_at", -1)],
            name="name_created_at"
        )
        logger.info("✓ インデックス作成: name + created_at")

        logger.info("インデックス作成完了")

    except Exception:
        logger.exception("インデックス作成エラー（既存の場合は無視）")


async def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # データベース接続
    db = DatabaseService()
    await db.connect()

    try:
        # インデックス作成（初回実行時）
        await create_indexes(db)

        importer = SimpleCSVImporter(db)

        if sys.argv[1] == '--all':
            # すべてのCSVファイルをインポート
            csv_files = [
                'foreign_companies_101_300_japan_asia_complete.csv',
                'japan-construction-2025-8-26.csv'
            ]

            for csv_file in csv_files:
                if not Path(csv_file).exists():
                    logger.warning("ファイルが見つかりません: %s", csv_file)
                    continue

                if 'foreign' in csv_file:
                    await importer.import_foreign_companies(csv_file)
                elif 'construction' in csv_file or 'japan' in csv_file:
                    await importer.import_construction_companies(csv_file)
        else:
            # 個別CSVファイルをインポート
            csv_path = sys.argv[1]

            if not Path(csv_path).exists():
                logger.error("ファイルが見つかりません: %s", csv_path)
                sys.exit(1)

            # ファイル名から種別を判定
            if 'foreign' in csv_path.lower():
                await importer.import_foreign_companies(csv_path)
            elif 'construction' in csv_path.lower() or 'japan' in csv_path.lower():
                await importer.import_construction_companies(csv_path)
            else:
                logger.error("CSVファイルの種別を判定できません: %s", csv_path)
                logger.error("ファイル名に 'foreign' または 'construction'/'japan' を含めてください")
                sys.exit(1)

        # 結果サマリー
        print("\n" + "=" * 80)
        print("インポート完了")
        print("=" * 80)
        print(f"総件数:       {importer.stats['total']}")
        print(f"インポート:   {importer.stats['inserted']}")
        print(f"スキップ:     {importer.stats['skipped']}")
        print(f"エラー:       {importer.stats['errors']}")
        print("=" * 80)

        # データベース統計
        total_companies = await db.count_documents('companies', {})
        print(f"\nデータベース総企業数: {total_companies}")

        # 業界別統計
        print("\n業界別統計:")
        for industry in IndustryType:
            count = await db.count_documents('companies', {'industry': industry.value})
            if count > 0:
                print(f"  {industry.value}: {count}件")

    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
