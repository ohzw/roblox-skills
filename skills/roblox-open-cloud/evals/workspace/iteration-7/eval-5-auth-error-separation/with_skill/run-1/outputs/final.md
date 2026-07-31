認証情報: configured
リクエスト: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
結果: HTTP 403 — APIキーは存在しますが、この操作の認可に失敗しました（Scope not authorized）。保存済みCreator Store assetの結果は取得できませんでした。
必要な権限: creator-store-save:read
検証: 403のため、読み取り結果の検証は未実施です。変更操作は行っていません。
次の対応: 既存のAPIキーを https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で編集し、API system と operation（creator-store-save:read）、対象リソース制限、許可IPアドレス、キーの状態・有効期限を確認してください。