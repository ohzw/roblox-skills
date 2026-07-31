認証情報: configured
リクエスト: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
結果: HTTP 403 — 権限不足（Scope not authorized.）。保存済み Creator Store asset の読み取り結果は取得できませんでした。
必要な権限: creator-store-save:read
検証: 読み取り専用 GET の権限エラーを確認しました。変更操作は一切実行していません（mutation なし）。
次の対応: API Key 管理ページ https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で、選択した API system と operations に creator-store-save:read が含まれること、対象 experience または resource restrictions、accepted IP addresses、key status と expiration を確認してください。権限を付与した後も API key はチャットへ貼り付けず、エージェントプロセスの環境変数 ROBLOX_OPEN_CLOUD_API_KEY に設定して再実行してください。