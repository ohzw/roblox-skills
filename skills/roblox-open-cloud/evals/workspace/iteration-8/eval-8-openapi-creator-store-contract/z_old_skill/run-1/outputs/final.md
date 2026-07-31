認証情報: configured（`ROBLOX_OPEN_CLOUD_API_KEY` の存在のみ確認。値は取得・表示していません）

契約確認（公式 OpenAPI JSON）:
- 操作: 保存済み Creator Store asset の一覧取得（読み取り専用）
- リクエスト: `GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1`
- `limit`: 1件に制限。`page`: 1ページ目を指定。
- 認証方式: API key 認証（`x-api-key`）。
- 必要な scope: `creator-store-save:read`
- 安定性: `EXPERIMENTAL`（公式 OpenAPI の `x-roblox-stability`）。

結果: HTTP 403 — API key は設定済みですが、`creator-store-save:read` が認可されていません（Scope not authorized）。

検証: 変更を伴わない上記の GET を1回だけ実行しました。保存済み asset の内容は権限不足のため取得できませんでした。作成・更新・削除などの変更操作は実行していません。

次の対応: 既存の設定済みキーを [API Key 管理](https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab) で編集し、`creator-store-save:read` に対応する API operation、対象リソース制限、許可 IP、キーの status／有効期限を確認してください。これは認証情報の欠如ではなく認可不足です。