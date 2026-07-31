認証情報: configured（APIキーの値は非表示）
リクエスト: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
結果: HTTP 403 — APIキーは認証されたが、対象操作の権限がありません。保存済みCreator Store assetは取得できませんでした。
必要な権限: creator-store-save:read
仕様根拠: 公式OpenAPI JSON（https://create.roblox.com/docs/cloud/openapi.json、OpenAPI 3.0.4、拡張機能バージョン1.1.0）。対象操作は `Saves_GetSaves`（Creator Store、`GET /toolbox-service/v1/saves`）で、`limit` は整数1〜500（既定値100）、`page` は整数1〜2147483647（既定値1、1始まり）です。認証方式としてOpenAPIは `roblox-legacy-cookie`、`roblox-api-key`、OAuth 2.0（`creator-store-save:read`）を列挙しており、今回の実行はAPIキー方式です。APIキーに要求されるスコープは `creator-store-save:read` です。安定性は `BETA`、非推奨ではありません。公式機能リファレンス: https://create.roblox.com/docs/cloud/reference/features/creator-store#Saves_GetSaves
検証: 実行は読み取り専用GETを1回だけ行いました。HTTP 403のため、保存済みassetのレスポンス内容は確認できませんでした。
次の対応: 既存の設定済みAPIキーを https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で編集し、対象APIシステムと操作（`creator-store-save:read`）、対象リソース制限、許可IP、キーの状態・有効期限を確認してください。キーの新規作成、環境変数の再設定、エージェントの再起動はこの403の対応ではありません。