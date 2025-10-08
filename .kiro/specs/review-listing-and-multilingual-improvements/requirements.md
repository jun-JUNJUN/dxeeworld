# Requirements Document

## Introduction

本機能は、DXEEWorldプラットフォームにおける企業レビューシステムの大幅な改善を実現します。主な改善領域は以下の3つです：

1. **レビュー一覧表示とアクセス制御** - ユーザーの認証状態とレビュー投稿履歴に基づいた適切なコンテンツ表示
2. **多言語対応レビュー投稿フロー** - 英語・日本語・中国語に対応した動的フォームと確認画面の実装
3. **雇用期間バリデーション** - 現従業員・元従業員選択時の適切な入力サポートとバリデーション

これらの改善により、グローバルユーザーへの対応強化、SEO最適化、ユーザー体験の向上、データ品質の改善を実現します。

## Requirements

### Requirement 1: レビュー一覧のアクセス制御と表示

**Objective:** ユーザーとして、自分の認証状態とレビュー投稿履歴に応じた適切なレビュー一覧を閲覧したい。これにより、貢献したユーザーには詳細情報へのアクセスを提供し、未認証ユーザーやWebクローラーには適切な情報を表示できる。

#### Acceptance Criteria

1. WHEN 未ログインユーザーがレビュー一覧ページにアクセスする THEN Review System SHALL レビューコメントの最初の1行または最初の128文字を表示し、残りの部分を伏せ字（例: "●●●●●"）で表示する
2. WHEN Webクローラー（User-Agent判定）がレビュー一覧ページにアクセスする THEN Review System SHALL 「(会社名)のReview」というテキストのみを表示する
3. WHEN ログイン済みユーザーで過去1年以内にレビューを投稿したユーザーがレビュー一覧ページにアクセスする THEN Review System SHALL 全企業のレビューを一覧で表示する
4. WHEN 認証済みレビュー投稿者がレビュー一覧を閲覧する THEN Review System SHALL 会社別フィルター機能を提供する
5. WHEN 認証済みレビュー投稿者がレビュー一覧を閲覧する THEN Review System SHALL 地域別フィルター機能を提供する
6. WHEN 認証済みレビュー投稿者がレビュー一覧を閲覧する THEN Review System SHALL レビュー評価のしきい値による絞り込み機能を提供する
7. IF ユーザーがログイン済みだが過去1年以内のレビュー投稿履歴がない THEN Review System SHALL レビュー一覧へのアクセスを制限し、「Reviewを投稿いただいた方に閲覧権限を付与しています」と表示する
8. WHEN ユーザーがレビューを投稿する THEN Review System SHALL ユーザーの最終レビュー投稿日時を更新し、1年間のアクセス権限を付与する

### Requirement 2: 多言語対応レビュー投稿フォーム

**Objective:** レビュー投稿者として、自分の母国語でレビューを投稿したい。これにより、グローバルユーザーの参加を促進し、より詳細で正確なレビュー情報を収集できる。

#### Acceptance Criteria

1. WHEN ユーザーがレビュー投稿フォームにアクセスする THEN Review Form SHALL フォーム最上部に言語選択ドロップダウンを表示する
2. WHERE 言語選択ドロップダウン THE Review Form SHALL 英語、日本語、中国語のオプションを提供する
3. WHEN ユーザーが言語選択ドロップダウンで言語を変更する THEN Review Form SHALL 選択された言語に応じてフォーム全体のラベルとプレースホルダーを切り替える
4. WHEN ユーザーが言語を選択してレビューを入力する THEN Review Form SHALL 選択された言語情報をフォームデータに含める
5. IF ユーザーがフォームを初回表示した THEN Review Form SHALL ブラウザの言語設定に基づいてデフォルト言語を設定する（英語/日本語/中国語のいずれか）
6. WHEN ユーザーが日本語でフォームを表示する THEN Review Form SHALL 全てのラベルとプレースホルダーを日本語で表示する
7. WHEN ユーザーが英語でフォームを表示する THEN Review Form SHALL 全てのラベルとプレースホルダーを英語で表示する
8. WHEN ユーザーが中国語でフォームを表示する THEN Review Form SHALL 全てのラベルとプレースホルダーを中国語（簡体字）で表示する

### Requirement 3: レビュー投稿確認画面

**Objective:** レビュー投稿者として、投稿前に入力内容を確認したい。これにより、誤投稿を防ぎ、英語以外の言語で投稿されたレビューの英語翻訳を事前確認できる。

#### Acceptance Criteria

1. WHEN ユーザーがレビュー投稿フォームで「次へ」または「確認」ボタンをクリックする THEN Review System SHALL 確認画面を表示する
2. WHERE 確認画面 THE Review System SHALL ユーザーが入力した全ての評価項目（7段階評価）を表示する
3. WHERE 確認画面 THE Review System SHALL ユーザーが選択した言語で入力されたコメントを原文のまま表示する
4. WHEN ユーザーが英語以外の言語（日本語または中国語）でレビューを投稿する THEN Review System SHALL 確認画面に英語翻訳されたコメントを表示する
5. IF ユーザーが英語でレビューを投稿した THEN Review System SHALL 確認画面に原文のみを表示し、翻訳は表示しない
6. WHERE 確認画面 THE Review System SHALL 「投稿」ボタンと「戻る」ボタンを提供する
7. WHEN ユーザーが確認画面で「戻る」ボタンをクリックする THEN Review System SHALL 入力内容を保持したままフォーム画面に戻る
8. WHEN ユーザーが確認画面で「投稿」ボタンをクリックする THEN Review System SHALL レビューをMongoDBに保存する

### Requirement 4: レビューデータの多言語保存

**Objective:** システムとして、レビューの言語情報を適切に保存し、将来的な多言語表示や分析に活用したい。

#### Acceptance Criteria

1. WHEN レビューがMongoDBに保存される THEN Review System SHALL レビューコメントの言語コード（"en", "ja", "zh"）をドキュメントに含める
2. WHEN レビューがMongoDBに保存される THEN Review System SHALL 元の言語で入力されたコメントを保存する
3. IF レビューが英語以外で投稿された THEN Review System SHALL 英語翻訳されたコメントも別フィールドに保存する
4. WHEN レビューデータが保存される THEN Review System SHALL 言語フィールドを必須項目として検証する
5. WHERE レビュードキュメント THE Review System SHALL 以下のフィールドを含める：language, comment, comment_en（英語以外の場合）

### Requirement 5: レビュー投稿完了フィードバック

**Objective:** レビュー投稿者として、投稿が成功したことを明確に確認したい。これにより、投稿完了の確信を得て、次のアクションに移れる。

#### Acceptance Criteria

1. WHEN レビューが正常に保存される THEN Review System SHALL ユーザーを企業詳細ページにリダイレクトする
2. WHEN ユーザーが企業詳細ページにリダイレクトされる THEN Review System SHALL ページ上部に「Review投稿しました。ありがとうございました。」というメッセージを表示する
3. WHERE 成功メッセージ THE Review System SHALL 目立つ色（成功を示す緑系）で表示する
4. WHEN 成功メッセージが表示される THEN Review System SHALL 5秒後に自動的にメッセージをフェードアウトする
5. IF レビュー保存中にエラーが発生した THEN Review System SHALL エラーメッセージを表示し、ユーザーを確認画面に留める

### Requirement 6: 雇用状態選択時の自動入力サポート

**Objective:** レビュー投稿者として、雇用状態に応じた適切な入力サポートを受けたい。これにより、入力の手間を削減し、データの一貫性を向上させる。

#### Acceptance Criteria

1. WHEN ユーザーがレビューフォームで「現従業員」を選択する THEN Review Form SHALL 雇用終了年月を自動的に「現在」に設定する
2. WHEN 雇用終了年月が「現在」に自動設定される THEN Review Form SHALL 雇用終了年月の入力フィールドを無効化する
3. WHEN ユーザーが「現従業員」から「元従業員」に変更する THEN Review Form SHALL 雇用終了年月の入力フィールドを有効化する
4. WHEN ユーザーが「元従業員」から「現従業員」に変更する THEN Review Form SHALL 雇用終了年月を再度「現在」に設定し、フィールドを無効化する
5. WHERE 雇用状態選択 THE Review Form SHALL 「現従業員」と「元従業員」の2つのオプションを提供する

### Requirement 7: 雇用期間バリデーション

**Objective:** システムとして、雇用期間情報の完全性を保証したい。これにより、レビューの信頼性を維持し、不完全なデータの保存を防止できる。

#### Acceptance Criteria

1. WHEN ユーザーが「元従業員」を選択して確認画面に進もうとする AND 雇用開始年が未入力 THEN Review Form SHALL 「雇用開始年を入力してください」というエラーメッセージを表示する
2. WHEN ユーザーが「元従業員」を選択して確認画面に進もうとする AND 雇用終了年が未入力 THEN Review Form SHALL 「雇用終了年を入力してください」というエラーメッセージを表示する
3. WHEN ユーザーが「元従業員」を選択して確認画面に進もうとする AND 雇用開始年と雇用終了年の両方が未入力 THEN Review Form SHALL 「雇用開始年と雇用終了年を入力してください」というエラーメッセージを表示する
4. IF 雇用期間バリデーションエラーが発生した THEN Review Form SHALL ユーザーを確認画面に進ませない
5. WHEN バリデーションエラーメッセージが表示される THEN Review Form SHALL エラーメッセージを該当する入力フィールドの近くに赤色で表示する
6. IF 雇用開始年が雇用終了年より後 THEN Review Form SHALL 「雇用開始年は雇用終了年より前である必要があります」というエラーメッセージを表示する
7. WHEN ユーザーが「現従業員」を選択する THEN Review Form SHALL 雇用開始年のみを必須とし、雇用終了年のバリデーションをスキップする
