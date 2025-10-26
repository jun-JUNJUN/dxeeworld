# Requirements Document

## Introduction
DXEEWorldのレビューフォームにおいて、現在DeepSeek LLMを使用しているテキスト翻訳機能をDeepL Translation APIに置き換えます。DeepLは専門的な翻訳サービスであり、より高品質で自然な翻訳結果が期待できます。この変更により、ユーザーは多言語レビュー投稿時により正確な翻訳プレビューを確認できるようになり、グローバルなスタートアップレビュープラットフォームとしての品質向上を実現します。

現在の実装ではDeepSeek Chat Completions APIを使用してプロンプトベースの翻訳を行っていますが、これをDeepL専用の翻訳APIに置き換えることで、翻訳品質の向上、レスポンス速度の改善、およびコスト最適化を図ります。

## Requirements

### Requirement 1: DeepL API統合によるTranslationServiceの置き換え
**Objective:** As a システム管理者, I want TranslationServiceをDeepSeek APIからDeepL APIに置き換える, so that より高品質で自然な翻訳結果をユーザーに提供できる

#### Acceptance Criteria

1. WHEN TranslationServiceが初期化される THEN Translation Service SHALL DeepL API認証キーを環境変数`DEEPL_API_KEY`から読み込む
2. IF 環境変数`DEEPL_API_KEY`が設定されていない THEN Translation Service SHALL ValueError例外を発生させ、明確なエラーメッセージを提供する
3. WHEN TranslationServiceが初期化される THEN Translation Service SHALL DeepL APIクライアント（httpx.AsyncClient）を適切なベースURL（https://api-free.deepl.com/v2 または https://api.deepl.com/v2）で構成する
4. WHEN TranslationServiceがインスタンス化される THEN Translation Service SHALL API認証ヘッダー（Authorization: DeepL-Auth-Key）を設定する
5. WHEN TranslationServiceが破棄される THEN Translation Service SHALL HTTPクライアントリソースを適切にクローズする

### Requirement 2: 翻訳メソッドのDeepL API対応
**Objective:** As a 開発者, I want translate_textメソッドとtranslate_batchメソッドがDeepL APIを使用するように実装される, so that 既存のコードインターフェースを維持しながらDeepL翻訳を利用できる

#### Acceptance Criteria

1. WHEN translate_textメソッドが呼び出される THEN Translation Service SHALL DeepL API `/v2/translate` エンドポイントにPOSTリクエストを送信する
2. WHEN translate_textメソッドがDeepL APIを呼び出す THEN Translation Service SHALL 以下のパラメータを送信する：text（翻訳対象テキスト）、source_lang（元言語コード）、target_lang（翻訳先言語コード）
3. IF source_langとtarget_langが同じである THEN Translation Service SHALL API呼び出しをスキップし、元のテキストをそのまま返す
4. IF 翻訳対象テキストが空または空白のみである THEN Translation Service SHALL API呼び出しをスキップし、空文字列を返す
5. WHEN DeepL APIから正常なレスポンスが返される THEN Translation Service SHALL translations[0].textフィールドから翻訳テキストを抽出し、Result.success()で返す
6. WHEN translate_batchメソッドが呼び出される THEN Translation Service SHALL 各テキストに対してtranslate_textを順次呼び出す
7. IF translate_batch中に個別の翻訳が失敗する THEN Translation Service SHALL 失敗したテキストを元のテキストのまま含め、処理を継続する（Graceful Degradation）

### Requirement 3: サポート言語の維持と拡張
**Objective:** As a ユーザー, I want 日本語、英語、中国語の翻訳をサポートする, so that 既存の多言語レビューフォーム機能を継続して利用できる

#### Acceptance Criteria

1. WHEN Translation Serviceが言語サポートを定義する THEN Translation Service SHALL 最低限、日本語（JA）、英語（EN）、中国語（ZH）をサポートする
2. WHEN translate_textが呼び出される AND source_langがサポート対象外である THEN Translation Service SHALL Result.failure()でTranslationErrorを返す
3. WHEN translate_textが呼び出される AND target_langがサポート対象外である THEN Translation Service SHALL Result.failure()でTranslationErrorを返す
4. WHEN is_language_supportedメソッドが呼び出される THEN Translation Service SHALL 指定された言語コードがサポートされているかをブール値で返す
5. WHEN get_supported_languagesメソッドが呼び出される THEN Translation Service SHALL サポートされている言語コードと言語名のマッピングを返す
6. WHERE DeepL APIが言語コードとして大文字を要求する（例: JA, EN, ZH） THE Translation Service SHALL 小文字の言語コード（ja, en, zh）を大文字に変換してAPIに送信する

### Requirement 4: エラーハンドリングとリトライロジック
**Objective:** As a システム管理者, I want DeepL API特有のエラーを適切に処理し、一時的な障害に対してリトライする, so that システムの可用性と信頼性を確保できる

#### Acceptance Criteria

1. WHEN DeepL APIが429（Rate Limit Exceeded）を返す THEN Translation Service SHALL APIRateLimitErrorをResult.failure()で返す
2. WHEN DeepL APIが403（Quota Exceeded）を返す THEN Translation Service SHALL TranslationError（"API quota exceeded"）をResult.failure()で返す
3. WHEN DeepL APIが456（Quota Exceeded）を返す THEN Translation Service SHALL TranslationError（"API quota exceeded"）をResult.failure()で返す
4. WHEN DeepL APIがタイムアウトエラー（408, 504）を返す AND リトライ回数が最大値未満である THEN Translation Service SHALL 指数バックオフでAPIリクエストを再試行する
5. WHEN DeepL APIがタイムアウトエラーを返す AND リトライ回数が最大値（MAX_RETRIES=2）に達した THEN Translation Service SHALL APITimeoutErrorをResult.failure()で返す
6. WHEN httpx.TimeoutExceptionが発生する AND リトライ回数が最大値未満である THEN Translation Service SHALL APIリクエストを再試行する
7. WHEN httpx.RequestErrorが発生する THEN Translation Service SHALL TranslationError（"API request error"）をResult.failure()で返す
8. WHEN 予期しない例外が発生する THEN Translation Service SHALL 例外をログに記録し、TranslationErrorをResult.failure()で返す
9. WHERE 翻訳エラーが発生した場合 THE Translation Service SHALL logger.exception()を使用してスタックトレースを含む詳細なログを記録する

### Requirement 5: 環境変数と設定の更新
**Objective:** As a システム管理者, I want DeepL API用の環境変数を設定し、DeepSeek関連の設定を削除する, so that システムが正しい翻訳APIを使用する

#### Acceptance Criteria

1. WHEN システムが起動する THEN システム SHALL 環境変数`DEEPL_API_KEY`の存在を確認する
2. WHEN .env.exampleファイルが参照される THEN .env.example SHALL DEEPL_API_KEY設定例を含み、DEEPSEEK_API_KEY設定例を削除する
3. WHEN TranslationServiceがインスタンス化される THEN Translation Service SHALL 環境変数`DEEPSEEK_API_KEY`を参照しない
4. WHEN 開発者がドキュメントを参照する THEN ドキュメント SHALL DeepL APIキーの取得方法と設定手順を明記する
5. WHERE DeepL APIには無料版（api-free.deepl.com）と有料版（api.deepl.com）がある THE 設定ドキュメント SHALL 両方のAPIエンドポイントの違いと選択方法を説明する

### Requirement 6: 既存テストの更新とDeepL API対応
**Objective:** As a 開発者, I want TranslationServiceのユニットテストがDeepL APIのモックを使用する, so that CI/CDパイプラインで翻訳機能を継続的にテストできる

#### Acceptance Criteria

1. WHEN test_translation_service.pyが実行される THEN テストスイート SHALL DeepSeek APIモックをDeepL APIモックに置き換える
2. WHEN translate_textメソッドのテストが実行される THEN テスト SHALL DeepL API `/v2/translate` エンドポイントのレスポンス形式（{"translations": [{"text": "..."}]}）をモックする
3. WHEN batch翻訳テストが実行される THEN テスト SHALL 各翻訳呼び出しが順次実行されることを検証する
4. WHEN APIエラーテストが実行される THEN テスト SHALL DeepL特有のエラーステータスコード（403, 456）をカバーする
5. WHEN タイムアウトテストが実行される THEN テスト SHALL リトライロジックが正しく動作することを検証する
6. WHEN 全テストが実行される THEN テストスイート SHALL 既存のテストケースの合格基準を維持する

### Requirement 7: レビューハンドラー統合の維持
**Objective:** As a ユーザー, I want レビューフォームでの翻訳機能が引き続き動作する, so that 多言語レビュー投稿時に翻訳プレビューを確認できる

#### Acceptance Criteria

1. WHEN review_handler.pyのReviewCreateHandlerが翻訳を実行する THEN ハンドラー SHALL TranslationServiceの同一インターフェース（translate_text）を使用する
2. WHEN レビュー確認画面が生成される THEN システム SHALL 各コメントカテゴリーに対してDeepL翻訳結果を表示する
3. IF 翻訳が失敗する THEN システム SHALL 元のテキストを表示し、エラーログを記録する（Graceful Degradation）
4. WHEN 複数言語への翻訳が必要である THEN システム SHALL 各ターゲット言語に対してtranslate_textを呼び出す
5. WHEN 翻訳処理が完了する THEN システム SHALL 翻訳結果をテンプレート変数として渡し、確認画面に表示する

### Requirement 8: パフォーマンスと品質の維持
**Objective:** As a ユーザー, I want 翻訳処理が高速かつ高品質である, so that レビュー投稿体験がスムーズである

#### Acceptance Criteria

1. WHEN 翻訳APIが呼び出される THEN Translation Service SHALL 適切なタイムアウト値（30秒）を設定する
2. WHEN 翻訳結果がログに記録される THEN Translation Service SHALL 元テキスト長と翻訳テキスト長を含む情報をlogger.info()で記録する
3. WHEN 複数のカテゴリーコメントが翻訳される THEN システム SHALL 各翻訳を非同期で処理し、全体の処理時間を最小化する
4. WHERE DeepLは翻訳専門APIである THE 翻訳品質 SHALL DeepSeek LLMベースの翻訳と同等以上である
5. WHEN APIレスポンスが返される THEN Translation Service SHALL レスポンスに含まれる使用量情報（detected_source_language等）をログに記録する

### Requirement 9: ドキュメントの更新
**Objective:** As a 開発者・運用担当者, I want DeepL API統合に関するドキュメントが整備されている, so that セットアップ、トラブルシューティング、メンテナンスを円滑に実施できる

#### Acceptance Criteria

1. WHEN TESTING_TRANSLATION_SERVICE.mdが更新される THEN ドキュメント SHALL DeepL APIキーの取得方法を記載する
2. WHEN 技術ドキュメントが更新される THEN tech.md SHALL DeepL Translation API統合を依存関係セクションに記載する
3. WHEN .env.exampleが更新される THEN ファイル SHALL DEEPL_API_KEYの設定例とコメントを含む
4. WHEN README.mdまたはSETUP.mdが参照される THEN ドキュメント SHALL DeepL無料版と有料版の違いを説明する
5. WHERE DeepL無料版には月間50万文字の制限がある THE ドキュメント SHALL 制限に関する情報と有料版へのアップグレード方法を記載する
