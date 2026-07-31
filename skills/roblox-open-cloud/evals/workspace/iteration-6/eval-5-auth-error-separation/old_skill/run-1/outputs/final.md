認証情報: configured（環境変数は設定済み。403 は missing setup ではありません）
リクエスト: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
結果: HTTP 403 — Scope not authorized. 保存済みCreator Store assetは読み取れませんでした。
必要な権限: creator-store-save:read
検証: 権限不足のため未実施。変更は一切していません。
次の対応: API Key管理ページ https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で、キーの selected API system and operations に creator-store-save:read が含まれていることを確認してください。あわせて target experience or resource restrictions、accepted IP addresses、key status and expiration を確認し、必要な権限・対象リソース制限・許可IP・有効状態を修正してから再試行してください。APIキー自体をチャットに提示する必要はありません。
