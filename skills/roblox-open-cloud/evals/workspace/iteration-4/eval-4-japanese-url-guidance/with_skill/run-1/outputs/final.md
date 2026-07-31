認証情報: configured（`ROBLOX_OPEN_CLOUD_API_KEY` は非表示・非出力）

リクエスト: `POST https://apis.roblox.com/toolbox-service/v2/assets:search`

リクエスト内容: `searchCategoryType` = `Model`、`query` = `tree`

必要な権限: `creator-store-product:read`

結果: HTTP `200` — Creator Store の Model カテゴリで `tree` の検索に成功しました。応答には `creatorStoreAssets` と `queryFacets` が含まれ、`nextPageToken` も返されました。

検証: side-effect-free の検索 API のみを呼び出しました。リソースの作成・更新・削除などの変更はありません。API キー管理やキー自体の読み取り・表示も行っていません。

次の対応: 不要（権限不足ではありません）。
