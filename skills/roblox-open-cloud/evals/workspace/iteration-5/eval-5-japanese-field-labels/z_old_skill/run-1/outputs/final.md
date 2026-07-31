認証情報: configured（`ROBLOX_OPEN_CLOUD_API_KEY` の存在のみ確認。値や一部は取得・表示していません）
要求: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
必要な権限: `creator-store-save:read`
結果: HTTP 403 — Scope not authorized.
検証: 保存済みCreator Store assetは読み取れませんでした。今回の操作は、上記の1件取得GETのみです。save/create/deleteなどの変更操作は実行していません。
次の対応: API Key管理ページ https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で、`creator-store-save:read` が選択されたAPI system/operationに付与されていることを確認してください。あわせて対象リソースの制限、許可済みIPアドレス、APIキーの状態と有効期限を確認し、必要な権限だけを持つキーへ更新またはローテーションしてください。APIキーの値をチャット、コマンド引数、ソースコード、リポジトリ、またはエージェントが読めるファイルに貼り付けないでください。