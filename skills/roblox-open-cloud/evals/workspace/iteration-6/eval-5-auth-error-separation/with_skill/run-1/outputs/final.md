認証情報: configured（既存の `ROBLOX_OPEN_CLOUD_API_KEY` がエージェントプロセスに設定済み）
リクエスト: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
結果: HTTP 403 — 認証情報は存在するが、権限不足（authorization）により拒否されました。レスポンス: `{"errors":[{"code":0,"message":"Scope not authorized."}]}`
必要な権限: `creator-store-save:read`
検証: 保存済みCreator Store assetの読み取り結果は取得できませんでした（HTTP 403）。変更操作は一切実行していません。
次の対応: 設定済みの既存キーを、API Key管理ページ（https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab）で編集してください。`creator-store-save:read` のAPIシステム／操作が選択されていること、対象エクスペリエンスまたはリソースの制限、許可済みIPアドレス、キーのステータスと有効期限を確認してください。これは既存キーの認可設定の問題であり、環境変数の設定不足ではありません。新しいキーの作成、環境変数の設定・再入力、エージェントの再起動は必要ありません。
