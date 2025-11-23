# Alibaba Cloud CI/CD 構築手順書
## Python + Tornado + MongoDB アプリケーション向け

本手順書では、GitHubリポジトリからAlibaba Cloud ECSへPython + Tornado + MongoDBアプリケーションを自動デプロイするCI/CDパイプラインの構築方法を解説します。

---

## 目次

1. 前提条件
2. アーキテクチャ概要
3. Alibaba Cloudリソースの準備
4. GitHub Actionsの設定
5. デプロイスクリプトの作成
6. CI/CDパイプラインのテスト
7. トラブルシューティング
8. 運用のベストプラクティス

---

## 1. 前提条件

### 必要なアカウント・リソース
- **Alibaba Cloudアカウント**（有効なサブスクリプション）
- **GitHubアカウント**とリポジトリ
- **ECSインスタンス**（Python 3.8+とDockerがインストール済み）
- **MongoDB**（Alibaba Cloud Database for MongoDBまたはECS上にセルフホスト）

### 必要なツール（ローカル開発環境）
- Git
- Python 3.8以上
- Docker（オプション：コンテナ化する場合）
- SSH クライアント

### アプリケーション要件
- `requirements.txt`ファイル
- Tornadoアプリケーションのエントリーポイント（例：`app.py`）
- MongoDBへの接続設定

---

## 2. アーキテクチャ概要

### CI/CDフロー

GitHub Repository
    ↓ (git push)
GitHub Actions トリガー
    ↓
1. コードチェックアウト
2. 依存関係インストール
3. テスト実行（オプション）
4. Dockerイメージビルド（またはコード直接デプロイ）
5. Alibaba Cloud Container Registry (ACR) へプッシュ
6. ECSインスタンスへデプロイ
7. アプリケーション再起動

### 使用するAlibaba Cloudサービス

| サービス | 用途 |
|---------|------|
| **ECS (Elastic Compute Service)** | アプリケーション実行環境 |
| **ACR (Container Registry)** | Dockerイメージの保管 |
| **ApsaraDB for MongoDB** | マネージドMongoDBサービス |
| **RAM (Resource Access Management)** | アクセス制御とIAM |
| **VPC (Virtual Private Cloud)** | ネットワークセキュリティ |

---

## 3. Alibaba Cloudリソースの準備

### 3.1 RAMユーザーの作成とアクセスキー取得

#### 手順

1. **Alibaba Cloudコンソール**にログイン
2. **RAM (Resource Access Management)** サービスに移動
3. **ユーザー** > **ユーザーの作成**を選択

**RAMユーザー設定：**
ユーザー名: github-actions-deploy
アクセス方式: プログラムアクセス（AccessKey）

4. 以下のポリシーをアタッチ：
   - `AliyunECSFullAccess`（ECS管理）
   - `AliyunContainerRegistryFullAccess`（ACR管理）
   - `AliyunMongoDBFullAccess`（MongoDB管理：オプション）

5. **AccessKey ID**と**AccessKey Secret**を安全に保存

> **重要**: AccessKey Secretは一度しか表示されません。必ずメモしてください。

### 3.2 Container Registryの設定

#### 名前空間とリポジトリの作成

1. **Container Registry**コンソールに移動
2. **名前空間**を作成（例：`production`）
3. **リポジトリ**を作成

リポジトリ名: tornado-app
リポジトリタイプ: プライベート
リージョン: ap-northeast-1（東京）

4. リポジトリのURIをメモ：
registry.ap-northeast-1.aliyuncs.com/production/tornado-app

### 3.3 ECSインスタンスの準備

#### SSH接続とDocker環境のセットアップ

**ECSインスタンスにSSH接続：**
ssh root@<ECS-PUBLIC-IP>

**Dockerのインストール（未インストールの場合）：**
# Alibaba Cloud Linux / CentOS
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Ubuntu
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

**Docker Composeのインストール（推奨）：**
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version

**Python環境のセットアップ（Dockerを使わない場合）：**
sudo yum install -y python3 python3-pip
pip3 install --upgrade pip

### 3.4 MongoDBのセットアップ

#### オプション A: Alibaba Cloud Database for MongoDB（推奨）

1. **ApsaraDB for MongoDB**コンソールに移動
2. インスタンスを作成：
   - バージョン: MongoDB 4.4以上
   - リージョン: ECSと同じリージョン
   - VPC: ECSインスタンスと同じVPC
3. 接続文字列を取得：
mongodb://username:password@dds-xxxxx.mongodb.rds.aliyuncs.com:3717/dbname

#### オプション B: ECS上にMongoDBをセルフホスト

**Dockerを使用してMongoDBをデプロイ：**
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v /data/mongodb:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=your_secure_password \
  mongo:4.4

### 3.5 セキュリティグループの設定

**ECSセキュリティグループのインバウンドルール：**

| プロトコル | ポート | ソース | 用途 |
|----------|-------|-------|------|
| SSH | 22 | GitHub Actions IP範囲 | デプロイアクセス |
| HTTP | 80 | 0.0.0.0/0 | Webトラフィック |
| HTTPS | 443 | 0.0.0.0/0 | Webトラフィック（SSL） |
| カスタムTCP | 8888 | 0.0.0.0/0 | Tornado デフォルトポート |

---

## 4. GitHub Actionsの設定

### 4.1 GitHub Secretsの設定

GitHubリポジトリで機密情報を安全に保管します。

1. GitHubリポジトリにアクセス
2. **Settings** > **Secrets and variables** > **Actions**
3. **New repository secret**で以下を追加：

| Secret名 | 値 | 説明 |
|---------|-----|------|
| `ALIBABA_ACCESS_KEY_ID` | your_access_key_id | RAMユーザーのAccessKey ID |
| `ALIBABA_ACCESS_KEY_SECRET` | your_access_key_secret | RAMユーザーのAccessKey Secret |
| `ACR_REGISTRY` | registry.ap-northeast-1.aliyuncs.com | ACRレジストリURL |
| `ACR_NAMESPACE` | production | ACR名前空間 |
| `ACR_REPOSITORY` | tornado-app | ACRリポジトリ名 |
| `ECS_HOST` | 192.168.1.100 | ECSパブリックIPアドレス |
| `ECS_USERNAME` | root | ECSログインユーザー名 |
| `ECS_SSH_KEY` | -----BEGIN RSA PRIVATE KEY----- | SSH秘密鍵（全体） |
| `MONGODB_URI` | mongodb://... | MongoDB接続文字列 |

### 4.2 SSH鍵ペアの作成

**ローカル環境で実行：**
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_actions_key

**公開鍵をECSインスタンスに追加：**
# ECSインスタンスにSSH接続
ssh root@<ECS-PUBLIC-IP>

# 公開鍵を追加
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "公開鍵の内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

**秘密鍵の内容をGitHub Secretsに追加：**
cat ~/.ssh/github_actions_key
# 出力全体を ECS_SSH_KEY としてGitHub Secretsに追加

### 4.3 GitHub Actionsワークフローファイルの作成

#### 方法1: Dockerコンテナ化デプロイ（推奨）

`.github/workflows/deploy.yml`を作成：

name: CI/CD Pipeline for Tornado App

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

env:
  ACR_REGISTRY: ${{ secrets.ACR_REGISTRY }}
  ACR_NAMESPACE: ${{ secrets.ACR_NAMESPACE }}
  ACR_REPOSITORY: ${{ secrets.ACR_REPOSITORY }}
  IMAGE_TAG: ${{ github.sha }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8

      - name: Lint with flake8
        run: |
          # コードスタイルチェック
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Run Tests
        run: |
          pytest tests/ --cov=. --cov-report=xml
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}

  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Configure Alibaba Cloud Credentials
        uses: aliyun/configure-aliyun-credentials-action@v1
        with:
          access-key-id: ${{ secrets.ALIBABA_ACCESS_KEY_ID }}
          access-key-secret: ${{ secrets.ALIBABA_ACCESS_KEY_SECRET }}
          region-id: ap-northeast-1

      - name: Login to Alibaba Cloud Container Registry
        run: |
          docker login \
            --username=${{ secrets.ALIBABA_ACCESS_KEY_ID }} \
            --password=${{ secrets.ALIBABA_ACCESS_KEY_SECRET }} \
            ${{ env.ACR_REGISTRY }}

      - name: Build Docker Image
        run: |
          docker build \
            --tag ${{ env.ACR_REGISTRY }}/${{ env.ACR_NAMESPACE }}/${{ env.ACR_REPOSITORY }}:${{ env.IMAGE_TAG }} \
            --tag ${{ env.ACR_REGISTRY }}/${{ env.ACR_NAMESPACE }}/${{ env.ACR_REPOSITORY }}:latest \
            --file Dockerfile \
            .

      - name: Push Docker Image to ACR
        run: |
          docker push ${{ env.ACR_REGISTRY }}/${{ env.ACR_NAMESPACE }}/${{ env.ACR_REPOSITORY }}:${{ env.IMAGE_TAG }}
          docker push ${{ env.ACR_REGISTRY }}/${{ env.ACR_NAMESPACE }}/${{ env.ACR_REPOSITORY }}:latest

  deploy:
    name: Deploy to ECS
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup SSH Key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.ECS_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H ${{ secrets.ECS_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy to ECS via SSH
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.ECS_USERNAME }}@${{ secrets.ECS_HOST }} << 'EOF'
            # ACRにログイン
            docker login \
              --username=${{ secrets.ALIBABA_ACCESS_KEY_ID }} \
              --password=${{ secrets.ALIBABA_ACCESS_KEY_SECRET }} \
              ${{ env.ACR_REGISTRY }}

            # 最新のイメージをプル
            docker pull ${{ env.ACR_REGISTRY }}/${{ env.ACR_NAMESPACE }}/${{ env.ACR_REPOSITORY }}:latest

            # 既存のコンテナを停止・削除
            docker stop tornado-app || true
            docker rm tornado-app || true

            # 新しいコンテナを起動
            docker run -d \
              --name tornado-app \
              --restart unless-stopped \
              -p 80:8888 \
              -e MONGODB_URI="${{ secrets.MONGODB_URI }}" \
              -e ENVIRONMENT="production" \
              ${{ env.ACR_REGISTRY }}/${{ env.ACR_NAMESPACE }}/${{ env.ACR_REPOSITORY }}:latest

            # 古いイメージをクリーンアップ
            docker image prune -f
          EOF

      - name: Verify Deployment
        run: |
          sleep 10
          curl -f http://${{ secrets.ECS_HOST }}/health || exit 1
          echo "Deployment successful!"

#### 方法2: コード直接デプロイ（非Docker）

`.github/workflows/deploy-direct.yml`を作成：

name: Deploy Python App Directly

on:
  push:
    branches:
      - main

jobs:
  deploy:
    name: Deploy to ECS
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup SSH Key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.ECS_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H ${{ secrets.ECS_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy Application
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.ECS_USERNAME }}@${{ secrets.ECS_HOST }} << 'EOF'
            # アプリケーションディレクトリに移動
            cd /opt/tornado-app || mkdir -p /opt/tornado-app && cd /opt/tornado-app

            # Gitリポジトリをクローン/更新
            if [ -d .git ]; then
              git pull origin main
            else
              git clone https://github.com/your-username/your-repo.git .
            fi

            # Python仮想環境を作成/有効化
            python3 -m venv venv
            source venv/bin/activate

            # 依存関係をインストール
            pip install --upgrade pip
            pip install -r requirements.txt

            # 既存プロセスを停止
            pkill -f "python.*app.py" || true

            # 環境変数を設定してアプリケーションを起動
            export MONGODB_URI="${{ secrets.MONGODB_URI }}"
            export ENVIRONMENT="production"
            nohup python app.py > /var/log/tornado-app.log 2>&1 &

            echo "Application deployed successfully"
          EOF

      - name: Verify Deployment
        run: |
          sleep 10
          curl -f http://${{ secrets.ECS_HOST }}:8888/health || exit 1

---

## 5. デプロイスクリプトの作成

### 5.1 Dockerfileの作成

プロジェクトルートに`Dockerfile`を作成：

# ベースイメージ
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係のインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーを作成して切り替え
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ポートを公開
EXPOSE 8888

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health')" || exit 1

# アプリケーション起動
CMD ["python", "app.py"]

### 5.2 .dockerignoreの作成

# Git関連
.git
.gitignore
.github

# Python関連
__pycache__
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# テスト・開発関連
tests/
.pytest_cache/
.coverage
htmlcov/

# ドキュメント
README.md
docs/

# IDE設定
.vscode/
.idea/
*.swp

### 5.3 docker-compose.ymlの作成（ローカル開発用）

version: '3.8'

services:
  app:
    build: .
    ports:
      - "8888:8888"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/tornado_db
      - ENVIRONMENT=development
    depends_on:
      - mongodb
    volumes:
      - .:/app
    restart: unless-stopped

  mongodb:
    image: mongo:4.4
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

volumes:
  mongodb_data:

### 5.4 アプリケーション設定例

`config.py`を作成して環境変数を管理：

import os

class Config:
    # MongoDB設定
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/tornado_db')

    # アプリケーション設定
    PORT = int(os.getenv('PORT', 8888))
    DEBUG = os.getenv('ENVIRONMENT', 'development') != 'production'

    # セキュリティ設定
    COOKIE_SECRET = os.getenv('COOKIE_SECRET', 'your-secret-key-change-in-production')
    XSRF_COOKIES = True

config = Config()

`app.py`の例：

import tornado.ioloop
import tornado.web
import motor.motor_tornado
from config import config

class HealthHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({"status": "healthy", "service": "tornado-app"})

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello from Tornado on Alibaba Cloud!")

def make_app():
    # MongoDBクライアント初期化
    client = motor.motor_tornado.MotorClient(config.MONGODB_URI)
    db = client.get_default_database()

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/health", HealthHandler),
    ],
    debug=config.DEBUG,
    cookie_secret=config.COOKIE_SECRET,
    xsrf_cookies=config.XSRF_COOKIES,
    db=db
    )

if __name__ == "__main__":
    app = make_app()
    app.listen(config.PORT)
    print(f"Server running on port {config.PORT}")
    tornado.ioloop.IOLoop.current().start()

### 5.5 requirements.txtの例

tornado==6.4
motor==3.3.2
pymongo==4.6.1
python-dotenv==1.0.0

---

## 6. CI/CDパイプラインのテスト

### 6.1 ローカルでのDockerビルドテスト

# イメージをビルド
docker build -t tornado-app:test .

# コンテナを実行
docker run -d \
  --name tornado-test \
  -p 8888:8888 \
  -e MONGODB_URI="mongodb://localhost:27017/test_db" \
  tornado-app:test

# ヘルスチェック
curl http://localhost:8888/health

# ログ確認
docker logs tornado-test

# クリーンアップ
docker stop tornado-test
docker rm tornado-test

### 6.2 GitHub Actionsワークフローのトリガー

# 変更をコミット
git add .
git commit -m "Add CI/CD pipeline"
git push origin main

### 6.3 デプロイ状況の確認

1. **GitHubリポジトリ** > **Actions**タブでワークフロー実行状況を確認
2. **各ジョブのログを確認**：
   - Test: テスト結果
   - Build: Dockerイメージビルド状況
   - Deploy: デプロイ実行結果

3. **ECSインスタンスで確認**：
# ECSにSSH接続
ssh root@<ECS-PUBLIC-IP>

# 実行中のコンテナ確認
docker ps

# ログ確認
docker logs tornado-app

# アプリケーションテスト
curl http://localhost/health

---

## 7. トラブルシューティング

### 7.1 よくある問題と解決方法

#### 問題1: ACRへのログインに失敗

**エラーメッセージ：**
Error response from daemon: Get https://registry.ap-northeast-1.aliyuncs.com/v2/: unauthorized

**解決方法：**
1. AccessKey IDとSecretが正しいか確認
2. RAMユーザーに`AliyunContainerRegistryFullAccess`ポリシーが付与されているか確認
3. ACRリージョンがECSリージョンと一致しているか確認

# 手動ログインテスト
docker login --username=<AccessKey-ID> registry.ap-northeast-1.aliyuncs.com

#### 問題2: SSH接続が失敗

**エラーメッセージ：**
Permission denied (publickey)

**解決方法：**
1. SSH秘密鍵が正しくGitHub Secretsに設定されているか確認
2. ECSインスタンスの`~/.ssh/authorized_keys`に公開鍵が追加されているか確認
3. ファイルパーミッションを確認：

# ECS上で実行
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

#### 問題3: MongoDBへの接続エラー

**エラーメッセージ：**
pymongo.errors.ServerSelectionTimeoutError: connection refused

**解決方法：**
1. MONGODB_URIが正しいか確認
2. MongoDBが起動しているか確認：
# Dockerの場合
docker ps | grep mongo

# MongoDBの接続テスト
mongosh "mongodb://username:password@host:port/database"

3. ファイアウォール/セキュリティグループ設定を確認
4. VPC内部接続の場合、プライベートIPアドレスを使用

#### 問題4: デプロイ後にアプリケーションが起動しない

**解決方法：**
# コンテナログを確認
docker logs tornado-app

# コンテナ内に入って調査
docker exec -it tornado-app /bin/bash

# アプリケーションを手動起動してエラーを確認
python app.py

### 7.2 デバッグコマンド集

# GitHub Actionsのローカルテスト（act使用）
act -s ALIBABA_ACCESS_KEY_ID=xxx -s ALIBABA_ACCESS_KEY_SECRET=xxx

# Dockerイメージのレイヤー確認
docker history tornado-app:latest

# コンテナリソース使用状況
docker stats tornado-app

# ネットワーク接続テスト
docker exec tornado-app ping mongodb

# Alibaba Cloud CLIでECS情報取得
aliyun ecs DescribeInstances --RegionId ap-northeast-1

---

## 8. 運用のベストプラクティス

### 8.1 セキュリティ

#### Secrets管理
- **GitHub Secretsを使用**：機密情報をコードに含めない
- **定期的なローテーション**：AccessKeyを3ヶ月ごとに更新
- **最小権限の原則**：RAMユーザーに必要最小限の権限のみ付与

#### ネットワークセキュリティ
# ECSセキュリティグループで不要なポートを閉じる
# SSH接続は特定のIPアドレスからのみ許可

# SSL/TLS証明書の設定（Nginx経由）
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://localhost:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

### 8.2 モニタリングとロギング

#### CloudMonitorの設定
1. **Alibaba Cloud CloudMonitor**で以下のメトリクスを監視：
   - CPU使用率
   - メモリ使用率
   - ネットワークトラフィック
   - ディスクI/O

#### ログ収集
# docker-compose.ymlにログドライバーを追加
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

**Alibaba Cloud Log Serviceとの統合：**
# Docker起動時にログドライバーを指定
docker run -d \
  --log-driver=syslog \
  --log-opt syslog-address=tcp://log-service-endpoint:514 \
  tornado-app:latest

### 8.3 バックアップ戦略

#### MongoDBバックアップ
# 自動バックアップスクリプト（cron設定）
# /etc/cron.daily/mongodb-backup.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mongodb"
mongodump --uri="mongodb://username:password@host:port/database" \
  --out="${BACKUP_DIR}/backup_${DATE}"

# 7日以上前のバックアップを削除
find ${BACKUP_DIR} -type d -mtime +7 -exec rm -rf {} \;

#### ECSスナップショット
- **Alibaba Cloudコンソール**から定期的にディスクスナップショットを作成
- **自動スナップショットポリシー**を設定

### 8.4 スケーリング戦略

#### 水平スケーリング（複数ECSインスタンス）
# 複数インスタンスへのデプロイ
deploy:
  strategy:
    matrix:
      host:
        - 192.168.1.100
        - 192.168.1.101
        - 192.168.1.102

#### Server Load Balancer (SLB)の設定
1. **SLBインスタンス**を作成
2. **バックエンドサーバー**としてECSインスタンスを追加
3. **ヘルスチェック**を設定：
   - パス: `/health`
   - 間隔: 30秒
   - タイムアウト: 5秒

### 8.5 環境分離

#### ブランチ戦略
# 環境別デプロイワークフロー
on:
  push:
    branches:
      - main          # 本番環境
      - staging       # ステージング環境
      - develop       # 開発環境

jobs:
  deploy:
    steps:
      - name: Set Environment
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "ENVIRONMENT=production" >> $GITHUB_ENV
            echo "ECS_HOST=${{ secrets.PROD_ECS_HOST }}" >> $GITHUB_ENV
          elif [[ "${{ github.ref }}" == "refs/heads/staging" ]]; then
            echo "ENVIRONMENT=staging" >> $GITHUB_ENV
            echo "ECS_HOST=${{ secrets.STAGING_ECS_HOST }}" >> $GITHUB_ENV
          fi

### 8.6 性能最適化

#### Tornadoの最適化設定
# app.py
import multiprocessing

if __name__ == "__main__":
    app = make_app()

    # プロセス数をCPUコア数に設定
    num_processes = multiprocessing.cpu_count()

    server = tornado.httpserver.HTTPServer(app)
    server.bind(config.PORT)
    server.start(num_processes)  # マルチプロセスモード

    print(f"Server running with {num_processes} processes")
    tornado.ioloop.IOLoop.current().start()

#### MongoDBインデックスの最適化
# 起動時にインデックスを作成
async def setup_indexes(db):
    await db.users.create_index([("email", 1)], unique=True)
    await db.posts.create_index([("created_at", -1)])

---

## 9. まとめ

本手順書では、以下の内容を実装しました：

✅ **Alibaba Cloudリソースの準備**
- RAMユーザーとアクセスキーの設定
- Container Registry (ACR)の構築
- ECSインスタンスとMongoDBのセットアップ

✅ **CI/CDパイプラインの構築**
- GitHub ActionsワークフローによるCI/CD自動化
- Dockerコンテナ化によるポータビリティ向上
- ACRを経由した安全なデプロイメント

✅ **セキュリティとベストプラクティス**
- Secretsの安全な管理
- ネットワークセキュリティの設定
- モニタリングとログ収集

### 次のステップ

1. **本番環境への適用前にステージング環境でテスト**
2. **自動ロールバック機能の実装**
3. **Kubernetes (ACK)への移行検討**（大規模な場合）
4. **CDN（Alibaba Cloud CDN）の統合**（静的コンテンツ配信）

---

## 参考リンク

### Alibaba Cloud公式ドキュメント
- [Alibaba Cloud ECS ドキュメント](https://www.alibabacloud.com/help/en/ecs/)
- [Container Registry (ACR) ガイド](https://www.alibabacloud.com/help/en/acr/)
- [ApsaraDB for MongoDB](https://www.alibabacloud.com/help/en/mongodb/)
- [RAM ユーザーガイド](https://www.alibabacloud.com/help/en/ram/)

### GitHub Actions
- [GitHub Actions 公式ドキュメント](https://docs.github.com/ja/actions)
- [Alibaba Cloud Credentials Action](https://github.com/marketplace/actions/configure-alibaba-cloud-credentials-action-for-github-actions)

### Python/Tornado/MongoDB
- [Tornado ドキュメント](https://www.tornadoweb.org/en/stable/)
- [Motor (非同期MongoDBドライバー)](https://motor.readthedocs.io/)
- [PyMongo ドキュメント](https://pymongo.readthedocs.io/)

---

**作成日**: 2025年11月23日
**バージョン**: 1.0
