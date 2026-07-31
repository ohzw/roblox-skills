認証情報: configured
リクエスト: GET https://apis.roblox.com/toolbox-service/v2/assets:search?searchCategoryType=Model&query=Roblox&pageNumber=0&maxPageSize=1
結果: HTTP 200 — Creator Store の検索結果を1件取得しました。返却された先頭アセットのクリエイターは Vallorum（user/32056239、認証済み）で、投票数は4,000（賛成3,800、反対200）でした。レスポンスには次ページトークンも含まれていました。
必要な権限: creator-store-product:read
仕様根拠: 公式 OpenAPI `https://create.roblox.com/docs/cloud/openapi.json`（OpenAPI 3.0.4、拡張機能バージョン1.1.0）。対象操作は `Toolbox_SearchCreatorStoreAssetsDeprecated`（GET）で、安定性は `BETA`、レート制限はAPIキー所有者あたり毎分1,000件です。クエリ制約は `maxPageSize` が1〜100（既定25）、`pageNumber` が0〜2,147,483,647で0始まり、`pageNumber` と `pageToken` は同時指定不可です。認証方式として仕様には `roblox-api-key` が掲載され、OAuth 2.0 の場合のスコープは `creator-store-product:read` です。今回はAPIキーをリクエストヘルパー経由で使用し、同スコープを必要権限として指定しました。
検証: 読み取りのみ実行。変更操作は行っていません。
次の対応: なし
