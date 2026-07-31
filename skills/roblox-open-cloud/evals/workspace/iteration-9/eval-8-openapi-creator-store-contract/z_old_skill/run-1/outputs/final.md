認証情報: configured（APIキーの存在のみ確認。値は取得・表示していません）
リクエスト: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
契約確認: 公式OpenAPI JSONでは保存済みCreator Store assetの一覧取得は `GET /toolbox-service/v1/saves`。`limit` は返却件数の上限（OpenAPI上は任意の整数で、数値範囲の明記なし）、`page` はページ番号で1から開始するため、1件取得として `limit=1&page=1` を指定しました。認証方式は API Key（`x-api-key` ヘッダー。OAuth 2.0またはCookieも文書上の選択肢）で、APIキーに必要なscopeは `creator-store-save:read` です。安定性は `BETA` です。
結果: HTTP 403 — `Scope not authorized.`。APIキーは設定済みですが、要求された権限が認可されませんでした。
必要な権限: `creator-store-save:read`
検証: 読み取りリクエストを1回実行しました。HTTP 403のためassetは返却されませんでした。変更系メソッドは実行していません。
次の対応: 既存の設定済みキーについて、https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で API operation/scope、対象リソース制限、許可IP、キーの状態・有効期限を確認・編集してください。キーの新規作成、環境変数の再設定、エージェントの再起動はこの403の対応ではありません。