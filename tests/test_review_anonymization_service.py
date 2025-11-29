"""
レビュー匿名化サービスのテスト
"""
import pytest
from src.services.review_anonymization_service import ReviewAnonymizationService


class TestReviewAnonymizationService:
    """ReviewAnonymizationServiceのテストクラス"""

    def test_anonymize_user_id_consistency(self):
        """同じuser_idは常に同じ匿名化表示になることを確認"""
        service = ReviewAnonymizationService()
        user_id = "user123"

        result1 = service.anonymize_user_id(user_id)
        result2 = service.anonymize_user_id(user_id)

        assert result1 == result2, "同じuser_idで異なる匿名化表示が生成された"

    def test_anonymize_user_id_format(self):
        """匿名化表示が「ユーザー[A-Z]」形式であることを確認"""
        service = ReviewAnonymizationService()
        result = service.anonymize_user_id("user123")

        assert result.startswith("ユーザー"), "匿名化表示が「ユーザー」で始まっていない"
        assert len(result) == 5, "匿名化表示の長さが不正（「ユーザー」+ 1文字であるべき）"
        # 最後の1文字がアルファベット（A-Z）であることを確認
        last_char = result[-1]
        assert last_char.isalpha() and last_char.isupper(), "最後の文字がA-Zのアルファベットではない"

    def test_anonymize_user_id_different_users(self):
        """異なるuser_idは異なる匿名化表示になることを確認（高確率）"""
        service = ReviewAnonymizationService()
        user_id1 = "user123"
        user_id2 = "user456"

        result1 = service.anonymize_user_id(user_id1)
        result2 = service.anonymize_user_id(user_id2)

        # 26文字のアルファベットがあるため、衝突する可能性はあるが低い
        # このテストは統計的に正しいが、稀に失敗する可能性がある
        assert result1 != result2, "異なるuser_idで同じ匿名化表示が生成された（衝突）"

    def test_anonymize_user_id_with_salt(self):
        """ソルトを変更すると異なる匿名化表示になることを確認"""
        service1 = ReviewAnonymizationService(salt="salt1")
        service2 = ReviewAnonymizationService(salt="salt2")
        user_id = "user123"

        result1 = service1.anonymize_user_id(user_id)
        result2 = service2.anonymize_user_id(user_id)

        assert result1 != result2, "異なるソルトで同じ匿名化表示が生成された"

    def test_anonymize_user_id_with_no_salt(self):
        """ソルトなしでもハッシュ化が正常に動作することを確認"""
        service = ReviewAnonymizationService()
        result = service.anonymize_user_id("user123")

        assert result.startswith("ユーザー")
        assert len(result) == 5

    def test_hash_user_id_returns_hex_string(self):
        """_hash_user_id が16進数文字列を返すことを確認"""
        service = ReviewAnonymizationService()
        result = service._hash_user_id("user123")

        # SHA-256は64文字の16進数文字列を返す
        assert isinstance(result, str), "ハッシュ値が文字列ではない"
        assert len(result) == 64, "SHA-256ハッシュ値の長さが64文字ではない"
        # 16進数文字列であることを確認
        assert all(c in '0123456789abcdef' for c in result), "16進数文字列ではない"

    def test_hash_to_letter_returns_single_uppercase_letter(self):
        """_hash_to_letter がA-Zの1文字を返すことを確認"""
        service = ReviewAnonymizationService()

        # いくつかのハッシュ値でテスト
        test_hashes = [
            "0" * 64,  # 全て0
            "f" * 64,  # 全てf
            "a1b2c3d4" + "0" * 56,  # 混在
        ]

        for hash_value in test_hashes:
            result = service._hash_to_letter(hash_value)
            assert len(result) == 1, "1文字ではない"
            assert result.isalpha() and result.isupper(), "A-Zのアルファベットではない"
            assert 'A' <= result <= 'Z', "A-Zの範囲外"

    def test_anonymize_user_id_empty_string(self):
        """空文字列のuser_idでも正常に動作することを確認"""
        service = ReviewAnonymizationService()
        result = service.anonymize_user_id("")

        # 空文字列でもハッシュ化は可能
        assert result.startswith("ユーザー")
        assert len(result) == 5

    def test_anonymize_user_id_special_characters(self):
        """特殊文字を含むuser_idでも正常に動作することを確認"""
        service = ReviewAnonymizationService()
        special_user_ids = [
            "user@example.com",
            "user-123_456",
            "ユーザー123",
            "用户456",
        ]

        for user_id in special_user_ids:
            result = service.anonymize_user_id(user_id)
            assert result.startswith("ユーザー"), f"user_id '{user_id}' で正しい形式ではない"
            assert len(result) == 5
