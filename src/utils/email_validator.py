"""
メールアドレスバリデーション機能
Task 5.3.1: メール登録フォームとバリデーション機能
"""
import re


def is_valid_email(email: str) -> bool:
    """
    メールアドレスの形式を検証する

    Args:
        email: 検証するメールアドレス

    Returns:
        bool: 有効な形式の場合True、無効な場合False
    """
    if not email or not isinstance(email, str):
        return False

    # 基本的なメールアドレス形式のパターン
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # 基本パターンチェック
    if not re.match(pattern, email):
        return False

    # 連続ドットのチェック
    if '..' in email:
        return False

    # 先頭・末尾のドットチェック
    local_part, domain_part = email.split('@')
    if local_part.startswith('.') or local_part.endswith('.'):
        return False

    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False

    return True


def validate_email_format(email: str) -> dict:
    """
    メールアドレスの詳細バリデーション結果を返す

    Args:
        email: 検証するメールアドレス

    Returns:
        dict: バリデーション結果と詳細メッセージ
    """
    result = {
        'valid': False,
        'errors': []
    }

    if not email:
        result['errors'].append('メールアドレスが入力されていません')
        return result

    if not isinstance(email, str):
        result['errors'].append('メールアドレスは文字列である必要があります')
        return result

    if len(email) > 254:
        result['errors'].append('メールアドレスが長すぎます')
        return result

    if '@' not in email:
        result['errors'].append('有効なメールアドレス形式ではありません')
        return result

    if email.count('@') != 1:
        result['errors'].append('メールアドレスに@は1つまでです')
        return result

    local_part, domain_part = email.split('@')

    if not local_part:
        result['errors'].append('メールアドレスのローカル部が空です')
        return result

    if not domain_part:
        result['errors'].append('メールアドレスのドメイン部が空です')
        return result

    if len(local_part) > 64:
        result['errors'].append('メールアドレスのローカル部が長すぎます')
        return result

    if '..' in email:
        result['errors'].append('連続するドットは使用できません')
        return result

    # 基本的なパターンチェック
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        result['errors'].append('有効なメールアドレス形式ではありません')
        return result

    result['valid'] = True
    return result