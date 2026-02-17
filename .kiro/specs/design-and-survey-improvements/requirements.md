# Requirements Document

## Project Description (Input)

Implement new design which is written in ./design_improvement_spec.md

### Summary

Comprehensive redesign of the Dxee platform with two major components:

1. **Visual Design Overhaul (Kaggle-style)**
   - Transform from purple sidebar-based layout to clean horizontal header
   - Implement modern color scheme (#20BEFF primary blue)
   - Standardize typography system
   - Improve home page, company search, and company detail pages
   - Ensure responsive design across all screen sizes

2. **Survey Structure Improvement (OpenWork-style, MECE principle)**
   - Restructure from 6 categories to 8 core categories + overall assessment
   - Apply MECE principle for comprehensive and non-overlapping coverage
   - Implement multi-step wizard UI for better UX
   - Add star rating components and new database schema
   - Create aggregation and visualization features (radar charts)

### Key Scope Areas

**Design System Components:**
- Header/Navigation redesign
- Color palette and CSS variables
- Typography system
- Card components
- Button and form elements
- Rating components

**Survey Categories (8):**
1. Compensation & Benefits (待遇・報酬)
2. Work-Life Balance (ワークライフバランス)
3. Company Culture (企業文化・風土)
4. Career Development (キャリア・成長)
5. Management & Organization (マネジメント・組織)
6. Performance & Promotion (評価・処遇制度)
7. Work Environment (職場環境)
8. Business & Product (事業・製品)
9. Overall Assessment (総合評価)

## Introduction

DxeeWorldプラットフォームを、Kaggle風のモダンで洗練されたデザインに刷新し、同時にOpenWorkのMECE原則に基づいた包括的なアンケート構造を実装します。このリニューアルにより、ユーザー体験の向上と、より質の高い企業評価データの収集を実現します。

## Requirements

### Requirement 1: デザインシステムの構築

**Objective:** Kaggle風のモダンな設計システムを確立し、プラットフォーム全体で統一された視覚的一貫性を実現する

#### Acceptance Criteria

1. WHEN プラットフォームが初期化されたとき THEN デザインシステム SHALL プライマリカラー（#20BEFF）、ダークカラー（#1A8FCC）、ライトカラー（#E3F5FF）を定義すること
2. IF CSS変数が設定されたとき THEN すべてのコンポーネント SHALL 定義されたカラー変数を使用すること
3. WHEN ページがレンダリングされるとき THEN フォントファミリー SHALL 英数字にはInter、日本語にはNoto Sans JPを使用すること
4. IF h1要素が使用されるとき THEN 文字サイズ SHALL 32px（2rem）、フォントウェイト SHALL 700、行間 SHALL 1.2 であること
5. IF h2要素が使用されるとき THEN 文字サイズ SHALL 24px（1.5rem）、フォントウェイト SHALL 600、行間 SHALL 1.2 であること
6. IF body テキストが表示されるとき THEN 文字サイズ SHALL 16px（1rem）、フォントウェイト SHALL 400、行間 SHALL 1.6 であること
7. WHERE スペーシングが定義されるとき THE システム SHALL 4px基準のスペーシングスケールを使用すること

---

### Requirement 2: ヘッダーとナビゲーションの改善

**Objective:** 紫色のサイドバーレイアウトを廃止し、水平方向のクリーンなヘッダーナビゲーションを実装する

#### Acceptance Criteria

1. WHEN ページが読み込まれたとき THEN ヘッダー SHALL 高さ64pxで、背景色#FFFFFF、下部に1px solid #E0E0E0のボーダーを持つこと
2. IF ロゴが配置されるとき THEN ロゴサイズ SHALL 最大幅150px、左上に配置されること
3. WHEN ユーザーがページをスクロールするとき THEN ヘッダー SHALL スティッキーポジションで固定表示されること
4. IF ナビゲーションメニューが表示されるとき THEN メニュー項目 SHALL「ホーム」「レビュー検索」「企業一覧」「ログイン/ユーザーアイコン」を含むこと
5. WHEN メニュー項目にホバーするとき THEN メニュー項目 SHALL 下線アニメーション（transition: 0.2s）が表示されること
6. IF 画面幅が768px未満のとき THEN ナビゲーション SHALL ハンバーガーメニューで表示されること
7. WHERE レスポンシブデバイスが使用されるとき THE ナビゲーション SHALL モバイル対応のメニュー配置を使用すること

---

### Requirement 3: ホームページの再設計

**Objective:** キャッチコピーと企業情報を効果的に提示し、ユーザー登録と企業検索への導線を最適化する

#### Acceptance Criteria

1. WHEN ホームページが表示されるとき THEN ヒーローセクション SHALL 「優秀な人材とスタートアップをつなぐ」というキャッチコピーを表示すること
2. IF ヒーローセクションがレンダリングされるとき THEN レイアウト SHALL グラデーション背景（#F8FBFF → #FFFFFF）、max-width 1200px、中央揃えであること
3. WHEN ユーザーがヒーローセクションを見るとき THEN セクション SHALL サブコピー「実績ベースの評価で、透明性の高いマッチングを実現」を含むこと
4. IF CTAボタンが配置されるとき THEN ボタン SHALL「無料で始める」（プライマリ）と「企業を探す」（セカンダリ、アウトライン）を含むこと
5. WHEN ページがレスポンシブ表示されるとき THEN ヒーローセクション SHALL モバイルでは縦積みレイアウト（左60% → 右40%を上下配置）に変更されること
6. WHERE イラスト/スクリーンショットが表示されるとき THE 画像 SHALL ヒーローセクション右側に配置されること

---

### Requirement 4: 統計情報セクションの改善

**Objective:** シンプルで視覚的に効果的な統計情報表示を実装し、プラットフォームの信頼性を伝える

#### Acceptance Criteria

1. WHEN 統計セクションが表示されるとき THEN レイアウト SHALL 背景#FFFFFF、4カラムグリッド（レスポンシブで2→1カラム）、padding 60px 24pxであること
2. IF 統計項目が表示されるとき THEN 各項目 SHALL アイコン（48px）、数字（36px、weight 700）、ラベル（14px、color #666）を含むこと
3. WHEN 統計数字が表示されるとき THEN テキスト配列 SHALL 中央揃えであること
4. WHERE アイコンが使用されるとき THE システム SHALL SVGアイコンまたはicon fontを使用すること

---

### Requirement 5: 企業・レビューカードコンポーネント

**Objective:** 企業情報を効果的に表示し、ユーザーが企業の詳細情報にアクセスしやすいカードデザインを実装する

#### Acceptance Criteria

1. WHEN 企業カードが表示されるとき THEN カードスタイル SHALL 背景#FFFFFF、1px solid #E0E0E0のボーダー、border-radius 8px、padding 20px、box-shadow 0 1px 3px rgba(0,0,0,0.08)であること
2. IF ユーザーがカードにホバーするとき THEN box-shadow SHALL 0 4px 12px rgba(0,0,0,0.12)に変更されること AND transition SHALL all 0.3s easeが適用されること
3. WHEN カード内容がレンダリングされるとき THEN 構成 SHALL 企業ロゴ、企業名、評価スター（★4.2）、業種・地域・企業規模、説明文（2行まで）、タグ、レビュー数・推薦度を含むこと
4. IF タグが表示されるとき THEN タグスタイル SHALL 背景#F0F0F0、color #333、padding 4px 12px、border-radius 16px、font-size 12pxであること
5. WHEN カードグリッドが表示されるとき THEN グリッド SHALL 3カラム（デスクトップ）→ 2カラム（タブレット）→ 1カラム（モバイル）に変更されること

---

### Requirement 6: 企業検索ページの改善

**Objective:** フィルタリングと検索機能を実装し、ユーザーが企業を効率的に発見できるようにする

#### Acceptance Criteria

1. WHEN 検索ページが表示されるとき THEN レイアウト SHALL 2カラム構成（左：フィルター250px幅、右：検索結果）であること
2. IF サイドバーフィルターが配置されるとき THEN フィルター SHALL 背景#FFFFFF、border-right 1px solid #E0E0E0、スティッキーポジション（スクロール時に固定）であること
3. WHEN ユーザーがフィルターを操作するとき THEN チェックボックス SHALL 業種、場所、企業規模でフィルタリング可能であること
4. IF 検索結果がレンダリングされるとき THEN グリッド SHALL 2カラムレイアウト、gap 20px、padding 24pxであること
5. WHEN ソート機能が使用されるとき THEN ドロップダウン SHALL 「評価順（高→低）」「評価順（低→高）」「レビュー数順」「企業名順」「最近追加順」のオプションを含むこと
6. WHERE ページネーションが表示されるとき THE システム SHALL ページネーションまたは無限スクロール機能を実装すること
7. IF リアルタイム検索が実装されるとき THEN 結果 SHALL フィルター変更時に即座に更新されること

---

### Requirement 7: 企業詳細ページの改善

**Objective:** 企業情報を体系的に表示し、複数のタブを通じて異なる視点から情報を提供する

#### Acceptance Criteria

1. WHEN 企業詳細ページが表示されるとき THEN ヘッダー SHALL ロゴ、企業名、評価スター（★4.5）、タグライン、業種・地域・企業規模、外部リンクボタンを含むこと
2. IF ヘッダーがレンダリングされるとき THEN スタイル SHALL 背景#FFFFFF、padding 32px、border-bottom 1px solid #E0E0E0、企業名 28px weight 700、評価スター 24pxであること
3. WHEN タブナビゲーションが表示されるとき THEN タブ SHALL 「概要」「レビュー(125)」「統計」「求人情報」を含むこと
4. IF ユーザーがタブをクリックするとき THEN タブ活性化時 SHALL color #20BEFF、border-bottom 2px solid #20BEFF、font-weight 600が適用されること
5. WHERE 通常のタブ状態のとき THE タブ SHALL color #666、border-bottom 2px solid transparentであること
6. WHEN 統計情報が表示されるとき THEN グラフ SHALL カテゴリー別平均スコアをレーダーチャートまたは棒グラフで表示すること

---

### Requirement 8: レスポンシブデザイン対応

**Objective:** すべてのデバイスサイズで最適なユーザー体験を提供する

#### Acceptance Criteria

1. IF デバイス幅が320px～767pxのとき THEN レイアウト SHALL 1カラム、ハンバーガーメニュー、タップ領域30px以上であること
2. IF デバイス幅が768px～1023pxのとき THEN グリッド SHALL 2カラム表示、簡易フィルター表示であること
3. IF デバイス幅が1024px以上のとき THEN グリッド SHALL 3カラム表示、フルフィルター表示であること
4. WHEN テキストがモバイル表示されるとき THEN フォントサイズ SHALL タップ領域の最小16pxを確保すること
5. WHERE 画像が表示されるとき THE 画像 SHALL レスポンシブ対応（srcset、picture要素）であること

---

### Requirement 9: アンケート項目構造の改善（MECE原則）

**Objective:** 6カテゴリーの既存構造を8カテゴリー+総合評価に拡張し、MECE原則に準拠した包括的かつ重複のない評価構造を実装する

#### Acceptance Criteria

1. WHEN アンケートが設計されるとき THEN カテゴリー構成 SHALL「待遇・報酬」「ワークライフバランス」「企業文化・風土」「キャリア・成長」「マネジメント・組織」「評価・処遇制度」「職場環境」「事業・製品」「総合評価」を含むこと
2. IF 待遇・報酬カテゴリーが定義されるとき THEN 質問項目 SHALL 給与水準、賞与・インセンティブ、福利厚生、ストックオプション、コメント欄を含むこと
3. IF ワークライフバランスカテゴリーが定義されるとき THEN 質問項目 SHALL 労働時間、休暇取得、柔軟な働き方、総合評価、コメント欄を含むこと
4. IF 企業文化カテゴリーが定義されるとき THEN 質問項目 SHALL 社風・雰囲気、多様性・インクルージョン、倫理・コンプライアンス、社内コミュニケーション、コメント欄を含むこと
5. IF キャリア・成長カテゴリーが定義されるとき THEN 質問項目 SHALL 成長機会、研修・教育制度、キャリアパス、メンター制度、コメント欄を含むこと
6. IF マネジメント・組織カテゴリーが定義されるとき THEN 質問項目 SHALL 経営陣のビジョン、意思決定プロセス、組織体制、直属上司の評価、コメント欄を含むこと
7. IF 評価・処遇制度カテゴリーが定義されるとき THEN 質問項目 SHALL 評価制度の公平性、評価とフィードバック、昇進・昇格、報酬と評価の連動性、コメント欄を含むこと
8. IF 職場環境カテゴリーが定義されるとき THEN 質問項目 SHALL オフィス環境、人間関係、ストレスレベル、健康管理・安全衛生、コメント欄を含むこと
9. IF 事業・製品カテゴリーが定義されるとき THEN 質問項目 SHALL 事業の将来性、製品・サービスへの誇り、社会貢献度、財務健全性、コメント欄を含むこと
10. WHEN 総合評価セクションが定義されるとき THEN 質問項目 SHALL 総合満足度（5段階）、推薦意向（NPS、0-10段階）、在籍状況、在籍期間、職種カテゴリー、総合コメント欄を含むこと

---

### Requirement 10: アンケートUI/UXの実装（マルチステップウィザード）

**Objective:** 段階的なアンケート入力画面を実装し、ユーザーの入力負担を軽減し、完了率を向上させる

#### Acceptance Criteria

1. WHEN アンケートが表示されるとき THEN 進捗表示 SHALL 9ステップの進捗バーを表示すること
2. IF ユーザーがステップを進めるとき THEN 遷移 SHALL 「← 戻る」「次へ →」ボタンで前後移動可能であること
3. WHEN スターレーティングコンポーネントが使用されるとき THEN スタイル SHALL サイズ32px、未選択時#D0D0D0、選択時#FFB400、ホバー時にスケール1.1、アニメーションtransition 0.2sであること
4. IF ユーザーがスターをホバーするとき THEN プレビュー表示 SHALL 「3 / 5」のような数値表示がされること
5. WHEN バリデーション が必要なとき THEN システム SHALL 必須項目のチェック、エラーメッセージ表示を実装すること
6. WHERE 途中保存が実装されるとき THE データ SHALL localStorageに保存されること AND ユーザーが後で再開可能であること
7. IF レビュー確認画面が表示されるとき THEN 画面 SHALL 送信前のすべての回答を確認可能にすること

---

### Requirement 11: レビューデータベーススキーマの拡張

**Objective:** 8カテゴリー+総合評価に対応する新しいデータベーススキーマを実装する

#### Acceptance Criteria

1. WHEN reviewsテーブルが設計されるとき THEN スキーマ SHALL company_id、user_id、作成日時、更新日時、is_verifiedフラグを含むこと
2. IF 待遇・報酬データが保存されるとき THEN カラム SHALL comp_salary、comp_bonus、comp_benefits、comp_equity、comp_commentを含むこと
3. IF ワークライフバランスデータが保存されるとき THEN カラム SHALL wlb_hours、wlb_vacation、wlb_flexibility、wlb_overall、wlb_commentを含むこと
4. IF 企業文化データが保存されるとき THEN カラム SHALL culture_atmosphere、culture_diversity、culture_ethics、culture_communication、culture_commentを含むこと
5. IF キャリア・成長データが保存されるとき THEN カラム SHALL career_growth、career_training、career_path、career_mentorship、career_commentを含むこと
6. IF マネジメント・組織データが保存されるとき THEN カラム SHALL mgmt_vision、mgmt_decision、mgmt_structure、mgmt_manager、mgmt_commentを含むこと
7. IF 評価・処遇制度データが保存されるとき THEN カラム SHALL perf_fairness、perf_feedback、perf_promotion、perf_linkage、perf_commentを含むこと
8. IF 職場環境データが保存されるとき THEN カラム SHALL env_office、env_relationships、env_stress、env_health、env_commentを含むこと
9. IF 事業・製品データが保存されるとき THEN カラム SHALL biz_future、biz_pride、biz_social_impact、biz_financial、biz_commentを含むこと
10. WHEN 総合評価データが保存されるとき THEN カラム SHALL overall_satisfaction、overall_nps、employment_status、tenure、job_category、overall_commentを含むこと
11. WHERE レーティング項目が格納されるとき THE データ型 SHALL TINYINT（1～5の制約あり）またはENUM（employment_status）であること
12. IF インデックスが定義されるとき THEN システム SHALL company_id と created_at の複合インデックスを作成すること

---

### Requirement 12: 集計・分析機能

**Objective:** カテゴリー別平均スコア、NPS、レーダーチャートなどの分析機能を実装し、企業の評価を視覚化する

#### Acceptance Criteria

1. WHEN 企業詳細ページが表示されるとき THEN 統計情報 SHALL 総合評価★4.2、カテゴリー別平均スコア（全8カテゴリー）、推薦度（NPS）を表示すること
2. IF カテゴリー別スコアが計算されるとき THEN ロジック SHALL 各カテゴリーの全質問項目の平均を算出すること
3. WHEN NPSスコアが計算されるとき THEN 計算式 SHALL「Promoters（9-10点）の割合」-「Detractors（0-6点）の割合」であること
4. WHERE レーダーチャートが表示されるとき THE グラフ SHALL この企業と業界平均の比較を表示すること
5. IF キャッシュ機構が実装されるとき THEN パフォーマンス対策 SHALL 集計結果をキャッシュしること AND 定期的に更新されること
6. WHEN レスポンシブ表示のとき THEN モバイルデバイス上 SHALL レーダーチャートが棒グラフに切り替えられること

---

### Requirement 13: デザインシステムの組織と実装

**Objective:** デザイン定義をコード化し、プロジェクト全体で一貫して適用できるようにする

#### Acceptance Criteria

1. IF CSS変数が定義されるとき THEN 定義場所 SHALL `:root` セレクタまたは専用テーマファイルであること
2. WHEN カラー値が参照されるとき THEN コード SHALL `var(--color-primary)` 形式を使用すること
3. IF フォント設定が定義されるとき THEN body要素 SHALL グローバルフォントファミリーと行間を設定すること
4. WHERE コンポーネントが作成されるとき THE スタイル SHALL デザインシステム変数を参照すること
5. WHEN ダークモード対応が検討されるとき THEN システム SHALL CSS変数の上書きで複数テーマに対応可能な構造であること

---

### Requirement 14: 既存機能との互換性

**Objective:** デザイン改善を実装する過程で、既存の認証、多言語対応、アクセス制御機能の互換性を維持する

#### Acceptance Criteria

1. WHEN 新しいデザインが適用されるとき THEN 認証ログイン機能 SHALL 既存のOAuth（Google、Facebook）およびメール認証と互換性を保つこと
2. IF 多言語サポート（EN/ZH/JA）が実装されているとき THEN レイアウト SHALL すべての言語で正しく表示されること
3. WHEN 新しいUI要素が追加されるとき THEN アクセス制御 SHALL 既存のレビュー閲覧・投稿の認可ルールを継続すること
4. WHERE モバイル対応が改善されるとき THE ログインパネル（login-panel.js）と その他の既存JavaScriptコンポーネント SHALL 新しいレイアウトと互換性を保つこと
