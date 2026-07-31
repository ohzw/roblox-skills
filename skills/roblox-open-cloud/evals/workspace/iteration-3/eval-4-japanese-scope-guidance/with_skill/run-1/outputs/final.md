認証情報: configured
リクエスト: POST https://apis.roblox.com/toolbox-service/v2/assets:search
結果: HTTP 400 — Bad Request。APIは「Either searchCategoryType or categoryPath must be provided.」を返しました。指定したリクエスト本文は `{ "query": "tree" }` です。
必要な権限: `creator-store-product:read`
検証: 認証ゲートは `configured: true` でした。検索APIの応答はHTTP 400で、Creator Store検索は成功しませんでした。読み戻しは該当せず、リソースの変更はありません。
次の対応: 今回はHTTP 403ではありません。もしHTTP 403になった場合は、[Credential Dashboard](https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab)で `creator-store-product:read` を付与し、選択したAPI system/operations、対象のexperienceまたはresource restrictions、accepted IP addresses、key statusを確認してください。APIキー自体を共有する必要はありません。
