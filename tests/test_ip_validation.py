"""
IPアドレス検証のユニットテスト
"""
import ipaddress
import pytest


def is_valid_ip(ip_str: str) -> bool:
    """
    IPアドレスの検証（BaseHandler._is_valid_ip と同じロジック）
    
    Args:
        ip_str: 検証対象のIPアドレス文字列
        
    Returns:
        bool: 有効なIPv4またはIPv6アドレスの場合True
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


class TestIPValidation:
    """IPアドレス検証のテストクラス"""

    def test_is_valid_ip_ipv4(self) -> None:
        """有効なIPv4アドレスの検証"""
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("8.8.8.8") is True
        assert is_valid_ip("127.0.0.1") is True
        assert is_valid_ip("203.0.113.195") is True

    def test_is_valid_ip_ipv6(self) -> None:
        """有効なIPv6アドレスの検証"""
        assert is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert is_valid_ip("::1") is True
        assert is_valid_ip("fe80::1") is True

    def test_is_valid_ip_invalid(self) -> None:
        """無効なIPアドレスの検証"""
        assert is_valid_ip("invalid") is False
        assert is_valid_ip("999.999.999.999") is False
        assert is_valid_ip("192.168.1") is False
        assert is_valid_ip("") is False
        assert is_valid_ip("<script>alert('xss')</script>") is False
        assert is_valid_ip("../../etc/passwd") is False
        assert is_valid_ip("javascript:alert(1)") is False

    def test_forwarded_for_parsing(self) -> None:
        """X-Forwarded-Forのパース処理テスト"""
        # カンマ区切りの最初のIPを取得
        forwarded_for = "203.0.113.195, 70.41.3.18, 150.172.238.178"
        first_ip = forwarded_for.split(",")[0].strip()
        assert first_ip == "203.0.113.195"
        assert is_valid_ip(first_ip) is True

    def test_xss_injection_prevention(self) -> None:
        """XSS攻撃ベクターの検証"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "';DROP TABLE users;--",
            "../../../etc/passwd",
            "javascript:void(0)",
            "' OR '1'='1"
        ]
        for malicious in malicious_inputs:
            assert is_valid_ip(malicious) is False
