# Implementation Plan

## DeepL Translation API統合タスク

本タスクリストは、既存のTranslationService（DeepSeek LLM使用）をDeepL Translation APIに移行するための実装タスクを定義します。既存のパブリックインターフェースを完全に維持し、内部実装のみを置き換えることで、他のコンポーネントへの影響をゼロにします。

---

- [x] 1. 環境設定とDeepL API準備
- [x] 1.1 DeepL APIアカウントとキーの取得
  - DeepL APIアカウントを作成（無料プランから開始）
  - APIキーを安全に取得し、ローカル環境で保管
  - curlまたはPostmanを使用してAPIキーの動作を検証
  - _Requirements: 7.1, 7.2_
  - **実装メモ**: ユーザーがDeepL APIアカウントを作成し、APIキーを取得する必要があります。

- [x] 1.2 環境変数設定ファイルの更新
  - `.env`ファイルに`DEEPL_API_KEY`を追加
  - `.env`ファイルに`DEEPL_API_BASE_URL`を追加（デフォルト: https://api-free.deepl.com/v2）
  - `.env.example`ファイルを更新し、DeepL API設定例を追加
  - 環境変数が正しく読み込まれることを確認
  - _Requirements: 7.1, 7.4, 7.5, 8.4_
  - **完了**: `.env.example`にDeepL API設定を追加済み

- [x] 2. 翻訳サービスのコア機能実装
- [x] 2.1 TranslationServiceの初期化と設定管理
  - 環境変数からDeepL APIキーを読み込む初期化処理を実装
  - 環境変数からAPI Base URLを読み込む処理を実装（デフォルト値設定）
  - APIキー未設定時にValueError例外を発生させる検証処理を実装
  - httpx.AsyncClientを作成し、適切な認証ヘッダー（DeepL-Auth-Key）を設定
  - タイムアウト設定（30秒）を適用
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.4, 7.5_

- [x] 2.2 言語コード変換と検証機能の実装
  - 日本語、英語、中国語の言語コードマッピング辞書を定義
  - アプリケーション言語コード（ja、en、zh）をDeepL API形式（JA、EN、ZH）に変換するロジックを実装
  - サポートされていない言語コードに対してエラーを返す検証処理を実装
  - `is_language_supported(lang_code)`クラスメソッドを実装
  - `get_supported_languages()`クラスメソッドを実装
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 2.3 テキスト翻訳機能の実装
  - `translate_text(text, source_lang, target_lang, context)`メソッドを実装
  - 元言語と翻訳先言語が同じ場合、API呼び出しをスキップして元テキストを返す最適化を実装
  - 空テキストまたは空白のみの入力に対して空文字列を返す処理を実装
  - DeepL API `/v2/translate`エンドポイントにPOSTリクエストを送信する処理を実装
  - リクエストボディに`text`配列、`target_lang`、`source_lang`を含める
  - 成功レスポンスからtranslationsを抽出し、Result.successオブジェクトを返す
  - エラーレスポンスに対してResult.failureオブジェクトを返す
  - 翻訳成功時にログ（元言語、翻訳先言語、テキスト長）を記録
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 5.7, 6.1, 6.2, 6.4_

- [x] 2.4 エラーハンドリングとリトライロジックの実装
  - HTTPステータス429（レート制限）を検出し、APIRateLimitErrorを返す処理を実装
  - HTTPステータス504または408（タイムアウト）を検出し、リトライロジックを実行
  - httpx.TimeoutExceptionを検出し、リトライロジックを実行
  - 最大リトライ回数を2回に設定
  - リトライ上限到達時にAPITimeoutErrorを返す処理を実装
  - 予期しないAPIエラーに対してエラーログを記録し、TranslationErrorを返す処理を実装
  - リトライ時にログを記録
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 2.5 バッチ翻訳機能の実装
  - `translate_batch(texts, source_lang, target_lang, context)`メソッドを実装
  - 空リスト入力に対して空リストを返す処理を実装
  - 各テキストを個別に`translate_text()`で翻訳するループ処理を実装
  - 個別翻訳失敗時に元テキストを返すGraceful Degradation処理を実装
  - 失敗したテキストに対して警告ログを記録
  - すべての翻訳完了後に結果リストを含むResult.successを返す
  - バッチ翻訳全体でエラーが発生した場合にTranslationErrorを返す
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.3, 6.4_

- [x] 2.6 非同期コンテキストマネージャーの実装
  - `__aenter__()`メソッドを実装し、selfを返す
  - `__aexit__()`メソッドを実装し、HTTPクライアントをクローズ
  - `close()`メソッドを実装し、httpx.AsyncClientのリソースを解放
  - _Requirements: 6.5, 6.6_

- [x] 3. 単体テストの実装と更新
- [x] 3.1 TranslationService初期化テストの実装
  - 環境変数からAPIキーを正しく読み込むことを検証するテストを実装
  - APIキー未設定時にValueErrorが発生することを検証するテストを実装
  - API Base URLが環境変数またはデフォルト値から正しく設定されることを検証するテストを実装
  - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.4, 7.5_
  - **完了**: test_translation_service_deepl.py に7個のテストを実装済み（全てパス）

- [x] 3.2 言語コード変換テストの実装
  - ja→JA、en→EN、zh→ZHの言語コード変換が正しく動作することを検証するテストを実装
  - サポート外言語コードに対してエラーが返されることを検証するテストを実装
  - `is_language_supported()`が正しい判定結果を返すことを検証するテストを実装
  - `get_supported_languages()`が正しいマッピング辞書を返すことを検証するテストを実装
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  - **完了**: TestLanguageCodeConversionクラスに5個のテストを実装済み（全てパス）

- [x] 3.3 translate_text正常系テストの実装
  - モック化されたDeepL APIレスポンス（200ステータス）を使用したテストを実装
  - 翻訳成功時にResult.successが返されることを検証
  - 翻訳テキストが正しく抽出されることを検証
  - 同一言語入力時に元テキストが返されることを検証
  - 空テキスト入力時に空文字列が返されることを検証
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 8.1_
  - **完了**: TestTranslateTextクラスに6個のテストを実装済み（全てパス）

- [x] 3.4 translate_textエラー系テストの実装
  - HTTPステータス429（レート制限）時にAPIRateLimitErrorが返されることを検証するテストを実装
  - HTTPステータス504（タイムアウト）時にリトライが実行されることを検証するテストを実装
  - リトライ上限到達時にAPITimeoutErrorが返されることを検証するテストを実装
  - httpx.TimeoutException発生時にリトライが実行されることを検証するテストを実装
  - 予期しないエラー時にTranslationErrorが返されることを検証するテストを実装
  - _Requirements: 2.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 8.1_
  - **完了**: TestErrorHandlingAndRetryクラスに4個のテストを実装済み（全てパス）

- [x] 3.5 translate_batchテストの実装
  - 空リスト入力時に空リストが返されることを検証するテストを実装
  - 複数テキストの正常翻訳が動作することを検証するテストを実装
  - 一部テキスト翻訳失敗時にGraceful Degradationが動作することを検証するテストを実装
  - 失敗したテキストが元テキストとして返されることを検証
  - 結果リスト長が入力リスト長と同じことを検証
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.1_
  - **完了**: TestBatchTranslationクラスに4個のテストを実装済み（全てパス）

- [x] 3.6 非同期コンテキストマネージャーテストの実装
  - async withブロックでTranslationServiceが正しく動作することを検証するテストを実装
  - `__aexit__()`後にHTTPクライアントが正しくクローズされることを検証するテストを実装
  - `close()`メソッドが正しくリソースを解放することを検証するテストを実装
  - _Requirements: 6.5, 6.6, 8.1_
  - **完了**: TestAsyncContextManagerクラスに3個のテストを実装済み（全てパス）

- [x] 4. 統合テストの実装
- [x] 4.1 ReviewHandlerとの統合テストの実装
  - review_handler.pyがTranslationServiceを呼び出して翻訳を実行できることを検証するテストを実装
  - 翻訳結果がreview_handler.pyで正しく処理されることを検証するテストを実装
  - バッチ翻訳がreview_handler.pyの複数コメント翻訳で正しく動作することを検証するテストを実装
  - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - **完了**: test_translation_integration.py に4個のテストを実装済み（全てパス）

- [x] 4.2 環境変数読み込み統合テストの実装
  - .envファイルからDEEPL_API_KEYが正しく読み込まれることを検証するテストを実装
  - .envファイルからDEEPL_API_BASE_URLが正しく読み込まれることを検証するテストを実装
  - TranslationServiceが正しく初期化されることを検証するテストを実装
  - _Requirements: 7.1, 7.4, 7.5_
  - **完了**: TestEnvironmentVariableIntegrationクラスに5個のテストを実装済み（全てパス）

- [x] 4.3 Result型互換性統合テストの実装
  - 既存のResult型との互換性を検証するテストを実装
  - `is_success`プロパティが正しく機能することを検証するテストを実装
  - `data`プロパティが正しく翻訳結果を返すことを検証するテストを実装
  - `error`プロパティが正しくエラーオブジェクトを返すことを検証するテストを実装
  - _Requirements: 6.4_
  - **完了**: TestResultTypeCompatibilityクラスに7個のテストを実装済み（全てパス）

- [ ] 5. マニュアルテストスクリプトの更新と実行
- [ ] 5.1 test_translation_manual.pyの更新
  - DeepL APIを使用した日本語→英語翻訳テストスクリプトを実装
  - DeepL APIを使用した日本語→中国語翻訳テストスクリプトを実装
  - DeepL APIを使用した英語→日本語翻訳テストスクリプトを実装
  - 非同期コンテキストマネージャーを使用したテストパターンを実装
  - _Requirements: 8.2_

- [ ] 5.2 マニュアルテストの実行と翻訳品質確認
  - test_translation_manual.pyを実行し、日本語→英語翻訳の品質を確認
  - test_translation_manual.pyを実行し、日本語→中国語翻訳の品質を確認
  - test_translation_manual.pyを実行し、英語→日本語翻訳の品質を確認
  - 翻訳結果が自然で正確であることを確認
  - _Requirements: 8.2_

- [x] 6. ドキュメントとコメントの充実
- [x] 6.1 TranslationServiceモジュールdocstringの作成
  - モジュールレベルのdocstringを作成し、DeepL API統合の概要を記述
  - 使用例を含むdocstringを作成
  - _Requirements: 8.3_
  - **完了**: モジュールdocstringに主な機能、サポート言語、環境変数、使用例、エラーハンドリングの詳細を追加

- [x] 6.2 TranslationServiceメソッドdocstringの作成
  - `translate_text()`メソッドのdocstringを作成（引数、戻り値、例外の説明）
  - `translate_batch()`メソッドのdocstringを作成（引数、戻り値、例外の説明）
  - `is_language_supported()`メソッドのdocstringを作成
  - `get_supported_languages()`メソッドのdocstringを作成
  - `close()`、`__aenter__()`、`__aexit__()`メソッドのdocstringを作成
  - _Requirements: 8.3_
  - **完了**: すべてのパブリックメソッドに詳細なdocstringを追加（引数、戻り値、使用例を含む）

- [x] 6.3 エラークラスdocstringの作成
  - TranslationErrorクラスのdocstringを作成（基底クラスの説明）
  - APIRateLimitErrorクラスのdocstringを作成（発生条件の説明）
  - APITimeoutErrorクラスのdocstringを作成（発生条件の説明）
  - _Requirements: 8.3_
  - **完了**: 全エラークラスに詳細なdocstringを追加（発生条件、対処方法、注意事項、使用例を含む）

- [ ] 7. 最終的なテストとデプロイ準備
- [ ] 7.1 全テストスイートの実行と検証
  - すべての単体テストを実行し、パスすることを確認
  - すべての統合テストを実行し、パスすることを確認
  - テストカバレッジを確認し、主要機能がカバーされていることを検証
  - _Requirements: 8.1, 8.5_

- [ ] 7.2 既存機能への影響確認
  - review_handler.pyが正常に動作することを確認
  - 既存のレビュー投稿機能が正常に動作することを確認
  - 多言語翻訳機能が正常に動作することを確認
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 7.3 パフォーマンステストの実行
  - 単一翻訳のレスポンス時間を測定（目標: 2秒以内）
  - バッチ翻訳（7カテゴリ）のレスポンス時間を測定（目標: 15秒以内）
  - タイムアウトとリトライの動作を検証
  - 結果をログに記録
  - _Requirements: 設計文書のPerformance Testing_

- [ ] 7.4 セキュリティ検証
  - APIキーが環境変数から正しく読み込まれ、ソースコードに含まれていないことを確認
  - .envファイルが.gitignoreに含まれていることを確認
  - テキスト長の上限チェックが動作することを確認
  - 言語コードの検証（ホワイトリスト方式）が動作することを確認
  - _Requirements: 設計文書のSecurity Considerations_

---

## タスク完了後のアクション

すべてのタスクが完了したら、以下のアクションを実行：

1. **コードレビュー**: 実装コードをレビューし、設計文書との整合性を確認
2. **デプロイメント**: 開発環境にデプロイし、実際のDeepL APIで動作確認
3. **モニタリング**: ログとエラーレートを24時間監視
4. **ドキュメント更新**: TESTING_TRANSLATION_SERVICE.mdとREADME.mdを更新
5. **クリーンアップ**: DeepSeek API関連の環境変数とコメントを削除

## 要件カバレッジサマリー

- **Requirement 1 (DeepL API統合)**: タスク 2.1, 3.1 でカバー
- **Requirement 2 (テキスト翻訳)**: タスク 2.3, 3.3, 3.4 でカバー
- **Requirement 3 (言語サポート)**: タスク 2.2, 3.2 でカバー
- **Requirement 4 (バッチ翻訳)**: タスク 2.5, 3.5 でカバー
- **Requirement 5 (エラーハンドリング)**: タスク 2.4, 3.4 でカバー
- **Requirement 6 (既存互換性)**: タスク 2.3, 2.5, 2.6, 4.1, 4.3, 7.2 でカバー
- **Requirement 7 (環境設定)**: タスク 1.2, 2.1, 3.1, 4.2 でカバー
- **Requirement 8 (テスト・ドキュメント)**: タスク 3.*, 5.*, 6.*, 7.1 でカバー
