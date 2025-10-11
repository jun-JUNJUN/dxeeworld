"""
ReviewListHandlerのプレビュー表示機能のユニットテスト
"""

import pytest


def truncate_comment_for_preview(comment: str, max_chars: int = 128) -> dict:
    """
    レビューコメントをプレビュー用に切り詰める関数
    （ReviewListHandlerにstaticmethodとして実装予定）

    Args:
        comment: レビューコメント
        max_chars: 最大表示文字数（デフォルト: 128）

    Returns:
        dict: {
            "visible_text": 表示する部分,
            "masked_text": 伏せ字部分,
            "has_more": 続きがあるか
        }
    """
    # 実装はReviewListHandlerに追加する
    from src.handlers.review_handler import ReviewListHandler

    return ReviewListHandler.truncate_comment_for_preview(comment, max_chars)


class TestReviewCommentPreview:
    """レビューコメントプレビュー機能のテストクラス"""

    def test_truncate_comment_short(self):
        """128文字以下のコメントはそのまま表示、伏せ字なし"""
        comment = "これは短いコメントです。"

        result = truncate_comment_for_preview(comment, max_chars=128)

        assert result["visible_text"] == comment
        assert result["masked_text"] == ""
        assert result["has_more"] is False

    def test_truncate_comment_long(self):
        """128文字を超えるコメントは128文字+伏せ字"""
        # 150文字のコメント
        comment = "a" * 150

        result = truncate_comment_for_preview(comment, max_chars=128)

        assert result["visible_text"] == "a" * 128
        assert result["masked_text"] == "●●●●●"
        assert result["has_more"] is True

    def test_truncate_comment_multiline_short_first_line(self):
        """複数行で最初の1行が128文字以下の場合、最初の1行+伏せ字"""
        comment = "最初の行です。\n2行目です。\n3行目です。"

        result = truncate_comment_for_preview(comment, max_chars=128)

        assert result["visible_text"] == "最初の行です。"
        assert result["masked_text"] == "●●●●●"
        assert result["has_more"] is True

    def test_truncate_comment_multiline_long_first_line(self):
        """複数行で最初の1行が128文字超の場合、128文字+伏せ字"""
        # 最初の1行が150文字
        first_line = "a" * 150
        comment = f"{first_line}\n2行目です。"

        result = truncate_comment_for_preview(comment, max_chars=128)

        assert result["visible_text"] == "a" * 128
        assert result["masked_text"] == "●●●●●"
        assert result["has_more"] is True

    def test_truncate_comment_empty(self):
        """空コメントの処理"""
        comment = ""

        result = truncate_comment_for_preview(comment, max_chars=128)

        assert result["visible_text"] == ""
        assert result["masked_text"] == ""
        assert result["has_more"] is False

    def test_truncate_comment_exactly_128_chars(self):
        """ちょうど128文字のコメント（伏せ字不要）"""
        comment = "a" * 128

        result = truncate_comment_for_preview(comment, max_chars=128)

        assert result["visible_text"] == comment
        assert result["masked_text"] == ""
        assert result["has_more"] is False

    def test_truncate_comment_custom_max_chars(self):
        """カスタムmax_chars値の動作確認"""
        comment = "a" * 100

        result = truncate_comment_for_preview(comment, max_chars=50)

        assert result["visible_text"] == "a" * 50
        assert result["masked_text"] == "●●●●●"
        assert result["has_more"] is True
