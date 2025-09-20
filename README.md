# DXEEWorld

Kaggle ライクな UI/UX を持つスタートアップエコシステムプラットフォーム

## セットアップ

### 簡単起動（推奨）

**Option 1: Simple UV Runner (推奨)**
```bash
# サーバー起動
./run_with_uv.sh

# テスト実行
./run_with_uv.sh test
```

**Option 2: Full Project Setup**
```bash
# サーバー起動
./activate_server.sh

# テスト実行
./activate_server.sh test
```

### 手動セットアップ

#### 1. 依存関係のインストール

**uv使用（推奨）:**
```bash
uv sync
```

**pip使用:**
```bash
pip install -r requirements.txt
```

#### 2. 環境設定

```bash
cp .env.example .env
# .env ファイルを編集して適切な値を設定
```

#### 3. MongoDB の起動

```bash
# ローカルでMongoDBを起動（Dockerの例）
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

#### 4. サーバーの起動

**uv使用:**
```bash
uv run python run_server.py
```

**直接実行:**
```bash
python run_server.py
```

## テスト実行

**uv使用:**
```bash
uv run pytest
```

**直接実行:**
```bash
pytest
```

## 技術スタック

- **Backend**: Tornado 6.5.2
- **Default Port**: 8202
- **Database**: MongoDB 7.0+
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Testing**: pytest, pytest-tornado

## プロジェクト構造

```
dxeeworld/
├── src/                    # ソースコード
│   ├── app.py             # メインアプリケーション
│   ├── config.py          # 設定管理
│   ├── database.py        # データベース接続
│   └── handlers.py        # HTTPハンドラー
├── static/                # 静的ファイル
│   ├── css/
│   └── js/
├── tests/                 # テストファイル
├── requirements.txt       # Python依存関係
└── run_server.py          # サーバー起動スクリプト
```