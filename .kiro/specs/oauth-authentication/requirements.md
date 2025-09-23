# Requirements Document

## Project Description (Input)
ログイン用OAuth認証サービスを実装したい。
ログイン用OAuth認証サービスは、1)Google 認証と2)Facebookと3)メール認証だけで良い。
3)メール認証は、メールアドレスだけ登録して、そのメールにRedirect　URLを貼って送信し、UserがそのRedirect URLをClick　すると、
本Homepage に飛んできて、メールアドレスは有効化される。 ここで、このセッションは有効化される。
メール認証のUserは、Loginの度に、メールアドレスを入力して、メールアドレスに6桁数字のコードを飛ばし、サイトに6桁数字が
入力して合っていれば、セッションは有効化される。
1)Google　認証では、ユーザーのメールアドレスをサイトのMongoDBに保持する。
2)Facebook認証では、ユーザーのメールアドレスをサイトのMongoDBに保持する。
どの認証方式も、a)認証方式とb)メールアドレス c)ユーザータイプ　の組み合わせで、Identity をMongoDBに登録する。
c)ユーザータイプは、今現在は、"user" とする。 後に、"admin" "ally" を加える。
認証方式は、本サイト上だと、
・Reviewの詳細を見るときに必要とする。
・Reviewを登録するときに必要とする。

認証の見せ方は、../deepschina と同じく、左MenuにLogin後は表示され、Loginパネルは右下に表示する。
Loginパネルは、「・Reviewの詳細を見るときに必要とする。」「・Reviewを登録するときに必要とする。」
の時にのみ、画面右下に表示する。
実装は、1)Google認証から始める。

## 導入

OAuth認証サービスは、Google認証、Facebook認証、メール認証の3つの認証方法を提供し、レビュー閲覧・投稿機能にセキュアなアクセス制御を実現します。認証されたユーザーの情報はMongoDBに保存され、セッション管理により継続的な認証状態を維持します。

## 要件

### 要件1: Google認証機能
**目的:** ユーザーとして、Googleアカウントでログインしたい。これにより、既存のGoogleアカウントを使用してサービスにアクセスできる。

#### 受入基準
1. WHEN ユーザーがGoogle認証ボタンをクリック THEN OAuth認証サービス SHALL GoogleのOAuth2.0認証フローを開始する
2. WHEN ユーザーがGoogle認証を完了 THEN OAuth認証サービス SHALL ユーザーのメールアドレスを取得する
3. WHEN Google認証が成功 THEN OAuth認証サービス SHALL ユーザー情報（認証方式: "google", メールアドレス, ユーザータイプ: "user"）をMongoDBに保存する
4. WHEN 既存のGoogleユーザーが再ログイン THEN OAuth認証サービス SHALL 既存のユーザー情報を更新する
5. WHEN Google認証が失敗 THEN OAuth認証サービス SHALL エラーメッセージを表示して認証フローを終了する

### 要件2: Facebook認証機能
**目的:** ユーザーとして、Facebookアカウントでログインしたい。これにより、既存のFacebookアカウントを使用してサービスにアクセスできる。

#### 受入基準
1. WHEN ユーザーがFacebook認証ボタンをクリック THEN OAuth認証サービス SHALL FacebookのOAuth2.0認証フローを開始する
2. WHEN ユーザーがFacebook認証を完了 THEN OAuth認証サービス SHALL ユーザーのメールアドレスを取得する
3. WHEN Facebook認証が成功 THEN OAuth認証サービス SHALL ユーザー情報（認証方式: "facebook", メールアドレス, ユーザータイプ: "user"）をMongoDBに保存する
4. WHEN 既存のFacebookユーザーが再ログイン THEN OAuth認証サービス SHALL 既存のユーザー情報を更新する
5. WHEN Facebook認証が失敗 THEN OAuth認証サービス SHALL エラーメッセージを表示して認証フローを終了する

### 要件3: メール認証機能
**目的:** ユーザーとして、メールアドレスを使用してアカウントを作成・ログインしたい。これにより、サードパーティアカウントを持たないユーザーもサービスにアクセスできる。

#### 受入基準

##### 新規登録プロセス
1. WHEN ユーザーがメールアドレスを入力して新規登録を実行 THEN OAuth認証サービス SHALL 確認用リダイレクトURLを含むメールを送信する
2. WHEN ユーザーがメール内のリダイレクトURLをクリック THEN OAuth認証サービス SHALL ユーザーをホームページにリダイレクトしてメールアドレスを有効化する
3. WHEN メールアドレスが有効化 THEN OAuth認証サービス SHALL セッションを有効化してユーザー情報（認証方式: "email", メールアドレス, ユーザータイプ: "user"）をMongoDBに保存する

##### ログインプロセス
4. WHEN メール認証ユーザーがログインを実行 THEN OAuth認証サービス SHALL メールアドレスの入力を要求する
5. WHEN ユーザーがメールアドレスを入力 THEN OAuth認証サービス SHALL 6桁数字の認証コードをメールに送信する
6. WHEN ユーザーが正しい6桁コードを入力 THEN OAuth認証サービス SHALL セッションを有効化する
7. WHEN ユーザーが間違った6桁コードを入力 THEN OAuth認証サービス SHALL エラーメッセージを表示して再入力を要求する
8. WHEN 認証コードの有効期限が切れた THEN OAuth認証サービス SHALL 新しいコードの再送を許可する

### 要件4: セッション管理機能
**目的:** システム管理者として、ユーザーの認証状態を適切に管理したい。これにより、セキュアなアクセス制御を実現できる。

#### 受入基準
1. WHEN ユーザーが正常に認証 THEN OAuth認証サービス SHALL セキュアなセッションを作成する
2. WHILE ユーザーがアクティブ THE OAuth認証サービス SHALL セッション状態を維持する
3. WHEN ユーザーがログアウト THEN OAuth認証サービス SHALL セッションを無効化する
4. WHEN セッションの有効期限が切れた THEN OAuth認証サービス SHALL 自動的にセッションを無効化する
5. WHEN 不正なセッションアクセスが検出 THEN OAuth認証サービス SHALL セッションを強制終了する

### 要件5: ユーザーデータ管理機能
**目的:** システム管理者として、ユーザー情報を一元管理したい。これにより、一貫性のあるユーザー管理を実現できる。

#### 受入基準
1. WHEN 新しいユーザーが認証 THEN OAuth認証サービス SHALL ユーザー情報をMongoDB内のIdentityコレクションに保存する
2. WHERE MongoDBにユーザー情報を保存する際 THE OAuth認証サービス SHALL 認証方式、メールアドレス、ユーザータイプの組み合わせで保存する
3. WHEN 初期設定時 THEN OAuth認証サービス SHALL ユーザータイプを"user"に設定する
4. WHEN 将来的な拡張時 THEN OAuth認証サービス SHALL "admin"と"ally"ユーザータイプをサポートする
5. WHEN 同一メールアドレスで複数認証方式が存在 THEN OAuth認証サービス SHALL 各認証方式を個別のIdentityレコードとして管理する

### 要件6: UI表示機能
**目的:** ユーザーとして、認証状態を視覚的に確認したい。これにより、現在のログイン状態を把握できる。

#### 受入基準
1. WHEN ユーザーがログイン後 THEN OAuth認証サービス SHALL 左メニューにユーザー情報を表示する
2. WHEN ユーザーが認証が必要なコンテンツにアクセス THEN OAuth認証サービス SHALL 画面右下にログインパネルを表示する
3. WHERE レビュー詳細表示が要求された場合 THE OAuth認証サービス SHALL ログインパネルを右下に表示する
4. WHERE レビュー投稿が要求された場合 THE OAuth認証サービス SHALL ログインパネルを右下に表示する
5. WHEN ユーザーが認証済み状態 THEN OAuth認証サービス SHALL ログインパネルを非表示にする

### 要件7: 設定ベースアクセス制御機能
**目的:** システム管理者として、.envファイルでURLパターンと必要なユーザー権限を設定できるようにしたい。これにより、柔軟で管理しやすいアクセス制御を実現できる。

#### 受入基準

##### アクセス制御設定管理
1. WHEN システム起動時 THEN OAuth認証サービス SHALL .envファイルからアクセス制御ルールを読み込む
2. WHERE .envファイルに設定を記載する際 THE OAuth認証サービス SHALL "URLパターン,必要権限1,必要権限2,..." の形式をサポートする
3. WHEN .envファイルに"/reviews/details,user,admin,ally"が設定 THEN OAuth認証サービス SHALL /reviews/detailsを含むURLに対してuser, admin, allyのいずれかの権限を要求する
4. WHEN 複数のアクセス制御ルールが設定 THEN OAuth認証サービス SHALL 各ルールを個別に評価する
5. WHEN .envファイルの設定が変更 THEN OAuth認証サービス SHALL 設定再読み込み機能をサポートする

##### URLパターンマッチング
6. WHEN ユーザーがURLにアクセス THEN OAuth認証サービス SHALL 設定されたURLパターンとの照合を実行する
7. WHERE URLが設定パターンを含む場合 THE OAuth認証サービス SHALL 対応する権限チェックを実行する
8. WHERE URLが設定パターンを含まない場合 THE OAuth認証サービス SHALL 認証不要でアクセスを許可する
9. WHEN 複数のパターンがマッチ THEN OAuth認証サービス SHALL 最初にマッチしたルールを適用する

##### 権限ベースアクセス制御
10. WHEN 認証が必要なURLにアクセス AND ユーザーが未認証 THEN OAuth認証サービス SHALL 認証を要求してアクセスを制限する
11. WHEN 認証が必要なURLにアクセス AND ユーザーが認証済み AND 必要な権限を保持 THEN OAuth認証サービス SHALL アクセスを許可する
12. WHEN 認証が必要なURLにアクセス AND ユーザーが認証済み AND 必要な権限を保持しない THEN OAuth認証サービス SHALL 権限不足エラーを表示してアクセスを拒否する
13. WHEN セッションが無効な状態でアクセス THEN OAuth認証サービス SHALL 再認証を要求する
14. WHERE 権限チェックを実行する際 THE OAuth認証サービス SHALL ユーザーのユーザータイプと設定された必要権限リストを照合する

##### 設定例サポート
15. WHEN .env設定例として THEN OAuth認証サービス SHALL 以下の形式をサポートする:
    - "/reviews/details,user,admin,ally" (レビュー詳細はuser/admin/ally権限が必要)
    - "/reviews/submit,user,admin" (レビュー投稿はuser/admin権限が必要)
    - "/admin,admin" (管理機能はadmin権限のみ必要)