# 実装計画

## 概要

この実装計画は、メール認証6桁コードログイン、.envベースアクセス制御、Mini Panel UI、レビュー投稿機能強化を段階的に実装するためのタスク分解です。既存のEmailAuthService、AccessControlMiddleware、ReviewHandlerを拡張し、新しいハンドラーとUIコンポーネントを追加します。

## タスク一覧

- [ ] 1. メール認証6桁コード生成・検証機能の実装
- [ ] 1.1 6桁コード生成機能の実装
  - `EmailAuthService` に `generate_login_code()` メソッドを追加
  - `secrets.randbelow(1000000)` で暗号学的に安全な6桁コード生成
  - 生成したコードをbcryptでハッシュ化
  - MongoDBの `email_verifications` コレクションに保存（有効期限5分、試行回数カウンター付き）
  - コード生成成功時、生成されたコード（平文）と有効期限を返す
  - _Requirements: 1.2, 1.6, 7.1, 7.2_

- [ ] 1.2 6桁コード検証機能の実装
  - `EmailAuthService` に `verify_login_code()` メソッドを追加
  - MongoDBから該当メールアドレスのハッシュ化コードを取得
  - `bcrypt.checkpw()` で入力コードとハッシュを照合
  - 有効期限チェック（5分以内）
  - 試行回数チェック（最大3回）
  - 検証成功時、ユーザー情報（identity_id, email）を返す
  - 検証失敗時、試行回数をインクリメント
  - _Requirements: 1.3, 1.4, 1.5, 7.2, 7.3_

- [ ] 1.3 6桁コード送信用メールサービス拡張
  - `EmailService` に `send_login_code_email()` メソッドを追加
  - メールテンプレート作成（6桁コードを含む）
  - SMTP経由でメール送信（タイムアウト10秒）
  - 送信成功/失敗をログに記録
  - メール送信エラーを適切にハンドリング（ユーザーフレンドリーなエラーメッセージ）
  - _Requirements: 1.2, 2.2, 2.3, 2.4, 7.4_

- [ ] 2. メール認証ログインハンドラーの実装
- [ ] 2.1 メールアドレス入力とコード送信ハンドラーの作成
  - `EmailLoginHandler` を新規作成（GET/POSTメソッド）
  - GETでメールアドレス入力フォームを表示
  - POSTでメールアドレスを受け取り、バリデーション
  - `IdentityService` でメールアドレスの存在確認
  - `EmailAuthService.generate_login_code()` で6桁コード生成
  - `EmailService.send_login_code_email()` でコード送信
  - コード入力画面にリダイレクト（`/auth/email/login?step=code&email={email}`）
  - _Requirements: 1.1, 1.2_

- [ ] 2.2 6桁コード入力フォーム表示機能の実装
  - `EmailLoginHandler.get()` メソッドに `step=code` パラメータ処理を追加
  - コード入力フォームをレンダリング（6桁数字入力、カウントダウンタイマー表示）
  - マスキングされたメールアドレス表示（例: `ab***@example.com`）
  - コード再送信ボタンの配置
  - _Requirements: 1.2, 1.5_

- [ ] 2.3 6桁コード検証ハンドラーの作成
  - `EmailCodeVerificationHandler` を新規作成（POSTメソッド）
  - メールアドレスと6桁コードを受け取り
  - `EmailAuthService.verify_login_code()` でコード検証
  - 検証成功時、`OAuthSessionService.create_oauth_session()` でセッション作成
  - セッションIDをSecure Cookieに設定
  - ログイン成功レスポンスを返す（ホームページへのリダイレクトURL含む）
  - 検証失敗時、エラーメッセージ表示と再入力プロンプト
  - _Requirements: 1.3, 1.4, 7.5_

- [ ] 2.4 コード再送信ハンドラーの作成
  - `EmailCodeResendHandler` を新規作成（POSTメソッド）
  - メールアドレスを受け取り
  - 新しい6桁コードを生成・送信（タスク1.1、1.3と同じロジック）
  - コード入力画面にリダイレクト
  - _Requirements: 1.5_

- [ ] 3. SMTP設定テスト機能の実装
- [ ] 3.1 SMTP接続テスト機能の実装
  - `EmailService` に `test_smtp_connection()` メソッドを追加
  - .envからSMTP設定（ホスト、ポート、ユーザー名、パスワード）を読み込み
  - SMTP接続を試行（タイムアウト10秒）
  - 接続成功/失敗を返す（詳細なエラー情報含む）
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 3.2 SMTP設定検証とログ記録の実装
  - システム起動時に `EmailService.test_smtp_connection()` を呼び出し
  - SMTP設定が不完全な場合、警告メッセージをログに記録
  - SMTP接続成功時、情報ログを記録
  - SMTP接続失敗時、詳細なエラーログを記録
  - _Requirements: 2.1, 2.3, 2.4, 2.5, 7.4_

- [ ] 3.3 SMTP手動テストエンドポイントの作成
  - `SMTPTestHandler` を新規作成（POSTメソッド、開発・デバッグ用）
  - オプションでテストメールアドレスを受け取り
  - `EmailService.test_smtp_connection()` で接続テスト実行
  - テストメールを送信（アドレス指定時）
  - テスト結果をJSONで返す（成功/失敗、接続情報、エラー詳細）
  - _Requirements: 2.2_

- [ ] 4. アクセス制御とMini Panel連携の実装
- [x] 4.1 アクセス制御ルールの.env設定読み込み確認
  - 既存の `AccessControlMiddleware.load_access_control_rules()` が正しく動作することを確認
  - `/reviews/new,user` ルールを.env.exampleに追加
  - `/edit,user` ルールを.env.exampleに追加
  - ルール読み込みログが正しく記録されることを確認
  - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.7_

- [x] 4.2 レビュー投稿ハンドラーのアクセス制御統合
  - `ReviewCreateHandler.get()` メソッドの先頭に認証チェックを追加
  - `AccessControlMiddleware.check_access()` を呼び出し
  - 未認証の場合、`show_login_panel=True` でテンプレートをレンダリング
  - 認証済みの場合、`review_form_visible=True` でレビューフォームを表示
  - _Requirements: 3.5, 3.8, 5.1, 5.2, 5.4_

- [x] 4.3 レビュー編集ハンドラーのアクセス制御統合
  - `ReviewEditHandler` に同様の認証チェックを追加
  - アクセス制御結果に基づいてMini Panel表示を制御
  - _Requirements: 3.5, 3.8, 5.5_

- [ ] 5. Mini Panel UI の実装
- [x] 5.1 Mini Panel HTML構造の作成
  - `templates/base.html` に Mini Panel HTMLを追加
  - パネルヘッダー（タイトル "Sign in to DXEEWorld"、閉じるボタン）
  - 認証オプション（Googleボタン、Facebookボタン、Email入力、"Sign in with Email" ボタン）
  - 登録リンク（"Don't have an account? Register"）
  - 初期状態は非表示（`display: none`）
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 5.2 Mini Panel CSSスタイルの実装
  - `static/css/login-panel.css` を新規作成
  - 右下固定配置（fixed position）、角丸、ダークモード背景
  - Googleボタン（白背景、Googleアイコン）、Facebookボタン（ダークブルー背景、Facebookアイコン）
  - Email入力フィールドとボタンのスタイル
  - モバイル対応（画面幅768px以下で画面中央に表示）
  - shadow効果、適度なpadding
  - _Requirements: 4.2, 4.7_

- [ ] 5.3 Mini Panel JavaScript制御の実装
  - `static/js/login-panel.js` を新規作成
  - `LoginPanel` クラスを実装（show/hide メソッド）
  - `loginWithEmail()` メソッド: Email入力値を取得し、`/auth/email/login` にPOST
  - `loginWithGoogle()` メソッド: 既存Google認証フローへリダイレクト
  - `loginWithFacebook()` メソッド: 既存Facebook認証フローへリダイレクト
  - 閉じるボタンと外側クリックでパネルを非表示
  - テンプレート変数 `show_login_panel` に基づいて自動表示
  - _Requirements: 4.1, 4.3, 4.4, 4.5, 4.6_

- [ ] 5.4 認証処理中のローディングインジケーター実装
  - Mini Panel内にローディングスピナーを追加
  - 認証API呼び出し中にスピナーを表示
  - 認証完了/失敗時にスピナーを非表示
  - _Requirements: 4.8_

- [ ] 6. レビュー投稿フォーム表示制御の実装
- [ ] 6.1 レビュー投稿テンプレートの更新
  - `templates/reviews/create.html` を更新
  - `show_login_panel` 変数を受け取り
  - `show_login_panel=True` の場合、レビューフォームを非表示
  - `show_login_panel=False` の場合、レビューフォームを表示
  - Mini Panelはbase.htmlで自動表示される
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 6.2 レビュー編集テンプレートの更新
  - `templates/reviews/edit.html` にも同様の制御を追加
  - 未認証時はMini Panel表示、編集フォーム非表示
  - _Requirements: 5.5_

- [ ] 7. 会社詳細ページレビュー投稿リンクの実装
- [ ] 7.1 会社詳細ハンドラーのテンプレートデータ拡張
  - `CompanyDetailHandler.get()` メソッドを更新
  - レビュー件数を取得（`review_count = len(reviews)`）
  - テンプレートデータに `show_review_link` と `review_count` を追加
  - `show_review_link = review_count > 0` のロジック
  - _Requirements: 6.1, 6.6_

- [ ] 7.2 会社詳細テンプレートへのレビュー投稿リンク追加
  - `templates/companies/detail.html` を更新
  - レビューセクションの上部に条件付きでリンクを表示
  - `review_count > 0` の場合、"Reviewを投稿する" リンク
  - `review_count == 0` の場合、"最初のReviewを投稿する" リンク
  - リンク先: `/companies/{company_id}/reviews/new`
  - _Requirements: 6.1, 6.2, 6.6_

- [ ] 7.3 複数レビュー投稿の制約解除確認
  - 既存のレビュー投稿ロジックで、同一ユーザー・同一会社の複数レビュー投稿が許可されていることを確認
  - 必要に応じて制約を解除（通常は既存実装で問題なし）
  - レビュー投稿完了後、会社詳細ページにリダイレクト
  - _Requirements: 6.5, 6.7_

- [ ] 8. エラーハンドリングとセキュリティ強化
- [ ] 8.1 ログイン試行回数制限の実装
  - `EmailAuthService.verify_login_code()` に試行回数チェックを追加
  - 3回失敗後、該当コードを無効化
  - 5回連続失敗後（複数コード）、アカウント一時ロック機能を実装
  - ロック解除は一定時間経過後（例: 15分）
  - _Requirements: 7.3_

- [ ] 8.2 アクセス制御エラーハンドリングの強化
  - `.env` 設定パースエラー時、デフォルトルール（全URL認証要求）を適用
  - 設定エラーをログに詳細記録
  - 権限不足エラー（403）の適切なレスポンス
  - _Requirements: 3.4, 3.10, 7.6_

- [ ] 8.3 セッション管理のセキュリティ確認
  - セッションIDが暗号化され、適切な有効期限が設定されていることを確認
  - 無効なセッションでのアクセス時、セッションクリアとログイン要求
  - セキュアCookie設定（Secure、HttpOnly、SameSite）を確認
  - _Requirements: 7.5, 7.7_

- [ ] 8.4 エラーログとユーザーメッセージの統一
  - すべてのエラーで詳細ログ記録とユーザーフレンドリーメッセージを提供
  - SMTP接続エラー: ログに詳細記録、ユーザーには一般的メッセージ
  - 認証失敗: ログに試行回数記録、ユーザーには再試行ガイダンス
  - _Requirements: 2.3, 2.4, 7.4_

- [ ] 9. ルーティング設定とシステム統合
- [ ] 9.1 新規ハンドラーのルーティング追加
  - `app.py` に以下のルートを追加:
    - `/auth/email/login` → `EmailLoginHandler`
    - `/auth/email/verify-code` → `EmailCodeVerificationHandler`
    - `/auth/email/resend-code` → `EmailCodeResendHandler`
    - `/admin/smtp-test` → `SMTPTestHandler`
  - 既存のレビュー投稿・編集ルートは変更なし
  - _Requirements: すべての新規ハンドラー_

- [ ] 9.2 .env設定ファイルの更新
  - `.env.example` にアクセス制御ルールの例を追加:
    - `ACCESS_CONTROL_RULES=/companies/([^/]+)/reviews/new,user;/reviews/([^/]+)/edit,user`
  - SMTP設定の例を確認（既存）
  - 本番環境用の`.env`ファイルに実際のルールを設定
  - _Requirements: 2.1, 3.1_

- [ ] 9.3 静的ファイルの統合
  - `login-panel.css` を `base.html` で読み込み
  - `login-panel.js` を `base.html` で読み込み
  - Googleアイコン、Facebookアイコンを `static/images/` に配置
  - _Requirements: 4.2, 4.3_

- [ ] 10. テストの実装
- [ ] 10.1 ユニットテストの作成
  - `test_email_auth_service.py`: `generate_login_code()`, `verify_login_code()` のテスト
  - `test_email_service.py`: `send_login_code_email()`, `test_smtp_connection()` のテスト
  - `test_access_control_middleware.py`: URLマッチング、設定パースのテスト
  - bcryptハッシュ化、有効期限、試行回数制限の動作確認
  - _Requirements: すべてのビジネスロジック_

- [ ] 10.2 統合テストの作成
  - メール認証ログイン完全フロー（メールアドレス入力 → コード送信 → コード検証 → セッション作成）
  - アクセス制御フロー（未認証アクセス → Mini Panel表示 → 認証 → フォーム表示）
  - レビュー投稿リンククリック → レビュー投稿ページ遷移
  - _Requirements: すべてのエンドツーエンドフロー_

- [ ] 10.3 E2Eテストの作成
  - ブラウザ自動化テスト（Selenium/Playwright）
  - 未認証ユーザーがレビュー投稿ページにアクセス → Mini Panel表示確認
  - Email認証フロー完全実行（モックSMTP使用）
  - モバイル表示テスト（Mini Panelの位置確認）
  - _Requirements: すべてのユーザーインタラクション_

## 実装順序の理由

1. **タスク1-2**: コア機能（6桁コード生成・検証、メール送信）を最初に実装し、他のタスクの基盤を構築
2. **タスク3**: SMTP設定テストで、メール送信機能の信頼性を早期に確保
3. **タスク4**: アクセス制御とハンドラー統合で、Mini Panel表示の条件を確立
4. **タスク5**: Mini Panel UIを実装し、ユーザー認証フローを完成
5. **タスク6-7**: レビュー投稿関連の機能強化（フォーム表示制御、投稿リンク）
6. **タスク8**: セキュリティとエラーハンドリングで、実装全体を強化
7. **タスク9**: ルーティングとシステム統合で、すべての機能を接続
8. **タスク10**: テストで、すべての要件が満たされていることを検証

## 要件カバレッジマトリクス

| 要件 | 対応タスク |
|------|-----------|
| 1.1 | 2.1 |
| 1.2 | 1.1, 1.3, 2.1 |
| 1.3 | 1.2, 2.3 |
| 1.4 | 1.2, 2.3 |
| 1.5 | 1.2, 2.2, 2.4 |
| 1.6 | 1.1 |
| 2.1 | 3.1, 3.2, 9.2 |
| 2.2 | 1.3, 3.1, 3.3 |
| 2.3 | 1.3, 3.1, 3.2, 8.4 |
| 2.4 | 1.3, 3.2, 8.4 |
| 2.5 | 3.2 |
| 3.1 | 4.1, 9.2 |
| 3.2 | 4.1 |
| 3.3 | 4.1 |
| 3.4 | 8.2 |
| 3.5 | 4.2, 4.3 |
| 3.6 | 4.1 |
| 3.7 | 4.1 |
| 3.8 | 4.2, 4.3 |
| 3.9 | (既存実装) |
| 3.10 | 8.2 |
| 3.11 | (既存実装) |
| 3.12 | (既存実装) |
| 3.13 | (既存実装) |
| 4.1 | 5.1, 5.3 |
| 4.2 | 5.1, 5.2 |
| 4.3 | 5.1, 5.3 |
| 4.4 | 5.3 |
| 4.5 | 5.3 |
| 4.6 | 5.3 |
| 4.7 | 5.2 |
| 4.8 | 5.4 |
| 5.1 | 4.2, 6.1 |
| 5.2 | 4.2, 6.1 |
| 5.3 | 6.1 |
| 5.4 | 4.2 |
| 5.5 | 4.3, 6.2 |
| 6.1 | 7.1, 7.2 |
| 6.2 | 7.2 |
| 6.3 | (Mini Panel機能で実現) |
| 6.4 | (Mini Panel機能で実現) |
| 6.5 | 7.3 |
| 6.6 | 7.1, 7.2 |
| 6.7 | 7.3 |
| 7.1 | 1.1 |
| 7.2 | 1.1, 1.2 |
| 7.3 | 1.2, 8.1 |
| 7.4 | 1.3, 3.2, 8.4 |
| 7.5 | 2.3, 8.3 |
| 7.6 | 8.2 |
| 7.7 | 8.3 |
