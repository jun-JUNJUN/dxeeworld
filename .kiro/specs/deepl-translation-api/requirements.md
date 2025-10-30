# Requirements Document

## Project Description (Input)
For the translation of text entered in the review form, I would like to use DeepL translation api, instead of DeepSeek LLM that is implemented in the current codes.

## Introduction

現在、レビューフォームのテキスト翻訳にDeepSeek LLMを使用していますが、DeepL Translation APIに移行することで、翻訳品質の向上とコスト効率の改善を実現します。DeepL APIは業界標準の翻訳サービスであり、より自然で正確な翻訳を提供し、レスポンス時間の改善も期待できます。

この移行により、ユーザーは高品質な多言語レビュー体験を得られ、プラットフォームの国際化戦略をさらに強化できます。既存のTranslationServiceインターフェースとの互換性を維持しながら、内部実装をDeepL APIに置き換えることで、他のコンポーネントへの影響を最小限に抑えます。

## Requirements

### Requirement 1: DeepL API統合とクライアント実装
**Objective:** 開発者として、DeepL Translation APIを既存のTranslationServiceに統合し、DeepSeek LLMと置き換えることで、翻訳品質を向上させたい

#### Acceptance Criteria

1. WHEN TranslationServiceが初期化される THEN Translation Service SHALL DeepL APIキーを環境変数 `DEEPL_API_KEY` から取得する
2. IF DeepL APIキーが設定されていない THEN Translation Service SHALL ValueError例外を発生させる
3. WHEN DeepL APIクライアントを初期化する THEN Translation Service SHALL DeepL APIの公式エンドポイント（https://api-free.deepl.com/v2 または https://api.deepl.com/v2）を使用する
4. WHEN HTTP通信を行う THEN Translation Service SHALL httpxライブラリを使用して非同期リクエストを実行する
5. WHERE タイムアウト設定 THEN Translation Service SHALL デフォルトタイムアウトを30秒に設定する

### Requirement 2: テキスト翻訳機能の実装
**Objective:** ユーザーとして、レビューコメントをDeepL APIを使用して高品質に翻訳できるようにしたい

#### Acceptance Criteria

1. WHEN `translate_text(text, source_lang, target_lang, context)` メソッドが呼び出される THEN Translation Service SHALL DeepL API `/v2/translate` エンドポイントにリクエストを送信する
2. IF 元言語と翻訳先言語が同じ THEN Translation Service SHALL API呼び出しをスキップし、元のテキストをそのまま返す
3. IF テキストが空または空白のみ THEN Translation Service SHALL API呼び出しをスキップし、空文字列を返す
4. WHEN DeepL APIにリクエストを送信する THEN Translation Service SHALL `text`, `source_lang`, `target_lang` パラメータをPOSTボディに含める
5. WHEN DeepL APIから成功レスポンスを受信する THEN Translation Service SHALL 翻訳されたテキストを含むResult.successオブジェクトを返す
6. IF DeepL APIがエラーレスポンスを返す THEN Translation Service SHALL エラー内容を含むResult.failureオブジェクトを返す

### Requirement 3: 言語サポートと検証
**Objective:** システムとして、プログラムコード内で言語コードの変換と検証を行い、現在サポートされている言語（日本語、英語、中国語）の翻訳機能を保証したい

#### Acceptance Criteria

1. WHERE サポート言語の定義 THEN Translation Service SHALL プログラムコード内で日本語（ja）、英語（en）、中国語（zh）の言語コードマッピングを定義する
2. WHEN アプリケーション言語コード（ja、en、zh）を受け取る THEN Translation Service SHALL DeepL API形式の言語コード（JA、EN、ZH）に変換する
3. IF サポートされていない言語コードが指定される THEN Translation Service SHALL 翻訳リクエストを送信せず、TranslationErrorを含むResult.failureを返す
4. WHEN `is_language_supported(lang_code)` メソッドが呼び出される THEN Translation Service SHALL プログラムコードで定義された言語マッピングに基づいて判定する
5. WHEN `get_supported_languages()` メソッドが呼び出される THEN Translation Service SHALL プログラムコードで定義されたサポート言語のマッピング辞書を返す
6. WHERE 言語コード変換ロジック THEN Translation Service SHALL アプリケーション層の言語コード（小文字）とDeepL API言語コード（大文字）の対応関係を明示的に管理する

### Requirement 4: バッチ翻訳機能の実装
**Objective:** システムとして、複数のレビューコメント（カテゴリ別）を効率的に翻訳できるようにしたい

#### Acceptance Criteria

1. WHEN `translate_batch(texts, source_lang, target_lang, context)` メソッドが呼び出される THEN Translation Service SHALL 各テキストを個別に `translate_text` メソッドで翻訳する
2. IF テキストリストが空 THEN Translation Service SHALL 空リストを含むResult.successを返す
3. WHEN バッチ翻訳中に個別の翻訳が失敗する THEN Translation Service SHALL 失敗したテキストについては元のテキストをそのまま使用する（Graceful Degradation）
4. WHEN すべてのバッチ翻訳が完了する THEN Translation Service SHALL 翻訳結果のリストを含むResult.successを返す
5. IF バッチ翻訳プロセス全体でエラーが発生する THEN Translation Service SHALL TranslationErrorを含むResult.failureを返す

### Requirement 5: エラーハンドリングとリトライ機能
**Objective:** システムとして、DeepL APIの一時的な障害やレート制限に適切に対処し、信頼性の高い翻訳サービスを提供したい

#### Acceptance Criteria

1. WHEN DeepL APIがHTTPステータス429（レート制限）を返す THEN Translation Service SHALL APIRateLimitErrorを含むResult.failureを返す
2. WHEN DeepL APIがHTTPステータス504または408（タイムアウト）を返す AND リトライ回数が最大リトライ数未満 THEN Translation Service SHALL 自動的にリクエストを再試行する
3. WHERE リトライ設定 THEN Translation Service SHALL 最大リトライ回数を2回に設定する
4. IF リトライ上限に達してもタイムアウトが続く THEN Translation Service SHALL APITimeoutErrorを含むResult.failureを返す
5. WHEN httpx.TimeoutExceptionが発生する AND リトライ回数が最大リトライ数未満 THEN Translation Service SHALL 自動的にリクエストを再試行する
6. WHEN DeepL APIから予期しないエラーが発生する THEN Translation Service SHALL エラー内容をログに記録し、TranslationErrorを含むResult.failureを返す
7. WHEN 翻訳が成功する THEN Translation Service SHALL 元言語、翻訳先言語、テキスト長をinfoレベルでログに記録する

### Requirement 6: 既存インターフェースとの互換性維持
**Objective:** 開発者として、既存のコード（review_handler.pyなど）を変更せずにDeepL APIへの移行を完了したい

#### Acceptance Criteria

1. WHEN TranslationServiceクラスのパブリックメソッドシグネチャ THEN Translation Service SHALL 既存のメソッド名、引数、戻り値の型を維持する
2. WHERE `translate_text` メソッド THEN Translation Service SHALL 引数 `(text: str, source_lang: str, target_lang: str, context: Optional[str])` を受け取る
3. WHERE `translate_batch` メソッド THEN Translation Service SHALL 引数 `(texts: List[str], source_lang: str, target_lang: str, context: Optional[str])` を受け取る
4. WHEN 翻訳メソッドが呼び出される THEN Translation Service SHALL `Result[T, TranslationError]` 型のオブジェクトを返す
5. WHEN 非同期コンテキストマネージャーとして使用される THEN Translation Service SHALL `__aenter__` および `__aexit__` メソッドをサポートする
6. WHEN `close()` メソッドが呼び出される THEN Translation Service SHALL HTTPクライアントのリソースを解放する

### Requirement 7: 環境設定とデプロイメント対応
**Objective:** 運用者として、DeepL APIの設定を簡単に行い、本番環境とテスト環境を適切に管理したい

#### Acceptance Criteria

1. WHERE 環境変数設定 THEN Translation Service SHALL `.env` ファイルから `DEEPL_API_KEY` を読み込む
2. WHEN DeepL無料プランを使用する THEN Translation Service SHALL API Base URLとして `https://api-free.deepl.com/v2` を使用する
3. WHEN DeepL有料プランを使用する THEN Translation Service SHALL API Base URLとして `https://api.deepl.com/v2` を使用する
4. WHERE API Base URL設定 THEN Translation Service SHALL 環境変数 `DEEPL_API_BASE_URL` からBase URLを読み込み可能にする
5. IF `DEEPL_API_BASE_URL` が設定されていない THEN Translation Service SHALL デフォルトでフリープランのエンドポイントを使用する

### Requirement 8: テストとドキュメント
**Objective:** 開発者として、DeepL API統合の正常性を確認し、他の開発者が理解しやすいドキュメントを提供したい

#### Acceptance Criteria

1. WHERE 単体テスト THEN Translation Service SHALL モック化されたDeepL APIレスポンスを使用したテストをパスする
2. WHEN 実際のDeepL APIを使用したマニュアルテスト THEN Translation Service SHALL 日本語→英語、日本語→中国語、英語→日本語の翻訳が正常に動作することを確認する
3. WHERE ドキュメント THEN Translation Service SHALL モジュールdocstring、メソッドdocstring、引数・戻り値の説明を含む
4. WHERE 設定ドキュメント THEN System SHALL `.env.example` ファイルに `DEEPL_API_KEY` と `DEEPL_API_BASE_URL` の設定例を追加する
5. WHERE 既存テスト THEN Translation Service SHALL 既存の `test_translation_service.py` テストスイートをDeepL API用に更新する
