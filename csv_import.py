#!/usr/bin/env python3
"""
CSVインポート実行ツール - コマンドライン実行版
"""
import asyncio
import sys
import os

# プロジェクトパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.tools.csv_import_tool import main

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)