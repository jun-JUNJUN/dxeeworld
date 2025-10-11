
## Admin PageのRequest.
- 今現在は、Admin画面の用意が無い。
- Use case: 将来の運用を見据えると、ユーザーが何か問い合わせしたときに、そのユーザーが何User なのか知りたい。
- Feature: ユーザーのemail アドレスを入れたら、Userは存在するか、存在する場合は何Userか、登録日時を表示。

[Doing]## Bug: Review　一覧が見れない。
- Current page does not show the list of reviews. When a user access to a review list, I would like to show the list of reviews.
- LoginしていないUser向けには、画像で表示したいし。
- web clawler には、「(会社名)のReview・・・」とだけ表示したい。
- LoginしているUserで、既に1年以内にReviewを投稿したUserは、他の企業もReviewを一覧で見ることができる。 見方は、会社別に見れたり、地域でFilter掛けられたり、Reviewの特定のしきい値で絞り込むことができる。

[Doing]## Review投稿の確認画面が無い。
- Review 投稿の言語を選べるようにしたい。選べるのは、[英語][日本語][中国語]など、Listする。
- Review 投稿の言語をFormの一番上部で選択できること。選択したら、Formそのものが、言語が切り替わる。
- Reivew 投稿の確認画面を表示してから、”投稿”にしたい。　
- Reivew 投稿の確認画面では、[投稿の言語でのコメント(just as a user typed))][投稿の言語が英語以外なら英語に翻訳したコメント]を表示する。
- 投稿されると、MongoDBには、Reviewのコメントの言語も保存すること。
- 投稿されたら、企業の詳細ページに映り、画面上側に”Review投稿しました。ありがとうございました。”とメッセージ表示する。

[Doing]## Bug: Review Formで、元従業員と現従業員を選択してもサポート機能が無い。
- 「現従業員」を選択したら、期限を”今現在”を自動で選択すること。
- 「元従業員」を選択したら、開始と終了の年が選択されていなければ、メッセージ表示し、投稿の確認画面に進めないようにする。

[Done] ## 画面の左下に、LoginしたらLogin情報を表示したい。
    "anthropic": {},
    "lmstudio": {
      "api_url": "http://localhost:1238/v1",
      "available_models": [
        {
          "name": "qwen3-1.7b",
          "display_name": "qwen3-1.7b",
          "supports_images": true,
          "supports_tool_calls": false,
        }
      ]
    }
