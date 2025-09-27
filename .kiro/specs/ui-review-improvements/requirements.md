# Requirements Document

## Introduction
DXEEWorldプラットフォームにおいて、モバイル端末での表示問題の解決、レビュー投稿画面の改善、および認証フローの強化を行う。これにより、全デバイスでの一貫したユーザー体験を提供し、レビュー投稿の利便性を向上させる。

## Requirements

### Requirement 1: モバイル端末での会社一覧表示最適化
**Objective:** As a モバイル端末ユーザー, I want 会社一覧ページのフォームが画面幅内に収まること, so that スクロールなしで検索条件を設定できる

#### Acceptance Criteria
1. WHEN ユーザーがモバイル端末で /companies ページにアクセスする THEN DXEEWorldシステム SHALL フォーム要素を画面幅内に収める
2. WHEN ユーザーがモバイル画面で業界フィルターを選択する THEN DXEEWorldシステム SHALL ドロップダウンを画面幅内に表示する
3. WHEN ユーザーがモバイル画面で企業規模フィルターを選択する THEN DXEEWorldシステム SHALL 選択肢を画面幅内に表示する
4. WHEN ユーザーがモバイル画面でページをリロードする THEN DXEEWorldシステム SHALL フォームレイアウトを画面幅内に維持する
5. WHERE 画面幅が768px以下の端末 THE DXEEWorldシステム SHALL 全フォーム要素を垂直配置で表示する

### Requirement 2: レビュー投稿画面の表示改善
**Objective:** As a レビュー投稿者, I want レビュー投稿画面で正確な企業情報が表示され、十分な入力スペースが確保されること, so that 効率的にレビューを作成できる

#### Acceptance Criteria
1. WHEN ユーザーがレビュー投稿画面にアクセスする THEN DXEEWorldシステム SHALL 対象企業の実際の会社名を表示する
2. WHEN ユーザーがレビュー投稿画面にアクセスする THEN DXEEWorldシステム SHALL 企業所在地の最初のカンマまでの文字列を表示する
3. WHEN ユーザーがPC環境でレビュー投稿画面にアクセスする THEN DXEEWorldシステム SHALL 画面横幅の90%でフォームを表示する
4. IF 企業の所在地データに複数の住所が含まれる THEN DXEEWorldシステム SHALL 最初のカンマより前の部分のみを表示する
5. WHERE レビュー投稿フォーム内 THE DXEEWorldシステム SHALL 企業名を「テスト企業」ではなく実データから取得して表示する

### Requirement 3: 勤務期間入力の改善
**Objective:** As a レビュー投稿者, I want 勤務期間をドロップダウンで選択できること, so that 正確で一貫した期間情報を入力できる

#### Acceptance Criteria
1. WHEN ユーザーがレビュー投稿画面の勤務期間セクションにアクセスする THEN DXEEWorldシステム SHALL 開始年ドロップダウンを表示する
2. WHEN ユーザーが開始年ドロップダウンを操作する THEN DXEEWorldシステム SHALL 1970年から現在年までの選択肢を提供する
3. WHEN ユーザーがレビュー投稿画面の勤務期間セクションにアクセスする THEN DXEEWorldシステム SHALL 終了年ドロップダウンを表示する
4. WHEN ユーザーが終了年ドロップダウンを操作する THEN DXEEWorldシステム SHALL 「現在勤務」および1970年から現在年までの選択肢を提供する
5. WHERE 勤務期間入力エリア THE DXEEWorldシステム SHALL 「勤務期間 [開始年ドロップダウン] ～ [終了年ドロップダウン]」の形式で表示する
6. WHEN ユーザーが終了年で「現在勤務」を選択する THEN DXEEWorldシステム SHALL その選択を現在進行中の勤務として記録する

### Requirement 4: 認証フローの強化
**Objective:** As a 未認証ユーザー, I want レビュー投稿を試みた際に適切な認証画面にリダイレクトされること, so that アカウント作成またはログインを通じてレビュー投稿できる

#### Acceptance Criteria
1. WHEN 未認証ユーザーが企業詳細ページで「Reviewを投稿する」ボタンをクリックする THEN DXEEWorldシステム SHALL ログイン/登録選択画面を表示する
2. WHEN ユーザーがログイン/登録画面にアクセスする THEN DXEEWorldシステム SHALL Googleログインオプションを表示する
3. WHEN ユーザーがログイン/登録画面にアクセスする THEN DXEEWorldシステム SHALL Facebookログインオプションを表示する
4. WHEN ユーザーがログイン/登録画面にアクセスする THEN DXEEWorldシステム SHALL メールアドレス登録オプションを表示する
5. IF OAuthプロバイダーの設定が.envファイルで有効化されている THEN DXEEWorldシステム SHALL 対応するソーシャルログインボタンを有効にする
6. WHERE .env.sampleファイル内 THE DXEEWorldシステム SHALL OAuth設定に必要な環境変数の例を記載する

### Requirement 5: レビューデータモデルの更新
**Objective:** As a システム管理者, I want レビューモデルが新しい勤務期間形式をサポートすること, so that データの整合性を保ちながら機能改善を実装できる

#### Acceptance Criteria
1. WHEN システムがレビューデータを保存する THEN DXEEWorldシステム SHALL 開始年を整数値として記録する
2. WHEN システムがレビューデータを保存する THEN DXEEWorldシステム SHALL 終了年を整数値または「現在勤務」フラグとして記録する
3. WHEN 既存のレビューデータが存在しない THEN DXEEWorldシステム SHALL データ移行を実行せずにモデルを更新する
4. IF ユーザーが「現在勤務」を選択する THEN DXEEWorldシステム SHALL 終了年フィールドをnullまたは特別値として保存する
5. WHILE レビューモデルの更新処理中 THE DXEEWorldシステム SHALL 既存の他のレビューフィールドの構造を保持する

### Requirement 6: 環境設定の文書化
**Objective:** As a 開発者, I want OAuth認証の設定方法が明確に文書化されること, so that 環境構築を正確に実行できる

#### Acceptance Criteria
1. WHEN 開発者が.env.sampleファイルを確認する THEN DXEEWorldシステム SHALL Google OAuth設定例を含む
2. WHEN 開発者が.env.sampleファイルを確認する THEN DXEEWorldシステム SHALL Facebook OAuth設定例を含む
3. WHEN 開発者が.env.sampleファイルを確認する THEN DXEEWorldシステム SHALL SMTP設定例を含む
4. WHERE .env.sampleファイル内 THE DXEEWorldシステム SHALL 各設定項目に説明コメントを付加する
5. IF OAuth設定が不完全な場合 THEN DXEEWorldシステム SHALL 該当するソーシャルログインボタンを無効化または非表示にする