Credential: configured
Request: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
Result: HTTP 403 — 権限不足（Scope not authorized）
Required permissions: creator-store-save:read
Verification: 実行結果は権限エラーのため、保存済みCreator Store assetの読み取り結果は取得できませんでした。
Next: Creator DashboardのAPIキー管理画面（https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab）で、対象キーに `creator-store-save:read` を付与してください。あわせて、選択したAPI system／operation、対象リソース制限、許可IPアドレス、キーの状態・有効期限を確認してください。APIキー自体をチャットに貼り付けないでください。権限設定後に同じGETを再実行してください。

変更は一切行っていません。POST／DELETEなどの書き込み操作は実行していません。
