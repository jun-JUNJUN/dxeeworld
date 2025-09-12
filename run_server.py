#!/usr/bin/env python3
"""
サーバー起動スクリプト
"""
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.app import main

if __name__ == "__main__":
    main()