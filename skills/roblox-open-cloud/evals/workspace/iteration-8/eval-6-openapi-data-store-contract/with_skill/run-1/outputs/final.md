認証情報: configured（認証情報の値は表示しません）
リクエスト: GET https://apis.roblox.com/cloud/v2/universes/987654321/data-stores?maxPageSize=1
結果: HTTP 401 — 認証に失敗したため、Data Store一覧は取得できませんでした（変更は行っていません）。

仕様確認:
- method: GET
- path: `/cloud/v2/universes/{universe_id}/data-stores`（`universe_id=987654321`）
- query: `maxPageSize=1`（最大1件）
- scope: `universe-datastores.control:list`
- 安定性: `STABLE`
- response schema（HTTP 200）: `ListDataStoresResponse`。`dataStores`（`DataStore`配列）および任意の`nextPageToken`を含みます。

仕様根拠: OpenAPI 3.0.4（extensions 1.1.0、https://create.roblox.com/docs/cloud/openapi.json）。関連公式リファレンス: https://create.roblox.com/docs/cloud/reference/features/storage#Cloud_ListDataStores
検証: 読み取り要求を1回実行しましたが、HTTP 401のため結果データはありません。
次の対応: 環境変数が未設定なのではなく、設定済みのキーが認証で拒否されています。既存キーの有効状態・有効期限を確認し、無効なら再生成してください。管理画面: https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab
