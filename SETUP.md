# DXEEWorld 環境設定ガイド

## 概要

このドキュメントは、DXEEWorldの開発環境セットアップとOAuth認証設定の手順を説明します。

## 基本環境設定

### 1. 前提条件

- Python 3.10以上
- MongoDB 4.4以上
- Git

### 2. プロジェクトのクローンと依存関係インストール

```bash
git clone <repository-url>
cd dxeeworld
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`を`.env`にコピーして設定を編集：

```bash
cp .env.example .env
```

## OAuth認証設定

### Google OAuth 2.0 設定

1. **Google Cloud Consoleでプロジェクト作成**
   - https://console.developers.google.com/ にアクセス
   - 新しいプロジェクトを作成または既存プロジェクトを選択

2. **OAuth 2.0 認証情報の作成**
   - 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
   - アプリケーションの種類：「ウェブアプリケーション」
   - 承認済みのリダイレクト URI: `http://localhost:8202/auth/google/callback`

3. **環境変数の設定**
   ```env
   GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8202/auth/google/callback
   GOOGLE_OAUTH_ENABLED=True
   ```

### Facebook OAuth 設定

1. **Facebook Developersでアプリ作成**
   - https://developers.facebook.com/ にアクセス
   - 「マイアプリ」→「アプリを作成」
   - アプリタイプ：「コンシューマー」

2. **Facebook Loginの設定**
   - 製品追加で「Facebook Login」を選択
   - 設定で有効なOAuthリダイレクトURI: `http://localhost:8202/auth/facebook/callback`

3. **環境変数の設定**
   ```env
   FACEBOOK_APP_ID=your-app-id
   FACEBOOK_APP_SECRET=your-app-secret
   FACEBOOK_OAUTH_REDIRECT_URI=http://localhost:8202/auth/facebook/callback
   FACEBOOK_OAUTH_ENABLED=True
   ```

### SMTP メール設定（Gmail例）

1. **Googleアカウントでアプリパスワード生成**
   - Googleアカウント設定→セキュリティ→2段階認証プロセス→アプリパスワード
   - アプリを選択し、パスワードを生成

2. **環境変数の設定**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USE_TLS=True
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-generated-app-password
   SMTP_FROM_ADDRESS=noreply@dxeeworld.com
   EMAIL_VERIFICATION_ENABLED=True
   ```

## データベース設定

### MongoDB設定

1. **ローカルMongoDB起動**
   ```bash
   # macOS (Homebrew)
   brew services start mongodb-community

   # Ubuntu/Debian
   sudo systemctl start mongod

   # Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

2. **環境変数の設定**
   ```env
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB_NAME=dxeeworld
   ```

## アプリケーション起動

```bash
python run_server.py
```

アプリケーションは http://localhost:8202 で利用可能になります。

## トラブルシューティング

### OAuth認証エラー

**問題**: 「OAuth設定が不完全です」エラー
**解決策**:
- 環境変数が正しく設定されているか確認
- OAuth設定で`*_OAUTH_ENABLED=True`になっているか確認
- リダイレクトURIがOAuthプロバイダー設定と一致しているか確認

**問題**: Google OAuth認証に失敗
**解決策**:
- Google Cloud ConsoleでOAuth同意画面が適切に設定されているか確認
- スコープに`email`と`profile`が含まれているか確認
- テストユーザーとして自分のアカウントを追加

### データベース接続エラー

**問題**: 「データベース接続に失敗しました」
**解決策**:
- MongoDBサービスが起動しているか確認: `brew services list | grep mongodb`
- MongoDB接続文字列が正しいか確認
- ネットワーク設定でMongoDB（27017ポート）がブロックされていないか確認

### メール送信エラー

**問題**: メール認証が送信されない
**解決策**:
- SMTP設定が正しいか確認
- Gmailの場合、2段階認証が有効でアプリパスワードを使用しているか確認
- ファイアウォールでSMTPポート（587）がブロックされていないか確認

### セキュリティ設定

本番環境では以下の設定を変更してください：

```env
DEBUG=False
SECRET_KEY=truly-random-secret-key-minimum-32-characters
JWT_SECRET=another-random-secret-key
```

## 開発環境での確認

1. **OAuth機能テスト**
   - `/auth/login`ページでOAuthボタンが表示されることを確認
   - 各OAuth認証フローが正常に動作することを確認

2. **メール機能テスト**
   - ユーザー登録でメール認証が送信されることを確認
   - メール内のリンクで認証が完了することを確認

3. **レビュー機能テスト**
   - レビュー投稿ページで企業名が正しく表示されることを確認
   - レビュー投稿が正常に完了することを確認