"""
Test for CompanyListHandler _get_size_label method fix
"""
import pytest
from src.handlers.company_handler import CompanyListHandler


class TestCompanyListHandlerSizeLabelFix:
    """CompanyListHandlerの_get_size_labelメソッド修復テスト"""

    def test_get_size_label_method_exists(self):
        """_get_size_labelメソッドが存在することを確認"""
        # Direct method check without instantiating the full handler
        assert hasattr(CompanyListHandler, '_get_size_label'), "_get_size_labelメソッドが存在しません"

    def test_get_size_label_returns_correct_labels(self):
        """_get_size_labelメソッドが正しいラベルを返すことを確認"""
        # Create a simple mock to test the method
        class MockHandler:
            def _get_size_label(self, size_value):
                return CompanyListHandler._get_size_label(self, size_value)

        handler = MockHandler()

        # 各企業規模に対して正しいラベルが返されることを確認
        assert handler._get_size_label('startup') == 'スタートアップ (1-10名)'
        assert handler._get_size_label('small') == '小企業 (11-50名)'
        assert handler._get_size_label('medium') == '中企業 (51-200名)'
        assert handler._get_size_label('large') == '大企業 (201-1000名)'
        assert handler._get_size_label('enterprise') == '大企業 (1000名以上)'
        assert handler._get_size_label('other') == 'その他'

    def test_get_size_label_handles_unknown_values(self):
        """_get_size_labelメソッドが未知の値を適切に処理することを確認"""
        class MockHandler:
            def _get_size_label(self, size_value):
                return CompanyListHandler._get_size_label(self, size_value)

        handler = MockHandler()

        # 未知の値の場合は元の値をそのまま返す
        assert handler._get_size_label('unknown_size') == 'unknown_size'
        assert handler._get_size_label('') == ''

