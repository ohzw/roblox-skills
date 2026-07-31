認証情報: configured

呼び出し前に公式 OpenAPI の契約を確認しました。
- method: `GET`
- path: `https://apis.roblox.com/cloud/v2/universes/987654321/data-stores`
- query: `maxPageSize=1`
- scope: `universe-datastores.read`
- 安定性: Stable
- response schema: Data Store 一覧（`dataStores` 配列、ページング時の `nextPageToken`）

リクエスト: GET `https://apis.roblox.com/cloud/v2/universes/987654321/data-stores?maxPageSize=1`
結果: HTTP 401 — 認証に失敗しました。Data Store 一覧は取得できませんでした。
必要な権限: `universe-datastores.read`
検証: 実行したのは読み取り専用の一覧取得 1 回のみ。変更は行っていません。
次の対応: 環境変数は設定済みとして検出されています。既存の API キーの有効状態・期限を確認し、無効なら再生成してください。API キー管理: https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab
